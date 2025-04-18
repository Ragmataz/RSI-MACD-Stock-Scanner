import pandas as pd
import numpy as np
import logging

def calculate_rsi_macd(data, fast_length=8, slow_length=16, signal_length=11, 
                      rsi_length=10, oversold=49, overbought=51):
    try:
        # Save symbol for logging
        symbol = data['Symbol'].iloc[0] if 'Symbol' in data.columns else 'Unknown'
        timeframe = data.index.freq if hasattr(data.index, 'freq') else 'Unknown'
        
        # Calculate EMAs for MACD - EXACTLY as in TradingView PineScript
        data['FastMA'] = data['Close'].ewm(span=fast_length, adjust=False).mean()
        data['SlowMA'] = data['Close'].ewm(span=slow_length, adjust=False).mean()
        data['MACD'] = data['FastMA'] - data['SlowMA']
        data['Signal'] = data['MACD'].ewm(span=signal_length, adjust=False).mean()  # Changed to EWM for consistency with TV
        
        # Calculate RSI - EXACTLY as in TradingView
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Use EWM instead of SMA for RSI calculation to match TradingView
        avg_gain = gain.ewm(alpha=1/rsi_length, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/rsi_length, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # Logging intermediate values for debugging
        logging.info(f"Symbol: {symbol} - Last values: Close={data['Close'].iloc[-1]:.2f}, RSI={data['RSI'].iloc[-1]:.2f}, "
                    f"MACD={data['MACD'].iloc[-1]:.4f}, Signal={data['Signal'].iloc[-1]:.4f}")
        
        # Create position column using exactly the same logic as the TradingView script
        data['Position'] = 0
        
        # Replicate the TradingView logic exactly:
        # pos = iff(xRSI > Overbought and signal < macd, 1,
        #      iff(xRSI < Oversold and signal > macd, -1, nz(pos[1], 0)))
        
        # First row has no previous position to reference
        if len(data) > 0:
            data.loc[data.index[0], 'Position'] = 0
            
        # Apply position logic to all candles
        for i in range(1, len(data)):
            rsi_value = data['RSI'].iloc[i]
            macd_value = data['MACD'].iloc[i]
            signal_value = data['Signal'].iloc[i]
            
            if rsi_value > overbought and signal_value < macd_value:
                data.loc[data.index[i], 'Position'] = 1
            elif rsi_value < oversold and signal_value > macd_value:
                data.loc[data.index[i], 'Position'] = -1
            else:
                # Keep previous position if conditions aren't met (this is what nz(pos[1], 0) does)
                data.loc[data.index[i], 'Position'] = data['Position'].iloc[i-1]
        
        # Debug if the last 3 positions to see transitions
        if len(data) >= 3:
            pos_3 = data['Position'].iloc[-3] if len(data) >= 3 else None
            pos_2 = data['Position'].iloc[-2]
            pos_1 = data['Position'].iloc[-1]
            
            logging.info(f"{symbol}: Last 3 positions = [{pos_3}, {pos_2}, {pos_1}]")
            logging.info(f"{symbol}: Last candle conditions: RSI={data['RSI'].iloc[-1]:.2f} (threshold={overbought}/{oversold}), "
                       f"MACD={data['MACD'].iloc[-1]:.4f}, Signal={data['Signal'].iloc[-1]:.4f}")
        
        # Detect signal ONLY if the position changed in the LAST candle
        signal = None
        if len(data) >= 2:  
            current_position = data['Position'].iloc[-1]
            previous_position = data['Position'].iloc[-2]
            
            # Only report if there was a FRESH position change
            if current_position != previous_position:
                if current_position == 1:
                    signal = 'BUY'
                    logging.info(f"✅ BUY signal detected for {symbol}: Position changed from {previous_position} to {current_position}")
                elif current_position == -1:
                    signal = 'SELL'
                    logging.info(f"🚨 SELL signal detected for {symbol}: Position changed from {previous_position} to {current_position}")
        
        return signal, data
    except Exception as e:
        logging.error(f"Error in RSI_MACD calculation: {e}")
        return None, data
