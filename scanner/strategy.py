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
        
        # Create position column using exactly the same logic as the TradingView script
        data['Position'] = 0
        
        # First row has no previous position to reference
        if len(data) > 0:
            data.loc[data.index[0], 'Position'] = 0
            
        # Replicate the TradingView logic exactly:
        # pos = iff(xRSI > Overbought and signal < macd, 1,
        #        iff(xRSI < Oversold and signal > macd, -1, nz(pos[1], 0)))
        for i in range(1, len(data)):
            if data['RSI'].iloc[i] > overbought and data['Signal'].iloc[i] < data['MACD'].iloc[i]:
                data.loc[data.index[i], 'Position'] = 1
            elif data['RSI'].iloc[i] < oversold and data['Signal'].iloc[i] > data['MACD'].iloc[i]:
                data.loc[data.index[i], 'Position'] = -1
            else:
                # Keep previous position if conditions aren't met (this is what nz(pos[1], 0) does)
                data.loc[data.index[i], 'Position'] = data['Position'].iloc[i-1]
        
        # Check for a NEW signal in the last candle (position changed from previous)
        signal = None
        position_changed = False
        
        if len(data) >= 3:  # Need at least 3 candles to detect new signals properly
            current_position = data['Position'].iloc[-1]
            previous_position = data['Position'].iloc[-2]
            
            # Only report position if it changed in the latest candle
            if current_position != previous_position:
                position_changed = True
                if current_position == 1:
                    signal = 'BUY'
                elif current_position == -1:
                    signal = 'SELL'
        
        return signal, data, position_changed
    except Exception as e:
        print(f"Error in RSI_MACD calculation: {e}")
        return None, data, False
