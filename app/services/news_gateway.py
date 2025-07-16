"""
News API Gateway - Centralized interface for managing multiple news providers
"""
import os
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from collections import defaultdict

from .news_providers import (
    NewsProvider, NewsArticle, RateLimitStatus,
    FinnhubProvider, NewsAPIProvider, AlphaVantageProvider, YahooFinanceProvider,
    NewsProviderError, RateLimitExceededError
)


@dataclass
class ProviderHealth:
    """Health status of a news provider"""
    name: str
    is_healthy: bool
    last_check: datetime
    consecutive_failures: int
    rate_limit_status: RateLimitStatus


class FallbackManager:
    """Manages provider fallback logic"""
    
    def __init__(self):
        # Provider priority order (higher priority = preferred)
        self.provider_priority = {
            'newsapi': 4,      # Highest quality, but limited
            'alpha_vantage': 3, # Good quality, very limited
            'finnhub': 2,      # Good for financial news
            'yahoo': 1         # Fallback option, no API key needed
        }
        self.provider_health: Dict[str, ProviderHealth] = {}
    
    def get_provider_order(self, exclude: Set[str] = None) -> List[str]:
        """Get providers in priority order, excluding unhealthy ones"""
        exclude = exclude or set()
        
        # Filter out excluded and unhealthy providers
        available_providers = []
        for provider_name, priority in sorted(self.provider_priority.items(), 
                                            key=lambda x: x[1], reverse=True):
            if provider_name in exclude:
                continue
                
            health = self.provider_health.get(provider_name)
            if health and not health.is_healthy:
                continue
                
            available_providers.append(provider_name)
        
        return available_providers
    
    def update_provider_health(self, provider_name: str, is_healthy: bool, 
                             rate_limit_status: RateLimitStatus):
        """Update provider health status"""
        current_health = self.provider_health.get(provider_name)
        
        if current_health:
            if is_healthy:
                consecutive_failures = 0
            else:
                consecutive_failures = current_health.consecutive_failures + 1
        else:
            consecutive_failures = 0 if is_healthy else 1
        
        self.provider_health[provider_name] = ProviderHealth(
            name=provider_name,
            is_healthy=is_healthy,
            last_check=datetime.now(timezone.utc),
            consecutive_failures=consecutive_failures,
            rate_limit_status=rate_limit_status
        )


class RateLimiter:
    """Intelligent rate limiter for multiple providers"""
    
    def __init__(self):
        self.request_history: Dict[str, List[datetime]] = defaultdict(list)
        self.provider_limits = {
            'newsapi': {'per_hour': 100, 'per_day': 1000},
            'alpha_vantage': {'per_minute': 5, 'per_day': 500},
            'finnhub': {'per_minute': 60},
            'yahoo': {'per_minute': 100}  # Conservative estimate
        }
    
    def can_make_request(self, provider_name: str) -> bool:
        """Check if we can make a request to the provider"""
        now = datetime.now(timezone.utc)
        history = self.request_history[provider_name]
        limits = self.provider_limits.get(provider_name, {})
        
        # Clean old requests from history
        self._clean_history(provider_name, now)
        
        # Check per-minute limit
        if 'per_minute' in limits:
            recent_requests = [req for req in history if (now - req).total_seconds() < 60]
            if len(recent_requests) >= limits['per_minute']:
                return False
        
        # Check per-hour limit
        if 'per_hour' in limits:
            recent_requests = [req for req in history if (now - req).total_seconds() < 3600]
            if len(recent_requests) >= limits['per_hour']:
                return False
        
        # Check per-day limit
        if 'per_day' in limits:
            recent_requests = [req for req in history if (now - req).total_seconds() < 86400]
            if len(recent_requests) >= limits['per_day']:
                return False
        
        return True
    
    def record_request(self, provider_name: str):
        """Record a request to the provider"""
        self.request_history[provider_name].append(datetime.now(timezone.utc))
    
    def get_wait_time(self, provider_name: str) -> int:
        """Get seconds to wait before next request"""
        if self.can_make_request(provider_name):
            return 0
        
        now = datetime.now(timezone.utc)
        history = self.request_history[provider_name]
        limits = self.provider_limits.get(provider_name, {})
        
        wait_times = []
        
        # Check per-minute limit
        if 'per_minute' in limits:
            recent_requests = [req for req in history if (now - req).total_seconds() < 60]
            if len(recent_requests) >= limits['per_minute']:
                oldest_request = min(recent_requests)
                wait_times.append(60 - (now - oldest_request).total_seconds())
        
        return max(wait_times) if wait_times else 0
    
    def _clean_history(self, provider_name: str, now: datetime):
        """Clean old requests from history"""
        history = self.request_history[provider_name]
        # Keep only requests from the last day
        self.request_history[provider_name] = [
            req for req in history if (now - req).total_seconds() < 86400
        ]


class NewsAPIGateway:
    """Centralized news API gateway with intelligent fallback and rate limiting"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.providers: Dict[str, NewsProvider] = {}
        self.rate_limiter = RateLimiter()
        self.fallback_manager = FallbackManager()
        
        # Initialize providers
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available news providers"""
        # Finnhub provider
        finnhub_key = os.getenv('FINNHUB_API_KEY')
        if finnhub_key:
            self.providers['finnhub'] = FinnhubProvider(finnhub_key)
        
        # NewsAPI provider
        newsapi_key = os.getenv('NEWSAPI_KEY')
        if newsapi_key:
            self.providers['newsapi'] = NewsAPIProvider(newsapi_key)
        
        # Alpha Vantage provider
        alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if alpha_vantage_key:
            self.providers['alpha_vantage'] = AlphaVantageProvider(alpha_vantage_key)
        
        # Yahoo Finance provider (no API key needed)
        self.providers['yahoo'] = YahooFinanceProvider()
        
        self.logger.info(f"Initialized {len(self.providers)} news providers: {list(self.providers.keys())}")
    
    def fetch_news(self, symbols: List[str], provider: str = None, limit: int = 50) -> List[NewsArticle]:
        """
        Fetch news with automatic fallback
        
        Args:
            symbols: List of stock symbols
            provider: Specific provider to use (optional)
            limit: Maximum articles per symbol
            
        Returns:
            List of NewsArticle objects
        """
        if not symbols:
            return []
        
        all_articles = []
        
        for symbol in symbols:
            try:
                articles = self._fetch_news_for_symbol(symbol, provider, limit)
                all_articles.extend(articles)
            except Exception as e:
                self.logger.error(f"Failed to fetch news for {symbol}: {e}")
                continue
        
        # Deduplicate articles
        return self._deduplicate_articles(all_articles)
    
    def _fetch_news_for_symbol(self, symbol: str, preferred_provider: str = None, 
                              limit: int = 50) -> List[NewsArticle]:
        """Fetch news for a single symbol with fallback"""
        if preferred_provider and preferred_provider in self.providers:
            provider_order = [preferred_provider]
        else:
            provider_order = self.fallback_manager.get_provider_order()
        
        last_error = None
        
        for provider_name in provider_order:
            if provider_name not in self.providers:
                continue
            
            provider = self.providers[provider_name]
            
            try:
                # Check rate limits
                if not self.rate_limiter.can_make_request(provider_name):
                    wait_time = self.rate_limiter.get_wait_time(provider_name)
                    self.logger.warning(f"Rate limited for {provider_name}, need to wait {wait_time}s")
                    continue
                
                # Check provider health
                if not provider.is_healthy():
                    self.fallback_manager.update_provider_health(
                        provider_name, False, provider.get_rate_limit_status()
                    )
                    continue
                
                # Make the request
                self.rate_limiter.record_request(provider_name)
                articles = provider.fetch_news_for_symbol(symbol, limit)
                
                # Update health status
                self.fallback_manager.update_provider_health(
                    provider_name, True, provider.get_rate_limit_status()
                )
                
                self.logger.info(f"Successfully fetched {len(articles)} articles for {symbol} from {provider_name}")
                return articles
                
            except RateLimitExceededError as e:
                self.logger.warning(f"Rate limit exceeded for {provider_name}: {e}")
                self.fallback_manager.update_provider_health(
                    provider_name, False, provider.get_rate_limit_status()
                )
                last_error = e
                continue
                
            except NewsProviderError as e:
                self.logger.error(f"Provider {provider_name} failed: {e}")
                self.fallback_manager.update_provider_health(
                    provider_name, False, provider.get_rate_limit_status()
                )
                last_error = e
                continue
        
        # If all providers failed, raise the last error
        if last_error:
            raise last_error
        else:
            raise NewsProviderError(f"No available providers for symbol {symbol}")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available and healthy providers"""
        available = []
        for name, provider in self.providers.items():
            try:
                if provider.is_healthy():
                    available.append(name)
            except Exception:
                continue
        return available
    
    def get_provider_status(self) -> Dict[str, Dict]:
        """Get detailed status of all providers"""
        status = {}
        for name, provider in self.providers.items():
            try:
                is_healthy = provider.is_healthy()
                rate_limit = provider.get_rate_limit_status()
                
                status[name] = {
                    'healthy': is_healthy,
                    'rate_limit': {
                        'remaining': rate_limit.requests_remaining,
                        'limit': rate_limit.requests_limit,
                        'reset_time': rate_limit.reset_time.isoformat() if rate_limit.reset_time else None,
                        'is_limited': rate_limit.is_limited
                    }
                }
            except Exception as e:
                status[name] = {
                    'healthy': False,
                    'error': str(e)
                }
        
        return status
    
    def _deduplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Remove duplicate articles based on content hash"""
        seen_hashes = set()
        unique_articles = []
        
        for article in articles:
            content_hash = article.content_hash
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_articles.append(article)
        
        # Sort by publication date (newest first)
        unique_articles.sort(key=lambda x: x.published_at, reverse=True)
        
        return unique_articles
    
    def trigger_manual_refresh(self, symbols: List[str], force_provider: str = None) -> Dict[str, List[NewsArticle]]:
        """
        Trigger immediate manual news refresh
        
        Args:
            symbols: List of symbols to refresh
            force_provider: Force use of specific provider
            
        Returns:
            Dictionary mapping symbols to their articles
        """
        results = {}
        
        for symbol in symbols:
            try:
                articles = self._fetch_news_for_symbol(symbol, force_provider, limit=100)
                results[symbol] = articles
                self.logger.info(f"Manual refresh: {len(articles)} articles for {symbol}")
            except Exception as e:
                self.logger.error(f"Manual refresh failed for {symbol}: {e}")
                results[symbol] = []
        
        return results