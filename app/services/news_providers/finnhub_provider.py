"""
Finnhub provider implementation - extracted and refactored from ai_analyzer.py.
"""

import requests
import time
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from .base import NewsProvider, NewsArticle, RateLimitStatus, NewsProviderError, RateLimitExceededError


class FinnhubProvider(NewsProvider):
    """Finnhub news provider implementation."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "Finnhub")
        self.base_url = "https://finnhub.io/api/v1"
        self.requests_per_minute = 60  # Free tier limit
        self.last_request_time = None
        
    def fetch_news_for_symbol(self, symbol: str, limit: int = 50) -> List[NewsArticle]:
        """Fetch news using Finnhub company news endpoint."""
        try:
            # Respect rate limits (60 calls/minute = 1 per second)
            self._respect_rate_limit()
            
            # Use dynamic date range to get recent news
            current_date = datetime.now()
            start_date = current_date - timedelta(days=30)  # Last 30 days
            end_date = current_date
            
            params = {
                'symbol': symbol.upper(),
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'token': self.api_key
            }
            
            response = requests.get(
                f"{self.base_url}/company-news",
                params=params,
                timeout=10
            )
            
            if response.status_code == 429:
                raise RateLimitExceededError("Finnhub rate limit exceeded")
            elif response.status_code != 200:
                raise NewsProviderError(f"Finnhub returned status {response.status_code}")
            
            news_data = response.json()
            
            if not news_data or len(news_data) == 0:
                return []
            
            articles = []
            # Limit to requested number of articles
            for article_data in news_data[:limit]:
                try:
                    article = self._parse_article(article_data, symbol)
                    if article:
                        articles.append(article)
                except Exception as e:
                    print(f"Error parsing Finnhub article: {e}")
                    continue
            
            return articles
            
        except RateLimitExceededError:
            raise
        except Exception as e:
            raise NewsProviderError(f"Finnhub fetch error: {e}")
    
    def get_rate_limit_status(self) -> RateLimitStatus:
        """Get current rate limit status."""
        return self._rate_limit_status
    
    def is_healthy(self) -> bool:
        """Check if Finnhub is healthy."""
        try:
            # Simple health check with quote endpoint
            params = {'symbol': 'AAPL', 'token': self.api_key}
            response = requests.get(
                f"{self.base_url}/quote",
                params=params,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def _respect_rate_limit(self):
        """Ensure we don't exceed rate limits (60 calls/minute)."""
        if self.last_request_time:
            time_since_last = time.time() - self.last_request_time
            if time_since_last < 1.0:  # 1 second minimum between requests
                time.sleep(1.0 - time_since_last)
        
        self.last_request_time = time.time()
    
    def _parse_article(self, article_data: dict, symbol: str) -> Optional[NewsArticle]:
        """Parse Finnhub article data into NewsArticle object."""
        try:
            # Skip articles with missing essential data
            headline = article_data.get('headline', '')
            url = article_data.get('url', '')
            
            if not headline or not url:
                return None
            
            # Parse published date from timestamp
            datetime_timestamp = article_data.get('datetime')
            if datetime_timestamp:
                published_at = datetime.fromtimestamp(datetime_timestamp, tz=timezone.utc)
            else:
                published_at = datetime.now(timezone.utc)
            
            return NewsArticle(
                title=headline,
                description=article_data.get('summary'),
                content=None,  # Finnhub doesn't provide full content
                url=url,
                url_to_image=article_data.get('image'),
                source_name=article_data.get('source', 'Finnhub'),
                source_id=None,
                author=None,  # Finnhub doesn't provide author info
                published_at=published_at,
                symbol=symbol
            )
            
        except Exception as e:
            print(f"Error parsing Finnhub article: {e}")
            return None