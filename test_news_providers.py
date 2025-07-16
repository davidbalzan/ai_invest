#!/usr/bin/env python3
"""
Test script for news providers implementation
"""
import os
import sys
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.news_gateway import NewsAPIGateway
from services.news_providers import FinnhubProvider, NewsAPIProvider, AlphaVantageProvider, YahooFinanceProvider

def test_individual_providers():
    """Test individual providers"""
    load_dotenv()
    
    print("Testing individual news providers...")
    
    # Test Finnhub
    finnhub_key = os.getenv('FINNHUB_API_KEY')
    if finnhub_key:
        print("\n--- Testing Finnhub Provider ---")
        try:
            provider = FinnhubProvider(finnhub_key)
            print(f"Health check: {provider.is_healthy()}")
            articles = provider.fetch_news_for_symbol('AAPL', limit=5)
            print(f"Fetched {len(articles)} articles from Finnhub")
            if articles:
                print(f"Sample article: {articles[0].title}")
        except Exception as e:
            print(f"Finnhub error: {e}")
    else:
        print("Finnhub API key not found")
    
    # Test NewsAPI
    newsapi_key = os.getenv('NEWSAPI_KEY')
    if newsapi_key:
        print("\n--- Testing NewsAPI Provider ---")
        try:
            provider = NewsAPIProvider(newsapi_key)
            print(f"Health check: {provider.is_healthy()}")
            articles = provider.fetch_news_for_symbol('AAPL', limit=5)
            print(f"Fetched {len(articles)} articles from NewsAPI")
            if articles:
                print(f"Sample article: {articles[0].title}")
        except Exception as e:
            print(f"NewsAPI error: {e}")
    else:
        print("NewsAPI key not found")
    
    # Test Alpha Vantage
    alpha_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if alpha_key:
        print("\n--- Testing Alpha Vantage Provider ---")
        try:
            provider = AlphaVantageProvider(alpha_key)
            print(f"Health check: {provider.is_healthy()}")
            articles = provider.fetch_news_for_symbol('AAPL', limit=5)
            print(f"Fetched {len(articles)} articles from Alpha Vantage")
            if articles:
                print(f"Sample article: {articles[0].title}")
        except Exception as e:
            print(f"Alpha Vantage error: {e}")
    else:
        print("Alpha Vantage API key not found")
    
    # Test Yahoo Finance
    print("\n--- Testing Yahoo Finance Provider ---")
    try:
        provider = YahooFinanceProvider()
        print(f"Health check: {provider.is_healthy()}")
        articles = provider.fetch_news_for_symbol('AAPL', limit=5)
        print(f"Fetched {len(articles)} articles from Yahoo Finance")
        if articles:
            print(f"Sample article: {articles[0].title}")
    except Exception as e:
        print(f"Yahoo Finance error: {e}")

def test_news_gateway():
    """Test the news gateway with fallback"""
    load_dotenv()
    
    print("\n\n=== Testing News Gateway ===")
    
    try:
        gateway = NewsAPIGateway()
        
        print(f"Available providers: {gateway.get_available_providers()}")
        print(f"Provider status: {gateway.get_provider_status()}")
        
        # Test fetching news for multiple symbols
        symbols = ['AAPL', 'GOOGL']
        print(f"\nFetching news for symbols: {symbols}")
        
        articles = gateway.fetch_news(symbols, limit=3)
        print(f"Total articles fetched: {len(articles)}")
        
        # Group articles by symbol
        by_symbol = {}
        for article in articles:
            symbol = article.symbol
            if symbol not in by_symbol:
                by_symbol[symbol] = []
            by_symbol[symbol].append(article)
        
        for symbol, symbol_articles in by_symbol.items():
            print(f"\n{symbol}: {len(symbol_articles)} articles")
            for article in symbol_articles[:2]:  # Show first 2
                print(f"  - {article.title[:80]}...")
                print(f"    Source: {article.source_name}, Published: {article.published_at}")
        
        # Test manual refresh
        print(f"\n--- Testing Manual Refresh ---")
        refresh_results = gateway.trigger_manual_refresh(['MSFT'], force_provider=None)
        for symbol, symbol_articles in refresh_results.items():
            print(f"Manual refresh for {symbol}: {len(symbol_articles)} articles")
        
    except Exception as e:
        print(f"Gateway error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("News Providers Test Suite")
    print("=" * 50)
    
    test_individual_providers()
    test_news_gateway()
    
    print("\nTest completed!")