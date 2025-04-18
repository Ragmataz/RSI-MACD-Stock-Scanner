#!/bin/bash

# Create base directory structure
mkdir -p scanner .github/workflows

# Create __init__.py to make scanner a package
touch scanner/__init__.py

# Create data.py
cat > scanner/data.py << 'EOF'
import yfinance as yf
import pandas as pd

def get_data(symbol, interval='1d'):
    try:
        data = yf.download(symbol, period='6mo', interval=interval)
        if data.empty or 'Close' not in data:
            return None

        data['Symbol'] = symbol
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None
EOF

# Create strategy.py
cat > scanner/strategy.py << 'EOF'
import pandas as pd
import numpy as np

def calculate_rsi_macd(data, fast_length=8, slow_length=16, signal_length=11, 
                      rsi_length=10, oversold=49, overbought=51):
    try:
        # Calculate EMAs for MACD
        data['FastMA'] = data['Close'].ewm(span=fast_length, adjust=False).mean()
        data['SlowMA'] = data['Close'].ewm(span=slow_length, adjust=False).mean()
        data['MACD'] = data['FastMA'] - data['SlowMA']
        data['Signal'] = data['MACD'].rolling(window=signal_length).mean()
        
        # Calculate RSI
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=rsi_length).mean()
        avg_loss = loss.rolling(window=rsi_length).mean()
        
        rs = avg_gain / avg_loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # Determine position based on conditions
        data['SignalLessMacd'] = data['Signal'] < data['MACD']
        data['SignalGreaterMacd'] = data['Signal'] > data['MACD']
        data['RsiOverbought'] = data['RSI'] > overbought
        data['RsiOversold'] = data['RSI'] < oversold
        
        # Create position column
        data['Position'] = 0
        
        # Buy condition: RSI > Overbought AND Signal < MACD
        buy_condition = (data['RsiOverbought'] & data['SignalLessMacd'])
        
        # Sell condition: RSI < Oversold AND Signal > MACD
        sell_condition = (data['RsiOversold'] & data['SignalGreaterMacd'])
        
        # Set positions
        data.loc[buy_condition, 'Position'] = 1
        data.loc[sell_condition, 'Position'] = -1
        
        # Check for signal in last candle
        signal = None
        if data['Position'].iloc[-1] == 1:
            signal = 'BUY'
        elif data['Position'].iloc[-1] == -1:
            signal = 'SELL'
        
        return signal, data
    except Exception as e:
        print(f"Error in RSI_MACD calculation: {e}")
        return None, data
EOF

# Create telegram_bot.py
cat > scanner/telegram_bot.py << 'EOF'
import os
import requests

def send_telegram_message(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=payload)
EOF

# Create scanner.py
cat > scanner/scanner.py << 'EOF'
import logging
from scanner.data import get_data
from scanner.strategy import calculate_rsi_macd
from scanner.telegram_bot import send_telegram_message

logging.basicConfig(level=logging.INFO)

# You can customize this stock list as needed
NIFTY50_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "LT.NS", "KOTAKBANK.NS", "SBIN.NS",
    "AXISBANK.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "ASIANPAINT.NS",
    "WIPRO.NS"
]

TIMEFRAMES = {
    "Daily": "1d",
    "Weekly": "1wk",
    "Monthly": "1mo"
}

# Strategy parameters from your inputs
STRATEGY_PARAMS = {
    "fast_length": 8,
    "slow_length": 16,
    "signal_length": 11,
    "rsi_length": 10,
    "oversold": 49,
    "overbought": 51
}

def run():
    signals_found = False
    buy_signals = []
    sell_signals = []
    
    for symbol in NIFTY50_SYMBOLS:
        for label, interval in TIMEFRAMES.items():
            logging.info(f"Processing {symbol} [{label}]")
            try:
                data = get_data(symbol, interval)
                if data is None:
                    raise ValueError("No data returned")
                
                signal, enriched = calculate_rsi_macd(
                    data,
                    **STRATEGY_PARAMS
                )
                
                if signal:
                    if signal == 'BUY':
                        buy_signals.append(f"{symbol} [{label}]")
                        signals_found = True
                    elif signal == 'SELL':
                        sell_signals.append(f"{symbol} [{label}]")
                        signals_found = True
                        
            except Exception as e:
                logging.error(f"Error processing {symbol} [{label}]: {e}")
    
    # Send Telegram messages with the results
    if buy_signals:
        message = "✅ <b>BUY SIGNALS</b>\n" + "\n".join(f"• {signal}" for signal in buy_signals)
        send_telegram_message(message)
    
    if sell_signals:
        message = "🚨 <b>SELL SIGNALS</b>\n" + "\n".join(f"• {signal}" for signal in sell_signals)
        send_telegram_message(message)
    
    if not signals_found:
        send_telegram_message("🔍 No RSI & MACD signals found today across any timeframe.")

if __name__ == '__main__':
    run()
EOF

# Create main.py
cat > main.py << 'EOF'
import os
import logging
from scanner.scanner import run

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    # Check if environment variables are set
    if not os.getenv("TELEGRAM_BOT_TOKEN") or not os.getenv("TELEGRAM_CHAT_ID"):
        logging.warning("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        logging.info("You can set them in your environment or create a .env file")
        exit(1)
    
    logging.info("Starting RSI & MACD Stock Scanner")
    run()
    logging.info("Scan completed")
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
yfinance>=0.2.28
pandas>=2.0.0
numpy>=1.26.0
requests>=2.31.0
EOF

# Create GitHub Actions workflow
cat > .github/workflows/run_scanner.yml << 'EOF'
name: Run Stock Scanner

on:
  schedule:
    # Run at market close - 16:00 IST (10:30 UTC) on weekdays
    # Adjust this timing based on your requirements
    - cron: '30 10 * * 1-5'
  
  # Allow manual trigger from GitHub UI
  workflow_dispatch:

jobs:
  scan:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v3
      
    - name: Set up Python 3.10
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        
    - name: Run scanner
      env:
        TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
        TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
      run: |
        python main.py
EOF

# Create README.md
cat > README.md << 'EOF'
# RSI & MACD Stock Scanner

This project scans a list of stocks (default: Nifty 50) for RSI and MACD signals on daily, weekly, and monthly timeframes and sends alerts via Telegram.

## Strategy Logic

The scanner uses a combination of RSI and MACD indicators:

- **Buy Signal**: When RSI > 51 AND MACD Signal Line < MACD Line
- **Sell Signal**: When RSI < 49 AND MACD Signal Line > MACD Line

Default Parameters:
- Fast EMA Length: 8
- Slow EMA Length: 16
- Signal Length: 11
- RSI Length: 10
- Oversold Level: 49
- Overbought Level: 51

## Setup

1. Install required packages:
   ```
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```
   export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
   export TELEGRAM_CHAT_ID="your_telegram_chat_id"
   ```

3. Run the scanner:
   ```
   python main.py
   ```

## Customizing

- You can modify the list of stocks in `scanner/scanner.py`
- Adjust strategy parameters in `scanner/scanner.py` under the `STRATEGY_PARAMS` dictionary
- Add additional timeframes if needed

## Files

- `main.py`: Entry point for the scanner
- `scanner/data.py`: Functions for fetching stock data
- `scanner/strategy.py`: RSI & MACD calculation logic
- `scanner/scanner.py`: Main scanning logic
- `scanner/telegram_bot.py`: Telegram notification functions
EOF

echo "Repository structure created successfully!"
echo "Run 'bash repository_setup.sh' to create all files"
echo "Don't forget to set up TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in your GitHub repo secrets."
