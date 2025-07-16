"""
NewsAPI.org provider implementation.
"""

import requests
import time
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from newsapi import NewsApiClient
from .base import NewsProvider, NewsArticle, RateLimitStatus, NewsProviderError, RateLimitExceededError


class NewsAPIProvider(NewsProvider):
    """NewsAPI.org news provider implementation."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "NewsAPI")
        self.base_url = "https://newsapi.org/v2"
        self.requests_per_day = 1000  # Free tier limit
        self.last_request_time = None
        
    def fetch_news_for_symbol(self, symbol: str, limit: int = 50) -> List[NewsArticle]:
        """Fetch news using NewsAPI.org everything endpoint."""
        try:
            # Respect rate limits (1 request per second for free tier)
            self._respect_rate_limit()
            
            # Get company name for better search results
            company_name = self._get_company_name(symbol)
            
            # Use dynamic date range for recent news
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            params = {
                'q': f'"{symbol}" OR "{company_name}"',
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': min(limit, 100),  # API max is 100
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'apiKey': self.api_key
            }
            
            response = requests.get(
                f"{self.base_url}/everything",
                params=params,
                timeout=10
            )
            
            # Update rate limit status from headers
            self._update_rate_limit_from_headers(response.headers)
            
            if response.status_code == 429:
                raise RateLimitExceededError("NewsAPI rate limit exceeded")
            elif response.status_code != 200:
                raise NewsProviderError(f"NewsAPI returned status {response.status_code}: {response.text}")
            
            data = response.json()
            
            if data.get('status') != 'ok':
                raise NewsProviderError(f"NewsAPI error: {data.get('message', 'Unknown error')}")
            
            articles = []
            for article_data in data.get('articles', []):
                try:
                    article = self._parse_article(article_data, symbol)
                    if article:
                        articles.append(article)
                except Exception as e:
                    print(f"Error parsing NewsAPI article: {e}")
                    continue
            
            return articles
            
        except RateLimitExceededError:
            raise
        except Exception as e:
            raise NewsProviderError(f"NewsAPI fetch error: {e}")
    
    def get_rate_limit_status(self) -> RateLimitStatus:
        """Get current rate limit status."""
        return self._rate_limit_status
    
    def is_healthy(self) -> bool:
        """Check if NewsAPI is healthy."""
        try:
            # Simple health check with minimal request
            params = {
                'q': 'test',
                'pageSize': 1,
                'apiKey': self.api_key
            }
            
            response = requests.get(
                f"{self.base_url}/everything",
                params=params,
                timeout=5
            )
            
            return response.status_code == 200
        except:
            return False
    
    def _respect_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        if self.last_request_time:
            time_since_last = time.time() - self.last_request_time
            if time_since_last < 1.0:  # 1 second minimum between requests
                time.sleep(1.0 - time_since_last)
        
        self.last_request_time = time.time()
    
    def _update_rate_limit_from_headers(self, headers):
        """Update rate limit status from API response headers."""
        try:
            # NewsAPI doesn't provide detailed rate limit headers in free tier
            # We'll track based on known limits
            remaining = headers.get('X-RateLimit-Remaining')
            if remaining:
                self._rate_limit_status.requests_remaining = int(remaining)
                self._rate_limit_status.is_limited = int(remaining) <= 10
        except:
            pass
    
    def _parse_article(self, article_data: dict, symbol: str) -> Optional[NewsArticle]:
        """Parse NewsAPI article data into NewsArticle object."""
        try:
            # Skip articles with missing essential data
            if not article_data.get('title') or not article_data.get('url'):
                return None
            
            # Parse published date
            published_str = article_data.get('publishedAt')
            if published_str:
                # NewsAPI uses ISO format: 2023-12-01T10:30:00Z
                published_at = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
            else:
                published_at = datetime.now(timezone.utc)
            
            # Extract source information
            source = article_data.get('source', {})
            source_name = source.get('name', 'Unknown')
            source_id = source.get('id')
            
            return NewsArticle(
                title=article_data['title'],
                description=article_data.get('description'),
                content=article_data.get('content'),
                url=article_data['url'],
                url_to_image=article_data.get('urlToImage'),
                source_name=source_name,
                source_id=source_id,
                author=article_data.get('author'),
                published_at=published_at,
                symbol=symbol
            )
            
        except Exception as e:
            print(f"Error parsing NewsAPI article: {e}")
            return None