import logging
from scanner.data import get_data
from scanner.strategy import calculate_rsi_macd
from scanner.telegram_bot import send_telegram_message

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Complete NIFTY50 symbols
NIFTY50_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "HINDUNILVR.NS",
    "INFY.NS", "ITC.NS", "BHARTIARTL.NS", "SBIN.NS", "HDFC.NS",
    "KOTAKBANK.NS", "LT.NS", "BAJFINANCE.NS", "AXISBANK.NS", "ASIANPAINT.NS",
    "MARUTI.NS", "HCLTECH.NS", "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS",
    "BAJAJFINSV.NS", "NTPC.NS", "TATAMOTORS.NS", "POWERGRID.NS", "WIPRO.NS",
    "HDFCLIFE.NS", "NESTLEIND.NS", "TECHM.NS", "DIVISLAB.NS", "ONGC.NS",
    "TATASTEEL.NS", "ADANIPORTS.NS", "JSWSTEEL.NS", "SBILIFE.NS", "HINDALCO.NS",
    "M&M.NS", "EICHERMOT.NS", "DRREDDY.NS", "COALINDIA.NS", "GRASIM.NS",
    "INDUSINDBK.NS", "UPL.NS", "CIPLA.NS", "HEROMOTOCO.NS", "BPCL.NS",
    "BRITANNIA.NS", "SHREECEM.NS", "ADANIENT.NS", "BAJAJ-AUTO.NS", "VEDL.NS"
]

# Use only the top 15 for testing if needed
# NIFTY50_SYMBOLS = NIFTY50_SYMBOLS[:15]

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
    
    # Process ITC.NS first with special logging
    if "ITC.NS" in NIFTY50_SYMBOLS:
        special_symbol = "ITC.NS"
        NIFTY50_SYMBOLS.remove(special_symbol)
        
        # Process ITC separately with extra logging
        logging.info(f"🔍 Special processing for {special_symbol}")
        
        for label, interval in TIMEFRAMES.items():
            logging.info(f"Processing {special_symbol} [{label}]")
            try:
                data = get_data(special_symbol, interval)
                if data is None or len(data) < 3:
                    logging.warning(f"Insufficient data for {special_symbol} [{label}]")
                    continue
                
                signal, enriched = calculate_rsi_macd(
                    data,
                    **STRATEGY_PARAMS
                )
                
                if signal:
                    if signal == 'BUY':
                        buy_signals.append(f"{special_symbol} [{label}]")
                        logging.info(f"✅ Added {special_symbol} [{label}] to BUY signals")
                    elif signal == 'SELL':
                        sell_signals.append(f"{special_symbol} [{label}]")
                        logging.info(f"🚨 Added {special_symbol} [{label}] to SELL signals")
                        
            except Exception as e:
                logging.error(f"Error processing {special_symbol} [{label}]: {e}")
        
        # Put ITC back in the list at the beginning
        NIFTY50_SYMBOLS.insert(0, special_symbol)
    
    # Process all other symbols
    for symbol in NIFTY50_SYMBOLS:
        # Skip ITC as it's already processed
        if symbol == "ITC.NS":
            continue
            
        for label, interval in TIMEFRAMES.items():
            logging.info(f"Processing {symbol} [{label}]")
            try:
                data = get_data(symbol, interval)
                if data is None or len(data) < 3:
                    logging.warning(f"Insufficient data for {symbol} [{label}]")
                    continue
                
                signal, enriched = calculate_rsi_macd(
                    data,
                    **STRATEGY_PARAMS
                )
                
                if signal:
                    if signal == 'BUY':
                        buy_signals.append(f"{symbol} [{label}]")
                    elif signal == 'SELL':
                        sell_signals.append(f"{symbol} [{label}]")
                        
            except Exception as e:
                logging.error(f"Error processing {symbol} [{label}]: {e}")
    
    # Build the message - ONLY SEND ONE MESSAGE
    message_parts = []
    
    if buy_signals:
        buy_section = "✅ <b>NEW BUY SIGNALS</b>\n" + "\n".join(f"• {signal}" for signal in buy_signals)
        message_parts.append(buy_section)
    
    if sell_signals:
        sell_section = "🚨 <b>NEW SELL SIGNALS</b>\n" + "\n".join(f"• {signal}" for signal in sell_signals)
        message_parts.append(sell_section)
    
    # Send exactly one message with everything combined
    if message_parts:
        final_message = "\n\n".join(message_parts)
        logging.info(f"Sending alert with {len(buy_signals)} buy and {len(sell_signals)} sell signals")
        # Send the message and track its state to prevent duplicates
        send_telegram_message(final_message)
    else:
        logging.info("No signals found")
        send_telegram_message("🔍 No new RSI & MACD signals found across any timeframe.")

if __name__ == '__main__':
    run()
