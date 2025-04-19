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

# Add Nifty Next 50 stocks if desired
NIFTY_NEXT50_SYMBOLS = [
    "APOLLOHOSP.NS", "PIDILITIND.NS", "HAVELLS.NS", "BAJAJHLDNG.NS", "BERGEPAINT.NS",
    "GODREJCP.NS", "MARICO.NS", "SIEMENS.NS", "DABUR.NS", "DLF.NS",
    "BIOCON.NS", "LUPIN.NS", "BOSCHLTD.NS", "PGHH.NS", "AMBUJACEM.NS",
    "BANDHANBNK.NS", "COLPAL.NS", "MCDOWELL-N.NS", "HINDPETRO.NS", "GAIL.NS",
    "BANKBARODA.NS", "AUROPHARMA.NS", "PNB.NS", "CADILAHC.NS", "ACC.NS",
    "HDFCAMC.NS", "ICICIGI.NS", "NAUKRI.NS", "INDIGO.NS", "MUTHOOTFIN.NS",
    "PEL.NS", "MOTHERSUMI.NS", "NMDC.NS", "ICICIPRULI.NS", "CONCOR.NS",
    "ADANITRANS.NS", "PAGEIND.NS", "DMART.NS", "SBICARD.NS", "PETRONET.NS",
    "ABBOTINDIA.NS", "TORNTPHARM.NS", "UBL.NS", "OFSS.NS", "NHPC.NS",
    "INDUSTOWER.NS", "MRF.NS", "MUTHOOTFIN.NS", "ADANIGREEN.NS", "GICRE.NS"
]

# Combine both lists if you want to scan both indices
# ALL_SYMBOLS = NIFTY50_SYMBOLS + NIFTY_NEXT50_SYMBOLS
ALL_SYMBOLS = NIFTY50_SYMBOLS  # Using only Nifty 50 for now

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
    
    for symbol in ALL_SYMBOLS:
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
    
    # Build the message
    message_parts = []
    
    if buy_signals:
        buy_section = "✅ <b>NEW BUY SIGNALS</b>\n" + "\n".join(f"• {signal}" for signal in buy_signals)
        message_parts.append(buy_section)
    
    if sell_signals:
        sell_section = "🚨 <b>NEW SELL SIGNALS</b>\n" + "\n".join(f"• {signal}" for signal in sell_signals)
        message_parts.append(sell_section)
    
    # Send exactly one message
    if message_parts:
        final_message = "\n\n".join(message_parts)
        logging.info(f"Sending alert with {len(buy_signals)} buy and {len(sell_signals)} sell signals")
        send_telegram_message(final_message)
    else:
        logging.info("No signals found")
        send_telegram_message("🔍 No new RSI & MACD signals found across any timeframe.")

if __name__ == '__main__':
    run()
