import yfinance as yf
import pandas as pd
import logging

def get_data(symbol, interval='1d'):
    try:
        # Special handling for ITC case
        special_debug = (symbol == "ITC.NS")
        if special_debug:
            logging.info(f"📊 DEBUGGING: Special handling for {symbol}")
        
        logging.info(f"Fetching data for {symbol} with interval {interval}")
        
        # Adjust period based on interval to ensure enough data for indicators
        if interval == '1mo':
            period = '3y'  # 3 years for monthly to get enough candles
        elif interval == '1wk':
            period = '1y'  # 1 year for weekly
        else:
            period = '6mo'  # 6 months for daily
            
        data = yf.download(symbol, period=period, interval=interval, progress=False)
        
        if data.empty or 'Close' not in data:
            logging.warning(f"No data available for {symbol}")
            return None

        # Clean data - remove NaN values
        data = data.dropna()
        
        # Make sure we have enough data for calculations
        if len(data) < 30:  # Need at least 30 candles for reliable indicators
            logging.warning(f"Not enough data points for {symbol}: only {len(data)} candles")
            return None
        
        # Extra debug for ITC
        if special_debug and interval == '1wk':
            logging.info(f"ITC WEEKLY DATA - Recent close prices:")
            for i in range(min(5, len(data))):
                idx = len(data) - 1 - i
                if idx >= 0:
                    logging.info(f"  {data.index[idx]}: Close={data['Close'].iloc[idx]:.2f}")
            
        data['Symbol'] = symbol
        logging.info(f"Successfully fetched {len(data)} data points for {symbol}")
        return data
        
    except Exception as e:
        logging.error(f"Error fetching data for {symbol}: {e}")
        return None
