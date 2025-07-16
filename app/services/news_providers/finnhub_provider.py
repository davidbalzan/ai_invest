"""
Finnhub news provider implementation
"""
import requests
import time
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from .base import NewsProvider, NewsArticle, RateLimitStatus, NewsProviderError, RateLimitExceededError


class FinnhubProvider(NewsProvider):
    """Finnhub news provider implementation"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "Finnhub")
        self.base_url = "https://finnhub.io/api/v1"
        self.requests_per_minute = 60  # Free tier limit
        self.last_request_time = None
    
    def fetch_news_for_symbol(self, symbol: str, limit: int = 50) -> List[NewsArticle]:
        """
        Fetch news for a specific symbol using Finnhub API
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            limit: Maximum number of articles to fetch (max 100 for Finnhub)
            
        Returns:
            List of NewsArticle objects
        """
        if not self.api_key:
            raise NewsProviderError("Finnhub API key not provided")
        
        # Respect rate limits (60 calls/minute = 1 per second)
        self._enforce_rate_limit()
        
        try:
            # Use dynamic date range to get recent news
            current_date = datetime.now()
            start_date = (current_date - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = current_date.strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/company-news"
            params = {
                'symbol': symbol.upper(),
                'from': start_date,
                'to': end_date,
                'token': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            # Update rate limit status
            self._update_rate_limit_from_response(response)
            
            if response.status_code == 429:
                raise RateLimitExceededError("Finnhub rate limit exceeded")
            elif response.status_code != 200:
                raise NewsProviderError(f"Finnhub API returned status {response.status_code}")
            
            news_data = response.json()
            
            if not news_data:
                return []
            
            # Convert to NewsArticle objects
            articles = []
            for item in news_data[:limit]:
                try:
                    article = self._parse_article(item, symbol)
                    if article:
                        articles.append(article)
                except Exception as e:
                    print(f"Error parsing Finnhub article: {e}")
                    continue
            
            return articles
            
        except requests.RequestException as e:
            raise NewsProviderError(f"Finnhub request failed: {e}")
        except Exception as e:
            raise NewsProviderError(f"Finnhub error: {e}")
    
    def get_rate_limit_status(self) -> RateLimitStatus:
        """Get current rate limit status"""
        return self._rate_limit_status
    
    def is_healthy(self) -> bool:
        """Check if Finnhub provider is healthy"""
        if not self.api_key:
            return False
        
        try:
            # Simple health check - get news for a common symbol
            url = f"{self.base_url}/company-news"
            params = {
                'symbol': 'AAPL',
                'from': '2024-01-01',
                'to': '2024-01-02',
                'token': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=5)
            return response.status_code in [200, 429]  # 429 means we're rate limited but API is working
            
        except Exception:
            return False
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting (1 request per second for free tier)"""
        if self.last_request_time:
            time_since_last = time.time() - self.last_request_time
            if time_since_last < 1.0:  # Less than 1 second
                time.sleep(1.0 - time_since_last)
        
        self.last_request_time = time.time()
    
    def _update_rate_limit_from_response(self, response):
        """Update rate limit status from Finnhub response headers"""
        # Finnhub doesn't provide detailed rate limit headers in free tier
        # We'll estimate based on known limits
        if response.status_code == 429:
            self._rate_limit_status = RateLimitStatus(
                requests_remaining=0,
                requests_limit=self.requests_per_minute,
                reset_time=datetime.now(timezone.utc) + timedelta(minutes=1),
                is_limited=True
            )
        else:
            # Assume we have some requests remaining
            self._rate_limit_status = RateLimitStatus(
                requests_remaining=self.requests_per_minute - 1,
                requests_limit=self.requests_per_minute,
                reset_time=datetime.now(timezone.utc) + timedelta(minutes=1),
                is_limited=False
            )
    
    def _parse_article(self, item: dict, symbol: str) -> Optional[NewsArticle]:
        """Parse Finnhub article data into NewsArticle object"""
        try:
            # Extract required fields
            headline = item.get('headline', '')
            summary = item.get('summary', '')
            url = item.get('url', '')
            
            if not headline or not url:
                return None
            
            # Parse timestamp
            published_timestamp = item.get('datetime')
            if published_timestamp:
                published_at = datetime.fromtimestamp(published_timestamp, tz=timezone.utc)
            else:
                published_at = datetime.now(timezone.utc)
            
            return NewsArticle(
                title=headline,
                description=summary,
                content=None,  # Finnhub doesn't provide full content
                url=url,
                url_to_image=item.get('image'),
                source_name=item.get('source', 'Finnhub'),
                source_id=item.get('id'),
                author=None,  # Finnhub doesn't provide author info
                published_at=published_at,
                symbol=symbol.upper()
            )
            
        except Exception as e:
            print(f"Error parsing Finnhub article: {e}")
            return None