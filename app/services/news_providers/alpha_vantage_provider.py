"""
Alpha Vantage provider implementation.
"""

import requests
import time
from datetime import datetime, timezone
from typing import List, Optional
from .base import NewsProvider, NewsArticle, RateLimitStatus, NewsProviderError, RateLimitExceededError


class AlphaVantageProvider(NewsProvider):
    """Alpha Vantage news provider implementation."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "Alpha Vantage")
        self.base_url = "https://www.alphavantage.co/query"
        self.requests_per_minute = 5  # Free tier limit
        self.last_request_time = None
        
    def fetch_news_for_symbol(self, symbol: str, limit: int = 50) -> List[NewsArticle]:
        """Fetch news using Alpha Vantage NEWS_SENTIMENT function."""
        try:
            # Respect rate limits (5 calls/minute)
            self._respect_rate_limit()
            
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': symbol.upper(),
                'limit': min(limit, 1000),  # API max is 1000
                'apikey': self.api_key
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=15  # Alpha Vantage can be slow
            )
            
            if response.status_code == 429:
                raise RateLimitExceededError("Alpha Vantage rate limit exceeded")
            elif response.status_code != 200:
                raise NewsProviderError(f"Alpha Vantage returned status {response.status_code}")
            
            data = response.json()
            
            # Check for API error messages
            if 'Error Message' in data:
                raise NewsProviderError(f"Alpha Vantage error: {data['Error Message']}")
            
            if 'Note' in data:
                raise RateLimitExceededError(f"Alpha Vantage rate limit: {data['Note']}")
            
            # Parse the feed
            feed = data.get('feed', [])
            if not feed:
                return []
            
            articles = []
            for article_data in feed:
                try:
                    article = self._parse_article(article_data, symbol)
                    if article:
                        articles.append(article)
                except Exception as e:
                    print(f"Error parsing Alpha Vantage article: {e}")
                    continue
            
            return articles
            
        except RateLimitExceededError:
            raise
        except Exception as e:
            raise NewsProviderError(f"Alpha Vantage fetch error: {e}")
    
    def get_rate_limit_status(self) -> RateLimitStatus:
        """Get current rate limit status."""
        return self._rate_limit_status
    
    def is_healthy(self) -> bool:
        """Check if Alpha Vantage is healthy."""
        try:
            # Simple health check with global quote
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'AAPL',
                'apikey': self.api_key
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=10
            )
            
            return response.status_code == 200 and 'Error Message' not in response.json()
        except:
            return False
    
    def _respect_rate_limit(self):
        """Ensure we don't exceed rate limits (5 calls/minute)."""
        if self.last_request_time:
            time_since_last = time.time() - self.last_request_time
            min_interval = 12.0  # 60 seconds / 5 calls = 12 seconds between calls
            if time_since_last < min_interval:
                time.sleep(min_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def _parse_article(self, article_data: dict, symbol: str) -> Optional[NewsArticle]:
        """Parse Alpha Vantage article data into NewsArticle object."""
        try:
            # Skip articles with missing essential data
            title = article_data.get('title', '')
            url = article_data.get('url', '')
            
            if not title or not url:
                return None
            
            # Parse published date
            time_published = article_data.get('time_published')
            if time_published:
                # Alpha Vantage format: YYYYMMDDTHHMMSS
                try:
                    published_at = datetime.strptime(time_published, '%Y%m%dT%H%M%S')
                    published_at = published_at.replace(tzinfo=timezone.utc)
                except ValueError:
                    published_at = datetime.now(timezone.utc)
            else:
                published_at = datetime.now(timezone.utc)
            
            # Extract source information
            source_name = article_data.get('source', 'Alpha Vantage')
            
            return NewsArticle(
                title=title,
                description=article_data.get('summary'),
                content=None,  # Alpha Vantage doesn't provide full content
                url=url,
                url_to_image=article_data.get('banner_image'),
                source_name=source_name,
                source_id=None,
                author=article_data.get('authors', [{}])[0].get('name') if article_data.get('authors') else None,
                published_at=published_at,
                symbol=symbol
            )
            
        except Exception as e:
            print(f"Error parsing Alpha Vantage article: {e}")
            return None