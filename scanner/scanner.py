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
