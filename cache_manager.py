import json
import os
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Union
import pytz
from market_scheduler import MarketScheduler

class CacheManager:
    """
    Intelligent cache manager with timezone-aware expiration policies
    Optimizes API costs by caching data with appropriate freshness rules
    """
    
    def __init__(self, cache_dir: str = None):
        import os
        self.cache_dir = cache_dir or os.getenv('CACHE_DIRECTORY', 'cache')
        self.market_scheduler = MarketScheduler()
        self.ensure_directories()
        
        # Cache expiration policies (in minutes) with environment variable overrides
        self.cache_policies = self._load_cache_policies()
    
    def ensure_directories(self):
        """Create necessary cache directories"""
        directories = [
            self.cache_dir,
            os.path.join(self.cache_dir, "stock_data"),
            os.path.join(self.cache_dir, "sentiment_data"),
            os.path.join(self.cache_dir, "ai_recommendations"),
            os.path.join(self.cache_dir, "technical_indicators"),
            os.path.join(self.cache_dir, "processed_news"),
            os.path.join(self.cache_dir, "metadata")
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def _load_cache_policies(self):
        """Load cache policies with environment variable overrides"""
        import os
        
        # Updated policies for more sensible fresh data handling
        default_policies = {
            'stock_data': {
                'market_hours': 2,          # 2 minutes during market hours (more responsive)
                'pre_post_market': 10,      # 10 minutes during pre/post market  
                'market_closed': 30,        # 30 minutes when market is closed (reduced from 60)
                'weekend': 480,             # 8 hours on weekends (reduced from 24h)
                'holiday': 480              # 8 hours on holidays
            },
            'sentiment_data': {
                'market_hours': 10,         # 10 minutes during market hours (much fresher than 30)
                'pre_post_market': 20,      # 20 minutes during pre/post market (reduced from 60)
                'market_closed': 60,        # 1 hour when market is closed (reduced from 4h)
                'weekend': 240,             # 4 hours on weekends (reduced from 24h)
                'holiday': 240              # 4 hours on holidays (much fresher)
            },
            'ai_recommendations': {
                'market_hours': 5,          # 5 minutes during market hours (reduced from 10)
                'pre_post_market': 15,      # 15 minutes during pre/post market (reduced from 30)
                'market_closed': 60,        # 1 hour when market is closed (reduced from 2h)
                'weekend': 240,             # 4 hours on weekends (reduced from 12h)
                'holiday': 240              # 4 hours on holidays
            },
            'technical_indicators': {
                'market_hours': 2,          # 2 minutes during market hours (same as stock data)
                'pre_post_market': 10,      # 10 minutes during pre/post market
                'market_closed': 30,        # 30 minutes when market is closed
                'weekend': 480,             # 8 hours on weekends 
                'holiday': 480              # 8 hours on holidays
            },
            'processed_news': {
                'market_hours': 30,         # 30 minutes during market hours (processed news can be cached longer)
                'pre_post_market': 60,      # 1 hour during pre/post market
                'market_closed': 120,       # 2 hours when market is closed
                'weekend': 720,             # 12 hours on weekends
                'holiday': 720              # 12 hours on holidays
            }
        }
        
        # Environment variable overrides
        env_overrides = {
            'stock_data': {
                'market_hours': 'CACHE_STOCK_DATA_MARKET_HOURS',
                'pre_post_market': 'CACHE_STOCK_DATA_PRE_POST',
                'market_closed': 'CACHE_STOCK_DATA_CLOSED',
                'weekend': 'CACHE_STOCK_DATA_WEEKEND',
                'holiday': 'CACHE_STOCK_DATA_WEEKEND'  # Use weekend setting for holidays
            },
            'sentiment_data': {
                'market_hours': 'CACHE_SENTIMENT_MARKET_HOURS',
                'pre_post_market': 'CACHE_SENTIMENT_PRE_POST',
                'market_closed': 'CACHE_SENTIMENT_CLOSED',
                'weekend': 'CACHE_SENTIMENT_WEEKEND',
                'holiday': 'CACHE_SENTIMENT_WEEKEND'
            },
            'ai_recommendations': {
                'market_hours': 'CACHE_AI_RECOMMENDATIONS_MARKET_HOURS',
                'pre_post_market': 'CACHE_AI_RECOMMENDATIONS_PRE_POST',
                'market_closed': 'CACHE_AI_RECOMMENDATIONS_CLOSED',
                'weekend': 'CACHE_AI_RECOMMENDATIONS_WEEKEND',
                'holiday': 'CACHE_AI_RECOMMENDATIONS_WEEKEND'
            },
            'technical_indicators': {
                'market_hours': 'CACHE_STOCK_DATA_MARKET_HOURS',  # Use stock data settings
                'pre_post_market': 'CACHE_STOCK_DATA_PRE_POST',
                'market_closed': 'CACHE_STOCK_DATA_CLOSED',
                'weekend': 'CACHE_STOCK_DATA_WEEKEND',
                'holiday': 'CACHE_STOCK_DATA_WEEKEND'
            }
        }
        
        # Apply environment variable overrides
        for data_type, periods in env_overrides.items():
            for period, env_var in periods.items():
                env_value = os.getenv(env_var)
                if env_value and env_value.isdigit():
                    default_policies[data_type][period] = int(env_value)
        
        return default_policies
    
    def _get_cache_key(self, data_type: str, identifier: str, **kwargs) -> str:
        """Generate consistent cache key"""
        # Include relevant parameters in the key
        key_components = [data_type, identifier]
        
        # Add sorted kwargs to ensure consistent keys
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_components.extend([f"{k}={v}" for k, v in sorted_kwargs])
        
        key_string = "|".join(str(comp) for comp in key_components)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_filepath(self, data_type: str, cache_key: str) -> str:
        """Get cache file path for given data type and key"""
        return os.path.join(self.cache_dir, data_type, f"{cache_key}.json")
    
    def _get_current_market_session(self) -> str:
        """Get current market session for cache policy selection"""
        current_time = datetime.now(timezone.utc)
        session = self.market_scheduler.get_market_session(current_time)
        
        # Check if it's weekend or holiday
        market_tz = pytz.timezone('America/New_York')
        current_market_time = current_time.astimezone(market_tz)
        
        # Simple weekend check
        if current_market_time.weekday() >= 5:  # Saturday=5, Sunday=6
            return 'weekend'
        
        # Map MarketSession enum to our cache policy keys
        from market_scheduler import MarketSession
        
        if session in [MarketSession.MARKET_OPEN, MarketSession.MARKET_CLOSE]:
            return 'market_hours'
        elif session in [MarketSession.PRE_MARKET, MarketSession.POST_MARKET]:
            return 'pre_post_market'
        elif session == MarketSession.WEEKEND:
            return 'weekend'
        else:
            return 'market_closed'
    
    def _get_cache_expiration_minutes(self, data_type: str) -> int:
        """Get cache expiration time in minutes based on current market session"""
        market_session = self._get_current_market_session()
        
        if data_type in self.cache_policies:
            return self.cache_policies[data_type].get(market_session, 60)
        else:
            # Default cache policy
            default_policies = {
                'market_hours': 10,
                'pre_post_market': 30,
                'market_closed': 60,
                'weekend': 1440,
                'holiday': 1440
            }
            return default_policies.get(market_session, 60)
    
    def is_cache_valid(self, data_type: str, identifier: str, **kwargs) -> bool:
        """Check if cached data is still valid"""
        cache_key = self._get_cache_key(data_type, identifier, **kwargs)
        filepath = self._get_cache_filepath(data_type, cache_key)
        
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'r') as f:
                cached_data = json.load(f)
            
            cached_time = datetime.fromisoformat(cached_data['cached_at'])
            current_time = datetime.now(timezone.utc)
            
            # Get expiration time based on current market session
            expiration_minutes = self._get_cache_expiration_minutes(data_type)
            expiration_time = cached_time + timedelta(minutes=expiration_minutes)
            
            is_valid = current_time < expiration_time
            
            # Additional validation for date changes
            if is_valid:
                is_valid = self._validate_date_context(cached_data, data_type)
            
            return is_valid
            
        except Exception as e:
            print(f"Error checking cache validity for {data_type}/{identifier}: {e}")
            return False
    
    def _validate_date_context(self, cached_data: dict, data_type: str) -> bool:
        """Additional validation for date-sensitive data"""
        cached_time = datetime.fromisoformat(cached_data['cached_at'])
        current_time = datetime.now(timezone.utc)
        
        # For stock data, invalidate if we've crossed into a new trading day
        if data_type in ['stock_data', 'technical_indicators']:
            market_tz = pytz.timezone('America/New_York')
            cached_market_time = cached_time.astimezone(market_tz)
            current_market_time = current_time.astimezone(market_tz)
            
            # If we've moved to a new trading day, invalidate cache
            if cached_market_time.date() != current_market_time.date():
                # Check if this is a new trading day (not just calendar day)
                if self._is_new_trading_day(cached_market_time, current_market_time):
                    return False
        
        return True
    
    def _is_new_trading_day(self, cached_time: datetime, current_time: datetime) -> bool:
        """Check if we've moved to a new trading day"""
        # Simple check: if dates are different and current time is after 9:30 AM ET
        if cached_time.date() != current_time.date():
            if current_time.hour >= 9 and current_time.minute >= 30:
                return True
        return False
    
    def get_cached_data(self, data_type: str, identifier: str, **kwargs) -> Optional[Dict]:
        """Retrieve cached data if valid"""
        if not self.is_cache_valid(data_type, identifier, **kwargs):
            return None
        
        cache_key = self._get_cache_key(data_type, identifier, **kwargs)
        filepath = self._get_cache_filepath(data_type, cache_key)
        
        try:
            with open(filepath, 'r') as f:
                cached_data = json.load(f)
            
            # Return only the data portion, not metadata
            return cached_data['data']
            
        except Exception as e:
            print(f"Error reading cached data for {data_type}/{identifier}: {e}")
            return None
    
    def should_force_refresh(self, data_type: str, identifier: str, **kwargs) -> bool:
        """Check if data should be force refreshed based on user requests or data age"""
        # For comprehensive analysis, prefer fresher data
        if kwargs.get('force_refresh', False):
            return True
            
        # If cached data is very old (beyond reasonable limits), force refresh
        cache_key = self._get_cache_key(data_type, identifier, **kwargs)
        filepath = self._get_cache_filepath(data_type, cache_key)
        
        if not os.path.exists(filepath):
            return True
            
        try:
            with open(filepath, 'r') as f:
                cached_data = json.load(f)
            
            cached_time = datetime.fromisoformat(cached_data['cached_at'])
            current_time = datetime.now(timezone.utc)
            age_hours = (current_time - cached_time).total_seconds() / 3600
            
            # Force refresh if data is absurdly old
            max_age_limits = {
                'sentiment_data': 24,    # News should never be more than 24h old
                'ai_recommendations': 12, # AI responses should be fresh
                'stock_data': 48,        # Stock data can be a bit older
                'technical_indicators': 48
            }
            
            max_age = max_age_limits.get(data_type, 24)
            if age_hours > max_age:
                print(f"🔄 Force refreshing {data_type} for {identifier} - data is {age_hours:.1f}h old (max: {max_age}h)")
                return True
                
        except Exception:
            return True  # Force refresh on corrupted cache
            
        return False

    def cache_data(self, data_type: str, identifier: str, data: Any, **kwargs) -> bool:
        """Cache data with metadata"""
        cache_key = self._get_cache_key(data_type, identifier, **kwargs)
        filepath = self._get_cache_filepath(data_type, cache_key)
        
        try:
            current_time = datetime.now(timezone.utc)
            market_session = self._get_current_market_session()
            
            cache_entry = {
                'data': data,
                'cached_at': current_time.isoformat(),
                'data_type': data_type,
                'identifier': identifier,
                'market_session_when_cached': market_session,
                'cache_key': cache_key,
                'expiration_minutes': self._get_cache_expiration_minutes(data_type),
                'kwargs': kwargs
            }
            
            with open(filepath, 'w') as f:
                json.dump(cache_entry, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            print(f"Error caching data for {data_type}/{identifier}: {e}")
            return False
    
    def invalidate_cache(self, data_type: str = None, identifier: str = None, **kwargs) -> int:
        """Invalidate cached data. Returns number of items removed."""
        removed_count = 0
        
        if data_type and identifier:
            # Invalidate specific cache entry
            cache_key = self._get_cache_key(data_type, identifier, **kwargs)
            filepath = self._get_cache_filepath(data_type, cache_key)
            if os.path.exists(filepath):
                os.remove(filepath)
                removed_count = 1
        elif data_type:
            # Invalidate all cache entries for a data type
            data_type_dir = os.path.join(self.cache_dir, data_type)
            if os.path.exists(data_type_dir):
                for filename in os.listdir(data_type_dir):
                    if filename.endswith('.json'):
                        os.remove(os.path.join(data_type_dir, filename))
                        removed_count += 1
        else:
            # Invalidate all cache
            for data_type_name in ['stock_data', 'sentiment_data', 'ai_recommendations', 'technical_indicators', 'processed_news']:
                data_type_dir = os.path.join(self.cache_dir, data_type_name)
                if os.path.exists(data_type_dir):
                    for filename in os.listdir(data_type_dir):
                        if filename.endswith('.json'):
                            os.remove(os.path.join(data_type_dir, filename))
                            removed_count += 1
        
        return removed_count
    
    def clear_stale_cache(self, data_type: str = None, max_age_hours: float = None) -> int:
        """Clear cache entries older than specified age. Returns number of items removed."""
        removed_count = 0
        current_time = datetime.now(timezone.utc)
        
        # Default max ages for different data types
        default_max_ages = {
            'sentiment_data': 12,     # News data older than 12h
            'ai_recommendations': 6,  # AI responses older than 6h  
            'stock_data': 24,         # Stock data older than 24h
            'technical_indicators': 24
        }
        
        data_types = [data_type] if data_type else ['stock_data', 'sentiment_data', 'ai_recommendations', 'technical_indicators', 'processed_news']
        
        for data_type_name in data_types:
            data_type_dir = os.path.join(self.cache_dir, data_type_name)
            if not os.path.exists(data_type_dir):
                continue
            
            # Use provided max_age or default for this data type
            max_age = max_age_hours if max_age_hours is not None else default_max_ages.get(data_type_name, 12)
            max_age_timedelta = timedelta(hours=max_age)
                
            for filename in os.listdir(data_type_dir):
                if not filename.endswith('.json'):
                    continue
                    
                filepath = os.path.join(data_type_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        cached_data = json.load(f)
                    
                    cached_time = datetime.fromisoformat(cached_data['cached_at'])
                    
                    if current_time - cached_time > max_age_timedelta:
                        os.remove(filepath)
                        removed_count += 1
                        print(f"🗑️ Removed stale {data_type_name} cache: {filename}")
                        
                except Exception as e:
                    print(f"Error processing cache file {filename}: {e}")
                    # Remove corrupted cache files
                    os.remove(filepath)
                    removed_count += 1
        
        return removed_count

    def cleanup_expired_cache(self) -> int:
        """Remove expired cache entries. Returns number of items removed."""
        removed_count = 0
        current_time = datetime.now(timezone.utc)
        
        for data_type_name in ['stock_data', 'sentiment_data', 'ai_recommendations', 'technical_indicators', 'processed_news']:
            data_type_dir = os.path.join(self.cache_dir, data_type_name)
            if not os.path.exists(data_type_dir):
                continue
                
            for filename in os.listdir(data_type_dir):
                if not filename.endswith('.json'):
                    continue
                    
                filepath = os.path.join(data_type_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        cached_data = json.load(f)
                    
                    cached_time = datetime.fromisoformat(cached_data['cached_at'])
                    expiration_minutes = cached_data.get('expiration_minutes', 60)
                    expiration_time = cached_time + timedelta(minutes=expiration_minutes)
                    
                    if current_time >= expiration_time:
                        os.remove(filepath)
                        removed_count += 1
                        
                except Exception as e:
                    print(f"Error processing cache file {filename}: {e}")
                    # Remove corrupted cache files
                    os.remove(filepath)
                    removed_count += 1
        
        return removed_count
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        stats = {
            'total_entries': 0,
            'by_type': {},
            'total_size_mb': 0,
            'expired_entries': 0,
            'current_market_session': self._get_current_market_session()
        }
        
        current_time = datetime.now(timezone.utc)
        total_size = 0
        
        for data_type_name in ['stock_data', 'sentiment_data', 'ai_recommendations', 'technical_indicators', 'processed_news']:
            data_type_dir = os.path.join(self.cache_dir, data_type_name)
            if not os.path.exists(data_type_dir):
                stats['by_type'][data_type_name] = {'count': 0, 'expired': 0, 'size_mb': 0}
                continue
            
            type_count = 0
            type_expired = 0
            type_size = 0
            
            for filename in os.listdir(data_type_dir):
                if not filename.endswith('.json'):
                    continue
                
                filepath = os.path.join(data_type_dir, filename)
                try:
                    file_size = os.path.getsize(filepath)
                    type_size += file_size
                    total_size += file_size
                    type_count += 1
                    
                    with open(filepath, 'r') as f:
                        cached_data = json.load(f)
                    
                    cached_time = datetime.fromisoformat(cached_data['cached_at'])
                    expiration_minutes = cached_data.get('expiration_minutes', 60)
                    expiration_time = cached_time + timedelta(minutes=expiration_minutes)
                    
                    if current_time >= expiration_time:
                        type_expired += 1
                        
                except Exception:
                    type_expired += 1  # Count corrupted files as expired
            
            stats['by_type'][data_type_name] = {
                'count': type_count,
                'expired': type_expired,
                'size_mb': round(type_size / (1024 * 1024), 2)
            }
            stats['total_entries'] += type_count
            stats['expired_entries'] += type_expired
        
        stats['total_size_mb'] = round(total_size / (1024 * 1024), 2)
        return stats
    
    def force_refresh_next_call(self, data_type: str = None, identifier: str = None, **kwargs):
        """Mark cache for refresh on next call (useful for forced updates)"""
        if data_type and identifier:
            # Create a temporary marker file
            cache_key = self._get_cache_key(data_type, identifier, **kwargs)
            marker_file = self._get_cache_filepath(data_type, f"{cache_key}.refresh")
            
            try:
                with open(marker_file, 'w') as f:
                    json.dump({
                        'refresh_requested_at': datetime.now(timezone.utc).isoformat(),
                        'data_type': data_type,
                        'identifier': identifier
                    }, f)
            except Exception as e:
                print(f"Error creating refresh marker: {e}")
    
    def should_force_refresh(self, data_type: str, identifier: str, **kwargs) -> bool:
        """Check if data should be force refreshed"""
        cache_key = self._get_cache_key(data_type, identifier, **kwargs)
        marker_file = self._get_cache_filepath(data_type, f"{cache_key}.refresh")
        
        if os.path.exists(marker_file):
            # Remove marker file and return True
            try:
                os.remove(marker_file)
                return True
            except Exception:
                pass
        
        return False 