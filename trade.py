import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

def get_prediction(symbol: str) -> str:
    debug_info = []
    
    try:
        debug_info.append("Starting analysis...")
        
        # Download data with explicit error handling
        debug_info.append(f"Downloading data for {symbol}...")
        try:
            df = yf.download(symbol, period="1mo", interval="1d", progress=False)
            debug_info.append(f"Downloaded {len(df)} rows of data")
        except Exception as e:
            return f"⚠️ Error downloading data for {symbol}: {str(e)}"
        
        # Check if data is valid
        if df.empty:
            return f"❌ No data available for {symbol}. Please check the symbol."
        
        if len(df) < 5:
            return f"❌ Not enough data for {symbol}. Only {len(df)} days available."
        
        # Print column names for debugging
        debug_info.append(f"DataFrame columns: {list(df.columns)}")
        
        # Check for required columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return f"❌ Missing required columns for {symbol}: {missing_columns}"
        
        # Check for NaN values
        nan_counts = df.isna().sum()
        if nan_counts.sum() > 0:
            debug_info.append(f"Warning: Found NaN values: {nan_counts.to_dict()}")
            # Fill NaN values
            df = df.fillna(method='ffill').fillna(method='bfill')
        
        # Get basic price information with safe access
        try:
            last_close = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2]) if len(df) > 1 else last_close
            last_volume = float(df['Volume'].iloc[-1])
            debug_info.append(f"Last close: {last_close}, Previous close: {prev_close}")
        except Exception as e:
            return f"⚠️ Error accessing price data: {str(e)}\nDebug info: {' | '.join(debug_info)}"
        
        # Calculate price change
        try:
            price_change = ((last_close - prev_close) / prev_close) * 100 if prev_close != 0 else 0
            debug_info.append(f"Price change: {price_change:.2f}%")
        except Exception as e:
            debug_info.append(f"Error calculating price change: {str(e)}")
            price_change = 0
        
        # Simple trend calculation
        try:
            if len(df) >= 7:
                recent_mean = df['Close'].iloc[-7:].mean()
                previous_mean = df['Close'].iloc[-14:-7].mean() if len(df) >= 14 else df['Close'].iloc[:-7].mean()
                short_trend = "Uptrend 📈" if recent_mean > previous_mean else "Downtrend 📉"
            else:
                short_trend = "Neutral ⚖️"
            debug_info.append(f"Trend: {short_trend}")
        except Exception as e:
            debug_info.append(f"Error calculating trend: {str(e)}")
            short_trend = "Neutral ⚖️"
        
        # Simplified RSI calculation
        try:
            # Calculate daily changes
            delta = df['Close'].diff().dropna()
            
            # Separate gains and losses
            gains = delta.copy()
            losses = delta.copy()
            gains[gains < 0] = 0
            losses[losses > 0] = 0
            losses = abs(losses)
            
            # Calculate average gains and losses over 14 periods
            avg_gain = gains.rolling(window=14, min_periods=1).mean()
            avg_loss = losses.rolling(window=14, min_periods=1).mean()
            
            # Calculate RS and RSI
            rs = avg_gain / avg_loss.replace(0, 0.001)  # Avoid division by zero
            rsi = 100 - (100 / (1 + rs))
            
            # Get the last RSI value
            last_rsi = float(rsi.iloc[-1])
            debug_info.append(f"RSI: {last_rsi:.2f}")
        except Exception as e:
            debug_info.append(f"Error calculating RSI: {str(e)}")
            last_rsi = 50  # Neutral default
        
        # Simplified ATR calculation
        try:
            # Calculate True Range
            tr1 = df['High'] - df['Low']
            tr2 = abs(df['High'] - df['Close'].shift())
            tr3 = abs(df['Low'] - df['Close'].shift())
            
            # True Range is the maximum of the three
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # ATR is the average of True Range
            atr = tr.rolling(window=14, min_periods=1).mean()
            
            # Get the last ATR value
            last_atr = float(atr.iloc[-1])
            debug_info.append(f"ATR: {last_atr:.2f}")
        except Exception as e:
            debug_info.append(f"Error calculating ATR: {str(e)}")
            last_atr = last_close * 0.02  # Default to 2% of price
        
        # Signal logic based on RSI
        if last_rsi < 30:
            signal = "BUY 🟢"
            rsi_note = "Oversold"
            strength = "Strong" if last_rsi < 20 else "Moderate"
        elif last_rsi > 70:
            signal = "SELL 🔴"
            rsi_note = "Overbought"
            strength = "Strong" if last_rsi > 80 else "Moderate"
        else:
            signal = "HOLD 🟡"
            rsi_note = "Neutral"
            strength = "Neutral"
        
        # Support and resistance levels
        support = last_close - last_atr
        resistance = last_close + last_atr
        
        # Format volume
        if last_volume >= 1_000_000:
            volume_str = f"{last_volume/1_000_000:.2f}M"
        else:
            volume_str = f"{last_volume/1_000:.2f}K"
        
        # Get current date
        current_date = datetime.now().strftime("%d %b %Y, %H:%M")
        
        debug_info.append("Analysis completed successfully")
        
        # Build detailed response
        return (
            f"📊 *{symbol}* Analysis  |  {current_date}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔔 *Signal: {signal}*  ({strength})\n\n"
            f"💹 *Price Action*\n"
            f"• Last Close: ₹{last_close:.2f}\n"
            f"• Day Change: {price_change:.2f}%\n"
            f"• Volume: {volume_str}\n"
            f"• Trend: {short_trend}\n\n"
            f"🎯 *Trade Levels*\n"
            f"• Support: ₹{support:.2f}\n"
            f"• Resistance: ₹{resistance:.2f}\n"
            f"• Buy Below: ₹{support:.2f}\n"
            f"• Sell Above: ₹{resistance:.2f}\n\n"
            f"📈 *Technical Indicators*\n"
            f"• RSI (14): {last_rsi:.2f} → {rsi_note}\n"
            f"• ATR (14): ₹{last_atr:.2f}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Disclaimer:* This is not financial advice. Always do your own research."
        )
    
    except Exception as e:
        debug_str = " | ".join(debug_info)
        return f"⚠️ Error processing {symbol}: {str(e)}\nDebug info: {debug_str}"