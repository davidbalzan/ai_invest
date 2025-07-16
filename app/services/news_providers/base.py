"""
Base classes and data models for news providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
import hashlib


@dataclass
class NewsArticle:
    """Standard news article data model."""
    title: str
    description: Optional[str]
    content: Optional[str]
    url: str
    url_to_image: Optional[str]
    source_name: str
    source_id: Optional[str]
    author: Optional[str]
    published_at: datetime
    symbol: Optional[str] = None  # Associated stock symbol
    
    @property
    def content_hash(self) -> str:
        """Generate content hash for deduplication."""
        content_for_hash = f"{self.title}{self.description or ''}{self.url}"
        return hashlib.sha256(content_for_hash.encode()).hexdigest()


@dataclass
class RateLimitStatus:
    """Rate limit status for a news provider."""
    requests_remaining: int
    requests_limit: int
    reset_time: Optional[datetime]
    is_limited: bool = False
    
    @property
    def usage_percentage(self) -> float:
        """Calculate usage percentage."""
        if self.requests_limit == 0:
            return 0.0
        return ((self.requests_limit - self.requests_remaining) / self.requests_limit) * 100


class NewsProviderError(Exception):
    """Base exception for news provider errors."""
    pass


class RateLimitExceededError(NewsProviderError):
    """Rate limit exceeded for news provider."""
    pass


class NewsProvider(ABC):
    """Abstract base class for news providers."""
    
    def __init__(self, api_key: str, name: str):
        self.api_key = api_key
        self.name = name
        self._rate_limit_status = RateLimitStatus(
            requests_remaining=1000,
            requests_limit=1000,
            reset_time=None
        )
    
    @abstractmethod
    def fetch_news_for_symbol(self, symbol: str, limit: int = 50) -> List[NewsArticle]:
        """
        Fetch news articles for a specific stock symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            limit: Maximum number of articles to fetch
            
        Returns:
            List of NewsArticle objects
            
        Raises:
            NewsProviderError: If fetching fails
            RateLimitExceededError: If rate limit is exceeded
        """
        pass
    
    @abstractmethod
    def get_rate_limit_status(self) -> RateLimitStatus:
        """Get current rate limit status."""
        pass
    
    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if the provider is healthy and available."""
        pass
    
    def _update_rate_limit_from_headers(self, headers: Dict[str, Any]) -> None:
        """Update rate limit status from API response headers."""
        # Default implementation - providers should override if they have specific headers
        pass
    
    def _get_company_name(self, symbol: str) -> str:
        """Get company name for symbol (basic implementation)."""
        # This could be enhanced with a symbol-to-company mapping
        company_names = {
            'AAPL': 'Apple Inc',
            'GOOGL': 'Alphabet Inc',
            'MSFT': 'Microsoft Corporation',
            'AMZN': 'Amazon.com Inc',
            'TSLA': 'Tesla Inc',
            'META': 'Meta Platforms Inc',
            'NVDA': 'NVIDIA Corporation',
            'NFLX': 'Netflix Inc'
        }
        return company_names.get(symbol.upper(), symbol)