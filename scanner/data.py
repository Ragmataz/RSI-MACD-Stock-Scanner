import yfinance as yf
import pandas as pd
import logging
import datetime

def get_data(symbol, interval='1d', force_download=False):
    """
    Get stock data with improved compatibility with TradingView calculations
    
    Args:
        symbol: The stock ticker symbol
        interval: Data interval (1d, 1wk, 1mo)
        force_download: Force fresh download instead of using cache
    """
    try:
        logging.info(f"Fetching data for {symbol} with interval {interval}")
        
        # Adjust period based on interval to ensure enough data for indicators
        if interval == '1mo':
            period = '5y'  # 5 years for monthly to get enough candles
        elif interval == '1wk':
            period = '2y'  # 2 years for weekly
        else:
            period = '1y'  # 1 year for daily
        
        # Get current time to ensure we have the latest data
        current_time = datetime.datetime.now()
        
        # For TradingView compatibility, ensure we get adjusted data
        data = yf.download(
            symbol, 
            period=period, 
            interval=interval, 
            auto_adjust=True,  # Important for TradingView compatibility
            progress=False
        )
        
        if data.empty or 'Close' not in data:
            logging.warning(f"No data available for {symbol}")
            return None

        # TradingView's indicator calculations typically ignore any candles with NaN values
        data = data.dropna()
        
        # Make sure we have enough data for calculations
        if len(data) < 30:  # Need at least 30 candles for reliable indicators
            logging.warning(f"Not enough data points for {symbol}: only {len(data)} candles")
            return None
            
        data['Symbol'] = symbol
        logging.info(f"Successfully fetched {len(data)} data points for {symbol}")
        
        # Log the last few candles to help with debugging
        logging.debug(f"Last 3 candles for {symbol}:\n{data.tail(3)}")
        
        return data
        
    except Exception as e:
        logging.error(f"Error fetching data for {symbol}: {e}")
        return None
