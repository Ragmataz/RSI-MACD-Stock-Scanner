import pandas as pd
import numpy as np
import logging

def calculate_rsi_macd(data, fast_length=8, slow_length=16, signal_length=11, 
                      rsi_length=10, oversold=49, overbought=51):
    """
    Calculate RSI and MACD using TradingView-compatible formulas
    """
    try:
        # Make a copy to avoid modifying the original
        df = data.copy()
        
        # Calculate EMAs for MACD - Using TradingView EMA formula
        # TradingView uses close prices for all calculations
        df['FastMA'] = df['Close'].ewm(span=fast_length, adjust=False).mean()
        df['SlowMA'] = df['Close'].ewm(span=slow_length, adjust=False).mean()
        df['MACD'] = df['FastMA'] - df['SlowMA']
        
        # TradingView uses SMA for signal line, not EMA
        df['Signal'] = df['MACD'].rolling(window=signal_length).mean()
        
        # Calculate RSI exactly as TradingView does
        delta = df['Close'].diff()
        gain = delta.copy()
        loss = delta.copy()
        gain[gain < 0] = 0
        loss[loss > 0] = 0
        loss = -loss  # Convert to positive values
        
        # First average gain and loss values
        avg_gain = gain.rolling(window=rsi_length).mean()
        avg_loss = loss.rolling(window=rsi_length).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Create flags for conditions
        df['SignalLessMacd'] = df['Signal'] < df['MACD']
        df['SignalGreaterMacd'] = df['Signal'] > df['MACD']
        df['RsiOverbought'] = df['RSI'] > overbought
        df['RsiOversold'] = df['RSI'] < oversold
        
        # Initialize Position column
        df['Position'] = 0
        
        # TradingView's position logic using previous positions
        # First row has no previous position to reference
        for i in range(1, len(df)):
            if df['RSI'].iloc[i] > overbought and df['Signal'].iloc[i] < df['MACD'].iloc[i]:
                df.loc[df.index[i], 'Position'] = 1  # Buy
            elif df['RSI'].iloc[i] < oversold and df['Signal'].iloc[i] > df['MACD'].iloc[i]:
                df.loc[df.index[i], 'Position'] = -1  # Sell
            else:
                # Keep previous position if conditions aren't met
                df.loc[df.index[i], 'Position'] = df['Position'].iloc[i-1]
        
        # Check for position change in the last candle
        signal = None
        
        if len(df) >= 3:  # Need at least 3 candles to detect changes
            current_position = df['Position'].iloc[-1]
            previous_position = df['Position'].iloc[-2]
            
            # Only report if position changed in latest candle
            if current_position != previous_position:
                if current_position == 1:
                    signal = 'BUY'
                    logging.info(f"BUY signal: RSI={df['RSI'].iloc[-1]:.2f}, MACD={df['MACD'].iloc[-1]:.4f}, Signal={df['Signal'].iloc[-1]:.4f}")
                elif current_position == -1:
                    signal = 'SELL'
                    logging.info(f"SELL signal: RSI={df['RSI'].iloc[-1]:.2f}, MACD={df['MACD'].iloc[-1]:.4f}, Signal={df['Signal'].iloc[-1]:.4f}")
                
                # Log extra debugging info for this stock
                logging.debug(f"Last 3 positions: {df['Position'].iloc[-3:]}")
                logging.debug(f"Last 3 RSI values: {df['RSI'].iloc[-3:]}")
                logging.debug(f"Last 3 MACD values: {df['MACD'].iloc[-3:]}")
                logging.debug(f"Last 3 Signal values: {df['Signal'].iloc[-3:]}")
        
        return signal, df
    except Exception as e:
        logging.error(f"Error in RSI_MACD calculation: {e}")
        return None, data
