import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
from cache_manager import CacheManager
import os

# Initialize cache manager
cache_manager = CacheManager()

def get_stock_data(symbol, period="1y", force_refresh=False):
    """Fetch stock data from Yahoo Finance with intelligent caching"""
    # Check if caching is enabled (default: True)
    enable_caching = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
    
    if not enable_caching or force_refresh:
        return _fetch_stock_data_direct(symbol, period)
    
    # Check for force refresh marker
    if cache_manager.should_force_refresh('stock_data', symbol, period=period):
        print(f"🔄 Force refreshing stock data for {symbol}")
        return _fetch_stock_data_direct(symbol, period)
    
    # Try to get cached data first
    cached_data = cache_manager.get_cached_data('stock_data', symbol, period=period)
    if cached_data is not None:
        print(f"📋 Using cached stock data for {symbol} (period: {period})")
        
        # Convert back to pandas DataFrame with proper attributes
        df = pd.DataFrame(cached_data['data'])
        
        # FIXED: Properly reconstruct the index using the stored date strings
        if 'index' in cached_data and cached_data['index']:
            df.index = pd.to_datetime(cached_data['index'])
        else:
            # Fallback: use the Date column if available
            if 'Date' in df.columns:
                df.index = pd.to_datetime(df['Date'])
                df = df.drop('Date', axis=1)  # Remove duplicate Date column
            else:
                # Last resort: try to convert the existing index
                df.index = pd.to_datetime(df.index)
        
        # Ensure proper timezone handling for the index
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        
        df.attrs['retrieval_timestamp'] = datetime.fromisoformat(cached_data['retrieval_timestamp'])
        df.attrs['symbol'] = cached_data['symbol']
        df.attrs['cached'] = True
        df.attrs['cached_at'] = cached_data['cached_at']
        return df
    
    # Fetch new data if not cached or expired
    print(f"🌐 Fetching fresh stock data for {symbol}")
    return _fetch_stock_data_direct(symbol, period)

def _fetch_stock_data_direct(symbol, period="1y"):
    """Direct fetch from Yahoo Finance without caching"""
    try:
        retrieval_timestamp = datetime.now(timezone.utc)
        stock = yf.Ticker(symbol)
        data = stock.history(period=period)
        if data.empty:
            print(f"No data found for {symbol}")
            return None
        
        # Add retrieval timestamp to the data
        data.attrs['retrieval_timestamp'] = retrieval_timestamp
        data.attrs['symbol'] = symbol
        data.attrs['cached'] = False
        
        # Cache the data for future use
        enable_caching = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
        if enable_caching:
            cache_data = {
                'data': data.reset_index().to_dict('records'),  # Convert to serializable format
                'retrieval_timestamp': retrieval_timestamp.isoformat(),
                'symbol': symbol,
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'period': period
            }
            
            # Store index separately for proper reconstruction
            cache_data['index'] = data.index.strftime('%Y-%m-%d').tolist()
            
            success = cache_manager.cache_data('stock_data', symbol, cache_data, period=period)
            if success:
                print(f"💾 Cached stock data for {symbol}")
            else:
                print(f"⚠️ Failed to cache stock data for {symbol}")
        
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def calculate_technical_indicators(stock_data, force_refresh=False):
    """Calculate technical indicators with intelligent caching"""
    if stock_data is None or stock_data.empty:
        return None
    
    symbol = stock_data.attrs.get('symbol', 'Unknown')
    
    # Check if caching is enabled and if we should use cached indicators
    enable_caching = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
    
    if not enable_caching or force_refresh:
        return _calculate_technical_indicators_direct(stock_data)
    
    # Check if data was already cached (from get_stock_data)
    was_stock_data_cached = stock_data.attrs.get('cached', False)
    
    # Generate cache key based on stock data characteristics
    last_data_point = stock_data.index[-1]
    cache_key_data = {
        'last_date': last_data_point.strftime('%Y-%m-%d'),
        'data_length': len(stock_data),
        'last_price': float(stock_data['Close'].iloc[-1])
    }
    
    # Check for force refresh marker
    if cache_manager.should_force_refresh('technical_indicators', symbol, **cache_key_data):
        print(f"🔄 Force refreshing technical indicators for {symbol}")
        return _calculate_technical_indicators_direct(stock_data)
    
    # Try to get cached indicators first
    cached_indicators = cache_manager.get_cached_data('technical_indicators', symbol, **cache_key_data)
    if cached_indicators is not None:
        print(f"📊 Using cached technical indicators for {symbol}")
        
        # Convert timestamps back to datetime objects
        for timestamp_field in ['data_timestamp', 'retrieval_timestamp', 'calculation_timestamp']:
            if timestamp_field in cached_indicators and isinstance(cached_indicators[timestamp_field], str):
                cached_indicators[timestamp_field] = datetime.fromisoformat(cached_indicators[timestamp_field])
        
        cached_indicators['cached'] = True
        return cached_indicators
    
    # Calculate new indicators if not cached or expired
    if was_stock_data_cached:
        print(f"📊 Calculating technical indicators for {symbol} (stock data was cached)")
    else:
        print(f"📊 Calculating technical indicators for {symbol} (fresh data)")
    
    return _calculate_technical_indicators_direct(stock_data)

def _calculate_technical_indicators_direct(stock_data):
    """Direct calculation of technical indicators without caching"""
    try:
        symbol = stock_data.attrs.get('symbol', 'Unknown')
        
        # Get the most recent data point
        latest_data = stock_data.iloc[-1]
        current_price = latest_data['Close']
        
        # Calculate RSI
        delta = stock_data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Calculate moving averages
        ma_20 = stock_data['Close'].rolling(window=20).mean()
        ma_50 = stock_data['Close'].rolling(window=50).mean()
        
        # Calculate MACD
        exp1 = stock_data['Close'].ewm(span=12).mean()
        exp2 = stock_data['Close'].ewm(span=26).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9).mean()
        
        # ENHANCED: Calculate volatility and market regime indicators
        # 1. Historical volatility (20-day)
        daily_returns = stock_data['Close'].pct_change()
        volatility = daily_returns.rolling(window=20).std() * (252 ** 0.5)  # Annualized
        
        # 2. Volume analysis
        avg_volume = stock_data['Volume'].rolling(window=20).mean()
        volume_ratio = stock_data['Volume'].iloc[-1] / avg_volume.iloc[-1] if avg_volume.iloc[-1] > 0 else 1
        
        # 3. Market regime detection
        price_momentum = (current_price - ma_50.iloc[-1]) / ma_50.iloc[-1] if ma_50.iloc[-1] > 0 else 0
        trend_strength = abs(price_momentum)
        
        # 4. Volatility-adjusted RSI thresholds
        vol_percentile = volatility.rank(pct=True).iloc[-1] if len(volatility.dropna()) > 0 else 0.5
        
        # Adjust RSI thresholds based on volatility
        if vol_percentile > 0.8:  # High volatility
            rsi_overbought = 75  # Higher threshold
            rsi_oversold = 25   # Lower threshold
        elif vol_percentile < 0.2:  # Low volatility
            rsi_overbought = 65  # Lower threshold
            rsi_oversold = 35   # Higher threshold
        else:  # Normal volatility
            rsi_overbought = 70
            rsi_oversold = 30
        
        # Get timestamps
        data_timestamp = stock_data.index[-1]  # Timestamp of the latest data point
        retrieval_timestamp = stock_data.attrs.get('retrieval_timestamp', datetime.now(timezone.utc))
        calculation_timestamp = datetime.now(timezone.utc)
        
        indicators = {
            'current_price': current_price,
            'rsi': rsi.iloc[-1],
            'ma_20': ma_20.iloc[-1],
            'ma_50': ma_50.iloc[-1],
            'macd': macd.iloc[-1],
            'signal': signal.iloc[-1],
            'volatility': volatility.iloc[-1],
            'volume_ratio': volume_ratio,
            'price_momentum': price_momentum,
            'trend_strength': trend_strength,
            'rsi_overbought': rsi_overbought,
            'rsi_oversold': rsi_oversold,
            # Timestamp tracking
            'data_timestamp': data_timestamp,           # When the stock data is from (last trading day)
            'retrieval_timestamp': retrieval_timestamp, # When we fetched the data
            'calculation_timestamp': calculation_timestamp, # When we calculated indicators
            'symbol': symbol,
            'cached': False
        }
        
        # Cache the indicators for future use
        enable_caching = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
        if enable_caching:
            # Prepare cache data (convert datetime objects to strings for JSON serialization)
            cache_data = indicators.copy()
            for timestamp_field in ['data_timestamp', 'retrieval_timestamp', 'calculation_timestamp']:
                if isinstance(cache_data[timestamp_field], (pd.Timestamp, datetime)):
                    cache_data[timestamp_field] = cache_data[timestamp_field].isoformat()
            
            # Cache key data
            cache_key_data = {
                'last_date': data_timestamp.strftime('%Y-%m-%d'),
                'data_length': len(stock_data),
                'last_price': float(current_price)
            }
            
            success = cache_manager.cache_data('technical_indicators', symbol, cache_data, **cache_key_data)
            if success:
                print(f"💾 Cached technical indicators for {symbol}")
            else:
                print(f"⚠️ Failed to cache technical indicators for {symbol}")
        
        return indicators
        
    except Exception as e:
        print(f"Error calculating technical indicators: {e}")
        return None 