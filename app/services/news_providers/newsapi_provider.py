"""
NewsAPI.org provider implementation
"""
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from .base import NewsProvider, NewsArticle, RateLimitStatus, NewsProviderError, RateLimitExceededError

try:
    from newsapi import NewsApiClient
    NEWSAPI_AVAILABLE = True
except ImportError:
    NEWSAPI_AVAILABLE = False


class NewsAPIProvider(NewsProvider):
    """NewsAPI.org provider implementation"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "NewsAPI")
        self.base_url = "https://newsapi.org/v2"
        self.requests_per_day = 1000  # Free tier limit
        self.requests_per_hour = 100  # Estimated reasonable limit
    
    def fetch_news_for_symbol(self, symbol: str, limit: int = 50) -> List[NewsArticle]:
        """
        Fetch news for a specific symbol using NewsAPI
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            limit: Maximum number of articles to fetch (max 100 for NewsAPI)
            
        Returns:
            List of NewsArticle objects
        """
        if not self.api_key:
            raise NewsProviderError("NewsAPI key not provided")
        
        try:
            # Get company name for better search results
            company_name = self._get_company_name(symbol)
            
            # Search query combining symbol and company name
            query = f'"{symbol}" OR "{company_name}"'
            
            url = f"{self.base_url}/everything"
            params = {
                'q': query,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': min(limit, 100),  # NewsAPI max is 100
                'apiKey': self.api_key
            }
            
            # Add date range for recent news (last 30 days)
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            params['from'] = from_date
            
            response = requests.get(url, params=params, timeout=10)
            
            # Update rate limit status
            self._update_rate_limit_from_response(response)
            
            if response.status_code == 429:
                raise RateLimitExceededError("NewsAPI rate limit exceeded")
            elif response.status_code == 401:
                raise NewsProviderError("NewsAPI authentication failed - check API key")
            elif response.status_code != 200:
                raise NewsProviderError(f"NewsAPI returned status {response.status_code}")
            
            data = response.json()
            
            if data.get('status') != 'ok':
                raise NewsProviderError(f"NewsAPI error: {data.get('message', 'Unknown error')}")
            
            articles_data = data.get('articles', [])
            
            # Convert to NewsArticle objects
            articles = []
            for item in articles_data:
                try:
                    article = self._parse_article(item, symbol)
                    if article:
                        articles.append(article)
                except Exception as e:
                    print(f"Error parsing NewsAPI article: {e}")
                    continue
            
            return articles
            
        except requests.RequestException as e:
            raise NewsProviderError(f"NewsAPI request failed: {e}")
        except Exception as e:
            raise NewsProviderError(f"NewsAPI error: {e}")
    
    def get_rate_limit_status(self) -> RateLimitStatus:
        """Get current rate limit status"""
        return self._rate_limit_status
    
    def is_healthy(self) -> bool:
        """Check if NewsAPI provider is healthy"""
        if not self.api_key:
            return False
        
        try:
            # Simple health check
            url = f"{self.base_url}/top-headlines"
            params = {
                'country': 'us',
                'category': 'business',
                'pageSize': 1,
                'apiKey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=5)
            return response.status_code in [200, 429]
            
        except Exception:
            return False
    
    def _update_rate_limit_from_response(self, response):
        """Update rate limit status from NewsAPI response headers"""
        headers = response.headers
        
        # NewsAPI provides rate limit info in headers
        requests_remaining = int(headers.get('X-RateLimit-Remaining', 0))
        requests_limit = int(headers.get('X-RateLimit-Limit', self.requests_per_hour))
        
        # Calculate reset time (NewsAPI resets hourly)
        reset_time = datetime.now(timezone.utc) + timedelta(hours=1)
        
        self._rate_limit_status = RateLimitStatus(
            requests_remaining=requests_remaining,
            requests_limit=requests_limit,
            reset_time=reset_time,
            is_limited=requests_remaining <= 0
        )
    
    def _parse_article(self, item: dict, symbol: str) -> Optional[NewsArticle]:
        """Parse NewsAPI article data into NewsArticle object"""
        try:
            # Extract required fields
            title = item.get('title', '')
            description = item.get('description', '')
            url = item.get('url', '')
            
            if not title or not url or title == '[Removed]':
                return None
            
            # Parse timestamp
            published_at_str = item.get('publishedAt')
            if published_at_str:
                # NewsAPI uses ISO format: 2024-01-15T10:30:00Z
                published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
            else:
                published_at = datetime.now(timezone.utc)
            
            # Extract source info
            source = item.get('source', {})
            source_name = source.get('name', 'NewsAPI')
            source_id = source.get('id')
            
            return NewsArticle(
                title=title,
                description=description,
                content=item.get('content'),  # NewsAPI provides partial content
                url=url,
                url_to_image=item.get('urlToImage'),
                source_name=source_name,
                source_id=source_id,
                author=item.get('author'),
                published_at=published_at,
                symbol=symbol.upper()
            )
            
        except Exception as e:
            print(f"Error parsing NewsAPI article: {e}")
            return None