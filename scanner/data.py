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
