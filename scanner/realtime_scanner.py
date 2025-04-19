import os
import time
import logging
import signal
import pickle
import datetime
from scanner.data import get_data
from scanner.strategy import calculate_rsi_macd
from scanner.telegram_bot import send_telegram_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/realtime_scanner_{time.strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

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

TIMEFRAMES = {
    "Daily": "1d",
    "Weekly": "1wk"
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

# File to store previously detected signals
SIGNALS_CACHE_FILE = 'signals_cache.pkl'

def load_signal_cache():
    """Load previously detected signals from cache file"""
    try:
        if os.path.exists(SIGNALS_CACHE_FILE):
            with open(SIGNALS_CACHE_FILE, 'rb') as f:
                return pickle.load(f)
        return {}
    except Exception as e:
        logging.error(f"Error loading signal cache: {e}")
        return {}
        
def save_signal_cache(cache):
    """Save detected signals to cache file"""
    try:
        with open(SIGNALS_CACHE_FILE, 'wb') as f:
            pickle.dump(cache, f)
    except Exception as e:
        logging.error(f"Error saving signal cache: {e}")

def check_market_hours():
    """Check if Indian market is currently open"""
    # Indian market hours: 9:15 AM to 3:30 PM IST, Monday to Friday
    now = datetime.datetime.now()
    
    # Check if weekend
    if now.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        return False
        
    # Convert to IST (UTC+5:30) by adding 5 hours and 30 minutes
    market_time = now + datetime.timedelta(hours=5, minutes=30)
    
    # Check if within market hours (9:15 AM to 3:30 PM IST)
    market_open = datetime.time(9, 15)
    market_close = datetime.time(15, 30)
    
    return (market_open <= market_time.time() <= market_close)

def scan_stocks():
    """Scan stocks for new signals"""
    signal_cache = load_signal_cache()
    buy_signals = []
    sell_signals = []
    
    for symbol in NIFTY50_SYMBOLS:
        for label, interval in TIMEFRAMES.items():
            cache_key = f"{symbol}_{interval}"
            
            try:
                # Always get fresh data
                data = get_data(symbol, interval, force_download=True)
                if data is None or len(data) < 3:
                    continue
                
                signal, enriched = calculate_rsi_macd(
                    data,
                    **STRATEGY_PARAMS
                )
                
                if signal:
                    # Check if this is a new signal we haven't reported yet
                    if cache_key not in signal_cache or signal_cache[cache_key] != signal:
                        # New signal detected
                        if signal == 'BUY':
                            buy_signals.append(f"{symbol} [{label}]")
                        elif signal == 'SELL':
                            sell_signals.append(f"{symbol} [{label}]")
                        
                        # Update cache
                        signal_cache[cache_key] = signal
                        logging.info(f"New {signal} signal for {symbol} [{label}]")
                    
            except Exception as e:
                logging.error(f"Error processing {symbol} [{label}]: {e}")
    
    # Save updated signal cache
    save_signal_cache(signal_cache)
    
    # Send notification if signals found
    if buy_signals or sell_signals:
        message_parts = []
        
        if buy_signals:
            buy_section = "✅ <b>NEW BUY SIGNALS</b>\n" + "\n".join(f"• {signal}" for signal in buy_signals)
            message_parts.append(buy_section)
        
        if sell_signals:
            sell_section = "🚨 <b>NEW SELL SIGNALS</b>\n" + "\n".join(f"• {signal}" for signal in sell_signals)
            message_parts.append(sell_section)
        
        if message_parts:
            send_telegram_message("\n\n".join(message_parts))
            return True
    
    return False

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    logging.info("Stopping realtime scanner...")
    exit(0)

def run_continuous_scanner():
    """Run scanner continuously"""
    signal.signal(signal.SIGINT, signal_handler)
    
    logging.info("Starting continuous RSI & MACD scanner...")
    
    # Initial scan to establish baseline
    scan_stocks()
    logging.info("Initial scan complete")
    
    # Check market hours info message
    if not check_market_hours():
        logging.info("Outside market hours. Scanner will check periodically but signals are less likely.")
    else:
        logging.info("Within market hours. Actively scanning for signals.")
        
    try:
        # Main loop
        while True:
            # Scan frequency: Every 3 minutes during market hours, every 15 minutes outside
            if check_market_hours():
                scan_interval = 180  # 3 minutes
            else:
                scan_interval = 900  # 15 minutes
            
            time.sleep(scan_interval)
            
            # Run a scan cycle
            any_signals = scan_stocks()
            
            # Log status
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            if any_signals:
                logging.info(f"[{current_time}] Signals detected and sent")
            else:
                logging.info(f"[{current_time}] Scan complete - no new signals")
                
    except Exception as e:
        logging.error(f"Error in continuous scanner: {e}")
        raise

if __name__ == "__main__":
    # Check if environment variables are set
    if not os.getenv("TELEGRAM_BOT_TOKEN") or not os.getenv("TELEGRAM_CHAT_ID"):
        logging.error("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        exit(1)
    
    # Make sure log folder exists
    os.makedirs('logs', exist_ok=True)
    
    # Run continuous scanner
    run_continuous_scanner()
