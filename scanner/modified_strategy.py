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
        
        # Check for NEW signal in last candle (position changed from previous candle)
        signal = None
        if len(data) >= 2:  # Make sure we have at least 2 candles to compare
            current_position = data['Position'].iloc[-1]
            previous_position = data['Position'].iloc[-2]
            
            # Check if there was a position change (fresh signal)
            if current_position == 1 and previous_position != 1:
                signal = 'BUY'
            elif current_position == -1 and previous_position != -1:
                signal = 'SELL'
        
        return signal, data
    except Exception as e:
        print(f"Error in RSI_MACD calculation: {e}")
        return None, data
