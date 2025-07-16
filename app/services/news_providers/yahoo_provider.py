"""
Yahoo Finance news provider implementation
"""
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from .base import NewsProvider, NewsArticle, RateLimitStatus, NewsProviderError, RateLimitExceededError


class YahooFinanceProvider(NewsProvider):
    """Yahoo Finance news provider implementation"""
    
    def __init__(self, api_key: str = None):
        # Yahoo Finance doesn't require an API key for basic news access
        super().__init__(api_key or "", "Yahoo Finance")
        self.base_url = "https://query1.finance.yahoo.com/v1/finance/search"
        self.news_url = "https://query2.finance.yahoo.com/v1/finance/search"
        self.requests_per_minute = 100  # Conservative estimate
    
    def fetch_news_for_symbol(self, symbol: str, limit: int = 50) -> List[NewsArticle]:
        """
        Fetch news for a specific symbol using Yahoo Finance
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            limit: Maximum number of articles to fetch
            
        Returns:
            List of NewsArticle objects
        """
        try:
            # Yahoo Finance news endpoint
            url = f"https://query1.finance.yahoo.com/v1/finance/search"
            params = {
                'q': symbol.upper(),
                'lang': 'en-US',
                'region': 'US',
                'quotesCount': 1,
                'newsCount': min(limit, 50),  # Yahoo typically returns up to 50 news items
                'enableFuzzyQuery': False,
                'quotesQueryId': 'tss_match_phrase_query',
                'multiQuoteQueryId': 'multi_quote_single_token_query',
                'newsQueryId': 'news_cie_vespa',
                'enableCb': True,
                'enableNavLinks': True,
                'enableEnhancedTrivialQuery': True
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            # Update rate limit status
            self._update_rate_limit_from_response(response)
            
            if response.status_code == 429:
                raise RateLimitExceededError("Yahoo Finance rate limit exceeded")
            elif response.status_code != 200:
                raise NewsProviderError(f"Yahoo Finance API returned status {response.status_code}")
            
            data = response.json()
            
            # Extract news from response
            news_data = data.get('news', [])
            
            # Convert to NewsArticle objects
            articles = []
            for item in news_data:
                try:
                    article = self._parse_article(item, symbol)
                    if article:
                        articles.append(article)
                except Exception as e:
                    print(f"Error parsing Yahoo Finance article: {e}")
                    continue
            
            return articles
            
        except requests.RequestException as e:
            raise NewsProviderError(f"Yahoo Finance request failed: {e}")
        except Exception as e:
            raise NewsProviderError(f"Yahoo Finance error: {e}")
    
    def get_rate_limit_status(self) -> RateLimitStatus:
        """Get current rate limit status"""
        return self._rate_limit_status
    
    def is_healthy(self) -> bool:
        """Check if Yahoo Finance provider is healthy"""
        try:
            # Simple health check
            url = "https://query1.finance.yahoo.com/v1/finance/search"
            params = {
                'q': 'AAPL',
                'lang': 'en-US',
                'region': 'US',
                'quotesCount': 1,
                'newsCount': 1
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            return response.status_code in [200, 429]
            
        except Exception:
            return False
    
    def _update_rate_limit_from_response(self, response):
        """Update rate limit status from Yahoo Finance response"""
        # Yahoo Finance doesn't provide detailed rate limit headers
        # We'll estimate based on response status
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
        """Parse Yahoo Finance article data into NewsArticle object"""
        try:
            # Extract required fields
            title = item.get('title', '')
            summary = item.get('summary', '')
            link = item.get('link', '')
            
            if not title or not link:
                return None
            
            # Parse timestamp
            provider_publish_time = item.get('providerPublishTime')
            if provider_publish_time:
                # Yahoo uses Unix timestamp
                published_at = datetime.fromtimestamp(provider_publish_time, tz=timezone.utc)
            else:
                published_at = datetime.now(timezone.utc)
            
            # Extract source info
            publisher = item.get('publisher', 'Yahoo Finance')
            
            # Extract thumbnail
            thumbnail = None
            if 'thumbnail' in item and 'resolutions' in item['thumbnail']:
                resolutions = item['thumbnail']['resolutions']
                if resolutions:
                    thumbnail = resolutions[0].get('url')
            
            return NewsArticle(
                title=title,
                description=summary,
                content=None,  # Yahoo Finance doesn't provide full content in search
                url=link,
                url_to_image=thumbnail,
                source_name=publisher,
                source_id=item.get('uuid'),
                author=None,  # Yahoo Finance doesn't provide author in search results
                published_at=published_at,
                symbol=symbol.upper()
            )
            
        except Exception as e:
            print(f"Error parsing Yahoo Finance article: {e}")
            return None