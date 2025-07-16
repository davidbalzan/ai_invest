"""
Alpha Vantage news provider implementation
"""
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from .base import NewsProvider, NewsArticle, RateLimitStatus, NewsProviderError, RateLimitExceededError


class AlphaVantageProvider(NewsProvider):
    """Alpha Vantage news provider implementation"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "Alpha Vantage")
        self.base_url = "https://www.alphavantage.co/query"
        self.requests_per_minute = 5  # Free tier limit
        self.requests_per_day = 500   # Free tier daily limit
    
    def fetch_news_for_symbol(self, symbol: str, limit: int = 50) -> List[NewsArticle]:
        """
        Fetch news for a specific symbol using Alpha Vantage API
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            limit: Maximum number of articles to fetch
            
        Returns:
            List of NewsArticle objects
        """
        if not self.api_key:
            raise NewsProviderError("Alpha Vantage API key not provided")
        
        try:
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': symbol.upper(),
                'apikey': self.api_key,
                'limit': min(limit, 1000)  # Alpha Vantage max is 1000
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            
            # Update rate limit status
            self._update_rate_limit_from_response(response)
            
            if response.status_code == 429:
                raise RateLimitExceededError("Alpha Vantage rate limit exceeded")
            elif response.status_code != 200:
                raise NewsProviderError(f"Alpha Vantage API returned status {response.status_code}")
            
            data = response.json()
            
            # Check for API error messages
            if 'Error Message' in data:
                raise NewsProviderError(f"Alpha Vantage error: {data['Error Message']}")
            elif 'Note' in data:
                raise RateLimitExceededError(f"Alpha Vantage rate limit: {data['Note']}")
            
            # Extract articles from response
            articles_data = data.get('feed', [])
            
            # Convert to NewsArticle objects
            articles = []
            for item in articles_data:
                try:
                    article = self._parse_article(item, symbol)
                    if article:
                        articles.append(article)
                except Exception as e:
                    print(f"Error parsing Alpha Vantage article: {e}")
                    continue
            
            return articles
            
        except requests.RequestException as e:
            raise NewsProviderError(f"Alpha Vantage request failed: {e}")
        except Exception as e:
            raise NewsProviderError(f"Alpha Vantage error: {e}")
    
    def get_rate_limit_status(self) -> RateLimitStatus:
        """Get current rate limit status"""
        return self._rate_limit_status
    
    def is_healthy(self) -> bool:
        """Check if Alpha Vantage provider is healthy"""
        if not self.api_key:
            return False
        
        try:
            # Simple health check with a basic query
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': 'AAPL',
                'apikey': self.api_key,
                'limit': 1
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code != 200:
                return False
            
            data = response.json()
            
            # Check if we get a valid response (not an error)
            return 'Error Message' not in data and 'feed' in data
            
        except Exception:
            return False
    
    def _update_rate_limit_from_response(self, response):
        """Update rate limit status from Alpha Vantage response"""
        # Alpha Vantage doesn't provide detailed rate limit headers
        # We'll estimate based on known limits and response content
        data = response.json() if response.status_code == 200 else {}
        
        if 'Note' in data and 'call frequency' in data['Note'].lower():
            # Rate limited
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
        """Parse Alpha Vantage article data into NewsArticle object"""
        try:
            # Extract required fields
            title = item.get('title', '')
            summary = item.get('summary', '')
            url = item.get('url', '')
            
            if not title or not url:
                return None
            
            # Parse timestamp
            time_published = item.get('time_published')
            if time_published:
                # Alpha Vantage format: YYYYMMDDTHHMMSS
                try:
                    published_at = datetime.strptime(time_published, '%Y%m%dT%H%M%S')
                    published_at = published_at.replace(tzinfo=timezone.utc)
                except ValueError:
                    published_at = datetime.now(timezone.utc)
            else:
                published_at = datetime.now(timezone.utc)
            
            # Extract source info
            source_name = item.get('source', 'Alpha Vantage')
            
            # Extract author info
            authors = item.get('authors', [])
            author = authors[0] if authors else None
            
            return NewsArticle(
                title=title,
                description=summary,
                content=None,  # Alpha Vantage doesn't provide full content
                url=url,
                url_to_image=item.get('banner_image'),
                source_name=source_name,
                source_id=None,
                author=author,
                published_at=published_at,
                symbol=symbol.upper()
            )
            
        except Exception as e:
            print(f"Error parsing Alpha Vantage article: {e}")
            return None