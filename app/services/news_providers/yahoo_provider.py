"""
Yahoo Finance provider implementation.
"""

import requests
import time
from datetime import datetime, timezone
from typing import List, Optional
from .base import NewsProvider, NewsArticle, RateLimitStatus, NewsProviderError, RateLimitExceededError


class YahooFinanceProvider(NewsProvider):
    """Yahoo Finance news provider implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        # Yahoo Finance doesn't require API key for basic access
        super().__init__(api_key or "", "Yahoo Finance")
        self.base_url = "https://query1.finance.yahoo.com/v1/finance"
        self.requests_per_minute = 100  # Conservative limit
        self.last_request_time = None
        
    def fetch_news_for_symbol(self, symbol: str, limit: int = 50) -> List[NewsArticle]:
        """Fetch news using Yahoo Finance search endpoint."""
        try:
            # Respect rate limits
            self._respect_rate_limit()
            
            # Yahoo Finance news endpoint
            params = {
                'q': symbol.upper(),
                'count': min(limit, 100),  # Reasonable limit
                'start': 0
            }
            
            # Use the search endpoint for news
            response = requests.get(
                f"{self.base_url}/search",
                params=params,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                timeout=10
            )
            
            if response.status_code == 429:
                raise RateLimitExceededError("Yahoo Finance rate limit exceeded")
            elif response.status_code != 200:
                raise NewsProviderError(f"Yahoo Finance returned status {response.status_code}")
            
            data = response.json()
            
            # Yahoo Finance has a different structure - try news section
            news_items = []
            
            # Try different possible structures
            if 'news' in data:
                news_items = data['news']
            elif 'items' in data:
                news_items = [item for item in data['items'] if item.get('type') == 'news']
            
            if not news_items:
                # Fallback: try alternative Yahoo Finance RSS approach
                return self._fetch_from_rss(symbol, limit)
            
            articles = []
            for article_data in news_items:
                try:
                    article = self._parse_article(article_data, symbol)
                    if article:
                        articles.append(article)
                except Exception as e:
                    print(f"Error parsing Yahoo Finance article: {e}")
                    continue
            
            return articles
            
        except RateLimitExceededError:
            raise
        except Exception as e:
            # Fallback to RSS if API fails
            try:
                return self._fetch_from_rss(symbol, limit)
            except:
                raise NewsProviderError(f"Yahoo Finance fetch error: {e}")
    
    def _fetch_from_rss(self, symbol: str, limit: int) -> List[NewsArticle]:
        """Fallback method using Yahoo Finance RSS feeds."""
        try:
            import feedparser
            
            # Yahoo Finance RSS URL for symbol
            rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol.upper()}&region=US&lang=en-US"
            
            response = requests.get(rss_url, timeout=10)
            if response.status_code != 200:
                return []
            
            feed = feedparser.parse(response.content)
            articles = []
            
            for entry in feed.entries[:limit]:
                try:
                    # Parse published date
                    published_at = datetime.now(timezone.utc)
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    
                    article = NewsArticle(
                        title=entry.title,
                        description=getattr(entry, 'summary', ''),
                        content=None,
                        url=entry.link,
                        url_to_image=None,
                        source_name='Yahoo Finance',
                        source_id=None,
                        author=None,
                        published_at=published_at,
                        symbol=symbol
                    )
                    articles.append(article)
                    
                except Exception as e:
                    print(f"Error parsing RSS entry: {e}")
                    continue
            
            return articles
            
        except ImportError:
            print("feedparser not available for Yahoo Finance RSS fallback")
            return []
        except Exception as e:
            print(f"RSS fallback error: {e}")
            return []
    
    def get_rate_limit_status(self) -> RateLimitStatus:
        """Get current rate limit status."""
        return self._rate_limit_status
    
    def is_healthy(self) -> bool:
        """Check if Yahoo Finance is healthy."""
        try:
            # Simple health check with quote endpoint
            response = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/AAPL",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def _respect_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        if self.last_request_time:
            time_since_last = time.time() - self.last_request_time
            min_interval = 0.6  # ~100 requests per minute
            if time_since_last < min_interval:
                time.sleep(min_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def _parse_article(self, article_data: dict, symbol: str) -> Optional[NewsArticle]:
        """Parse Yahoo Finance article data into NewsArticle object."""
        try:
            # Skip articles with missing essential data
            title = article_data.get('title', '')
            url = article_data.get('link', '')
            
            if not title or not url:
                return None
            
            # Parse published date
            published_at = datetime.now(timezone.utc)
            if 'pubDate' in article_data:
                try:
                    # Try parsing various date formats
                    pub_date = article_data['pubDate']
                    if isinstance(pub_date, (int, float)):
                        published_at = datetime.fromtimestamp(pub_date, tz=timezone.utc)
                    elif isinstance(pub_date, str):
                        # Try ISO format first
                        try:
                            published_at = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                        except:
                            # Fallback to current time
                            pass
                except:
                    pass
            
            return NewsArticle(
                title=title,
                description=article_data.get('summary', ''),
                content=None,
                url=url,
                url_to_image=article_data.get('thumbnail'),
                source_name='Yahoo Finance',
                source_id=None,
                author=article_data.get('author'),
                published_at=published_at,
                symbol=symbol
            )
            
        except Exception as e:
            print(f"Error parsing Yahoo Finance article: {e}")
            return None