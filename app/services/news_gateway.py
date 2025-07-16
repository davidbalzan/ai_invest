"""
News API Gateway with intelligent rate limiting and fallback mechanisms.
"""

import os
import time
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from .news_providers import (
    NewsProvider, NewsArticle, RateLimitStatus,
    NewsAPIProvider, FinnhubProvider, AlphaVantageProvider, YahooFinanceProvider,
    NewsProviderError, RateLimitExceededError
)


@dataclass
class ProviderHealth:
    """Health status of a news provider."""
    is_healthy: bool
    last_check: datetime
    consecutive_failures: int
    last_error: Optional[str] = None


class FallbackManager:
    """Manages provider fallback logic."""
    
    def __init__(self):
        self.provider_health: Dict[str, ProviderHealth] = {}
        self.health_check_interval = timedelta(minutes=5)
    
    def get_alternative_provider(self, failed_provider: str, available_providers: List[str]) -> Optional[str]:
        """Get the best alternative provider when one fails."""
        # Remove the failed provider from options
        alternatives = [p for p in available_providers if p != failed_provider]
        
        if not alternatives:
            return None
        
        # Sort by health status and preference
        provider_priority = {
            'finnhub': 1,      # Most reliable for stock news
            'newsapi': 2,      # Good general news coverage
            'alpha_vantage': 3, # Slower but comprehensive
            'yahoo': 4         # Fallback option
        }
        
        # Filter healthy providers
        healthy_alternatives = []
        for provider in alternatives:
            health = self.provider_health.get(provider)
            if not health or health.is_healthy:
                healthy_alternatives.append(provider)
        
        if not healthy_alternatives:
            # If no healthy alternatives, try the least recently failed
            return min(alternatives, key=lambda p: self.provider_health.get(p, ProviderHealth(True, datetime.min, 0)).consecutive_failures)
        
        # Return the highest priority healthy provider
        return min(healthy_alternatives, key=lambda p: provider_priority.get(p, 999))
    
    def record_failure(self, provider_name: str, error: str):
        """Record a provider failure."""
        if provider_name not in self.provider_health:
            self.provider_health[provider_name] = ProviderHealth(True, datetime.now(), 0)
        
        health = self.provider_health[provider_name]
        health.is_healthy = False
        health.consecutive_failures += 1
        health.last_error = error
        health.last_check = datetime.now()
    
    def record_success(self, provider_name: str):
        """Record a provider success."""
        if provider_name not in self.provider_health:
            self.provider_health[provider_name] = ProviderHealth(True, datetime.now(), 0)
        
        health = self.provider_health[provider_name]
        health.is_healthy = True
        health.consecutive_failures = 0
        health.last_error = None
        health.last_check = datetime.now()


class RateLimiter:
    """Intelligent rate limiter for multiple providers."""
    
    def __init__(self):
        self.provider_limits = {
            'newsapi': {'requests_per_day': 1000, 'requests_per_second': 1},
            'finnhub': {'requests_per_minute': 60, 'requests_per_second': 1},
            'alpha_vantage': {'requests_per_minute': 5, 'requests_per_second': 0.2},
            'yahoo': {'requests_per_minute': 100, 'requests_per_second': 1.67}
        }
        self.request_history: Dict[str, List[datetime]] = {}
    
    def can_make_request(self, provider_name: str) -> bool:
        """Check if we can make a request to the provider."""
        if provider_name not in self.provider_limits:
            return True
        
        limits = self.provider_limits[provider_name]
        history = self.request_history.get(provider_name, [])
        now = datetime.now()
        
        # Clean old requests from history
        if 'requests_per_day' in limits:
            cutoff = now - timedelta(days=1)
            history = [req_time for req_time in history if req_time > cutoff]
            if len(history) >= limits['requests_per_day']:
                return False
        
        if 'requests_per_minute' in limits:
            cutoff = now - timedelta(minutes=1)
            recent_requests = [req_time for req_time in history if req_time > cutoff]
            if len(recent_requests) >= limits['requests_per_minute']:
                return False
        
        if 'requests_per_second' in limits:
            cutoff = now - timedelta(seconds=1)
            very_recent = [req_time for req_time in history if req_time > cutoff]
            if len(very_recent) >= limits['requests_per_second']:
                return False
        
        return True
    
    def record_request(self, provider_name: str):
        """Record a request to the provider."""
        if provider_name not in self.request_history:
            self.request_history[provider_name] = []
        
        self.request_history[provider_name].append(datetime.now())
        
        # Keep only recent history to prevent memory bloat
        cutoff = datetime.now() - timedelta(days=1)
        self.request_history[provider_name] = [
            req_time for req_time in self.request_history[provider_name] 
            if req_time > cutoff
        ]


class NewsAPIGateway:
    """Centralized gateway for managing multiple news providers."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.providers: Dict[str, NewsProvider] = {}
        self.rate_limiter = RateLimiter()
        self.fallback_manager = FallbackManager()
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available news providers based on API keys."""
        # NewsAPI
        newsapi_key = os.getenv('NEWSAPI_API_KEY')
        if newsapi_key:
            try:
                self.providers['newsapi'] = NewsAPIProvider(newsapi_key)
                self.logger.info("NewsAPI provider initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize NewsAPI: {e}")
        
        # Finnhub
        finnhub_key = os.getenv('FINNHUB_API_KEY')
        if finnhub_key:
            try:
                self.providers['finnhub'] = FinnhubProvider(finnhub_key)
                self.logger.info("Finnhub provider initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Finnhub: {e}")
        
        # Alpha Vantage
        alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if alpha_vantage_key:
            try:
                self.providers['alpha_vantage'] = AlphaVantageProvider(alpha_vantage_key)
                self.logger.info("Alpha Vantage provider initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Alpha Vantage: {e}")
        
        # Yahoo Finance (no API key required)
        try:
            self.providers['yahoo'] = YahooFinanceProvider()
            self.logger.info("Yahoo Finance provider initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Yahoo Finance: {e}")
        
        if not self.providers:
            self.logger.warning("No news providers could be initialized")
    
    def fetch_news(self, symbols: List[str], provider: Optional[str] = None, limit: int = 50) -> List[NewsArticle]:
        """
        Fetch news with automatic fallback and deduplication.
        
        Args:
            symbols: List of stock symbols
            provider: Specific provider to use (optional)
            limit: Maximum articles per symbol
            
        Returns:
            List of deduplicated NewsArticle objects
        """
        if not symbols:
            return []
        
        all_articles = []
        
        for symbol in symbols:
            symbol_articles = self._fetch_news_for_symbol(symbol, provider, limit)
            all_articles.extend(symbol_articles)
        
        # Deduplicate articles
        return self._deduplicate_articles(all_articles)
    
    def _fetch_news_for_symbol(self, symbol: str, preferred_provider: Optional[str], limit: int) -> List[NewsArticle]:
        """Fetch news for a single symbol with fallback."""
        if not self.providers:
            self.logger.error("No news providers available")
            return []
        
        # Determine provider order
        if preferred_provider and preferred_provider in self.providers:
            provider_order = [preferred_provider] + [p for p in self.providers.keys() if p != preferred_provider]
        else:
            # Default order by reliability
            provider_order = ['finnhub', 'newsapi', 'alpha_vantage', 'yahoo']
            provider_order = [p for p in provider_order if p in self.providers]
        
        for provider_name in provider_order:
            try:
                # Check rate limits
                if not self.rate_limiter.can_make_request(provider_name):
                    self.logger.info(f"Rate limit reached for {provider_name}, trying next provider")
                    continue
                
                provider = self.providers[provider_name]
                
                # Check provider health
                if not provider.is_healthy():
                    self.logger.warning(f"Provider {provider_name} is unhealthy, trying next")
                    self.fallback_manager.record_failure(provider_name, "Health check failed")
                    continue
                
                # Make the request
                self.rate_limiter.record_request(provider_name)
                articles = provider.fetch_news_for_symbol(symbol, limit)
                
                # Record success
                self.fallback_manager.record_success(provider_name)
                
                self.logger.info(f"Successfully fetched {len(articles)} articles for {symbol} from {provider_name}")
                return articles
                
            except RateLimitExceededError as e:
                self.logger.warning(f"Rate limit exceeded for {provider_name}: {e}")
                self.fallback_manager.record_failure(provider_name, str(e))
                continue
                
            except NewsProviderError as e:
                self.logger.error(f"Provider {provider_name} failed: {e}")
                self.fallback_manager.record_failure(provider_name, str(e))
                continue
                
            except Exception as e:
                self.logger.error(f"Unexpected error with {provider_name}: {e}")
                self.fallback_manager.record_failure(provider_name, str(e))
                continue
        
        self.logger.warning(f"All providers failed for symbol {symbol}")
        return []
    
    def _deduplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Remove duplicate articles based on content hash."""
        seen_hashes: Set[str] = set()
        unique_articles = []
        
        for article in articles:
            content_hash = article.content_hash
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_articles.append(article)
        
        self.logger.info(f"Deduplicated {len(articles)} articles to {len(unique_articles)} unique articles")
        return unique_articles
    
    def get_available_providers(self) -> List[str]:
        """Get list of available and healthy providers."""
        healthy_providers = []
        for name, provider in self.providers.items():
            try:
                if provider.is_healthy():
                    healthy_providers.append(name)
            except:
                pass
        return healthy_providers
    
    def get_provider_status(self) -> Dict[str, Dict]:
        """Get status of all providers."""
        status = {}
        for name, provider in self.providers.items():
            try:
                rate_limit = provider.get_rate_limit_status()
                health = self.fallback_manager.provider_health.get(name)
                
                status[name] = {
                    'healthy': provider.is_healthy(),
                    'rate_limit': {
                        'remaining': rate_limit.requests_remaining,
                        'limit': rate_limit.requests_limit,
                        'usage_percentage': rate_limit.usage_percentage
                    },
                    'consecutive_failures': health.consecutive_failures if health else 0,
                    'last_error': health.last_error if health else None
                }
            except Exception as e:
                status[name] = {
                    'healthy': False,
                    'error': str(e)
                }
        
        return status