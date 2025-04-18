import pandas as pd
import numpy as np
import logging

def calculate_rsi_macd(data, fast_length=8, slow_length=16, signal_length=11, 
                      rsi_length=10, oversold=49, overbought=51):
    try:
        # Calculate EMAs for MACD
        data['FastMA'] = data['Close'].ewm(span=fast_length, adjust=False).mean()
        data['SlowMA'] = data['Close'].ewm(span=slow_length, adjust=False).mean()
        data['MACD'] = data['FastMA'] - data['SlowMA']
        data['Signal'] = data['MACD'].ewm(span=signal_length, adjust=False).mean()  # Changed to EWM for consistency
        
        # Calculate RSI
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.ewm(span=rsi_length, adjust=False).mean()  # Changed to EWM for consistency
        avg_loss = loss.ewm(span=rsi_length, adjust=False).mean()  # Changed to EWM for consistency
        
        rs = avg_gain / avg_loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # Create position column using exactly the same logic as the TradingView script
        data['Position'] = 0
        
        # First row has no previous position to reference
        if len(data) > 0:
            data.loc[data.index[0], 'Position'] = 0
            
        # Replicate the TradingView logic exactly
        for i in range(1, len(data)):
            if data['RSI'].iloc[i] > overbought and data['Signal'].iloc[i] < data['MACD'].iloc[i]:
                data.loc[data.index[i], 'Position'] = 1
            elif data['RSI'].iloc[i] < oversold and data['Signal'].iloc[i] > data['MACD'].iloc[i]:
                data.loc[data.index[i], 'Position'] = -1
            else:
                # Keep previous position if conditions aren't met (this is what nz(pos[1], 0) does)
                data.loc[data.index[i], 'Position'] = data['Position'].iloc[i-1]
        
        # Check for a NEW signal in the last candle
        signal = None
        
        if len(data) >= 3:  # Need at least 3 candles to detect new signals properly
            current_position = data['Position'].iloc[-1]
            previous_position = data['Position'].iloc[-2]
            
            # Only report position if it changed in the latest candle
            if current_position != previous_position:
                if current_position == 1:
                    signal = 'BUY'
                    logging.info(f"BUY signal detected: RSI={data['RSI'].iloc[-1]:.2f}, MACD={data['MACD'].iloc[-1]:.4f}, Signal={data['Signal'].iloc[-1]:.4f}")
                elif current_position == -1:
                    signal = 'SELL'
                    logging.info(f"SELL signal detected: RSI={data['RSI'].iloc[-1]:.2f}, MACD={data['MACD'].iloc[-1]:.4f}, Signal={data['Signal'].iloc[-1]:.4f}")
        
        return signal, data
    except Exception as e:
        logging.error(f"Error in RSI_MACD calculation: {e}")
        return None, data
