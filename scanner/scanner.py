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
    buy_signals = []
    sell_signals = []
    
    for symbol in NIFTY50_SYMBOLS:
        for label, interval in TIMEFRAMES.items():
            logging.info(f"Processing {symbol} [{label}]")
            try:
                data = get_data(symbol, interval)
                if data is None or len(data) < 3:
                    logging.warning(f"Insufficient data for {symbol} [{label}]")
                    continue
                
                signal, enriched, position_changed = calculate_rsi_macd(
                    data,
                    **STRATEGY_PARAMS
                )
                
                # Only add to signals if position actually changed in the latest candle
                if signal and position_changed:
                    if signal == 'BUY':
                        buy_signals.append(f"{symbol} [{label}]")
                    elif signal == 'SELL':
                        sell_signals.append(f"{symbol} [{label}]")
                        
            except Exception as e:
                logging.error(f"Error processing {symbol} [{label}]: {e}")
    
    # Create a single combined message
    message_parts = []
    
    if buy_signals:
        buy_section = "✅ <b>NEW BUY SIGNALS</b>\n" + "\n".join(f"• {signal}" for signal in buy_signals)
        message_parts.append(buy_section)
    
    if sell_signals:
        sell_section = "🚨 <b>NEW SELL SIGNALS</b>\n" + "\n".join(f"• {signal}" for signal in sell_signals)
        message_parts.append(sell_section)
    
    # Send a single consolidated message or a "no signals" message
    if message_parts:
        send_telegram_message("\n\n".join(message_parts))
    else:
        send_telegram_message("🔍 No new RSI & MACD signals found across any timeframe.")

if __name__ == '__main__':
    run()
