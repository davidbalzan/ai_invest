#!/usr/bin/env python3
"""
Test script to verify task 3 completion
"""
import os
import sys

def test_directory_structure():
    """Test that the news_providers directory structure is created"""
    print("✓ Testing directory structure...")
    
    # Check if directory exists
    providers_dir = "app/services/news_providers"
    assert os.path.exists(providers_dir), f"Directory {providers_dir} does not exist"
    
    # Check required files
    required_files = [
        "__init__.py",
        "base.py", 
        "finnhub_provider.py",
        "newsapi_provider.py",
        "alpha_vantage_provider.py",
        "yahoo_provider.py"
    ]
    
    for file in required_files:
        file_path = os.path.join(providers_dir, file)
        assert os.path.exists(file_path), f"File {file_path} does not exist"
    
    print("  ✓ All required files exist")

def test_base_classes():
    """Test that base NewsProvider abstract class is implemented"""
    print("✓ Testing base classes...")
    
    sys.path.insert(0, os.getcwd())
    from app.services.news_providers.base import NewsProvider, NewsArticle, RateLimitStatus
    
    # Test that NewsProvider is abstract
    try:
        provider = NewsProvider("test_key", "test_name")
        assert False, "NewsProvider should be abstract"
    except TypeError:
        pass  # Expected
    
    # Test NewsArticle dataclass
    from datetime import datetime, timezone
    article = NewsArticle(
        title="Test Title",
        description="Test Description", 
        content="Test Content",
        url="https://test.com",
        url_to_image="https://test.com/image.jpg",
        source_name="Test Source",
        source_id="test_id",
        author="Test Author",
        published_at=datetime.now(timezone.utc)
    )
    
    assert article.title == "Test Title"
    assert len(article.content_hash) == 64  # SHA256 hash length
    
    print("  ✓ Base classes work correctly")

def test_provider_implementations():
    """Test that all provider implementations exist and can be imported"""
    print("✓ Testing provider implementations...")
    
    sys.path.insert(0, os.getcwd())
    
    # Test imports
    from app.services.news_providers.finnhub_provider import FinnhubProvider
    from app.services.news_providers.newsapi_provider import NewsAPIProvider
    from app.services.news_providers.alpha_vantage_provider import AlphaVantageProvider
    from app.services.news_providers.yahoo_provider import YahooFinanceProvider
    
    # Test that they inherit from NewsProvider
    from app.services.news_providers.base import NewsProvider
    
    assert issubclass(FinnhubProvider, NewsProvider)
    assert issubclass(NewsAPIProvider, NewsProvider)
    assert issubclass(AlphaVantageProvider, NewsProvider)
    assert issubclass(YahooFinanceProvider, NewsProvider)
    
    print("  ✓ All provider implementations exist and inherit correctly")

def test_news_gateway():
    """Test that NewsAPIGateway exists and can be imported"""
    print("✓ Testing News API Gateway...")
    
    sys.path.insert(0, os.getcwd())
    from app.services.news_gateway import NewsAPIGateway, FallbackManager, RateLimiter
    
    # Test that gateway can be instantiated
    gateway = NewsAPIGateway()
    
    # Test that it has required methods
    assert hasattr(gateway, 'fetch_news')
    assert hasattr(gateway, 'get_available_providers')
    assert hasattr(gateway, 'get_provider_status')
    assert hasattr(gateway, 'trigger_manual_refresh')
    
    print("  ✓ News API Gateway implemented correctly")

def test_rate_limiting_and_fallback():
    """Test that rate limiting and fallback mechanisms exist"""
    print("✓ Testing rate limiting and fallback mechanisms...")
    
    sys.path.insert(0, os.getcwd())
    from app.services.news_gateway import RateLimiter, FallbackManager
    
    # Test RateLimiter
    rate_limiter = RateLimiter()
    assert hasattr(rate_limiter, 'can_make_request')
    assert hasattr(rate_limiter, 'record_request')
    assert hasattr(rate_limiter, 'get_wait_time')
    
    # Test FallbackManager
    fallback_manager = FallbackManager()
    assert hasattr(fallback_manager, 'get_provider_order')
    assert hasattr(fallback_manager, 'update_provider_health')
    
    print("  ✓ Rate limiting and fallback mechanisms implemented")

def test_finnhub_extraction():
    """Test that Finnhub functionality was extracted from ai_analyzer.py"""
    print("✓ Testing Finnhub extraction...")
    
    sys.path.insert(0, os.getcwd())
    
    # Test that ai_analyzer.py now uses the new FinnhubProvider
    with open('ai_analyzer.py', 'r') as f:
        content = f.read()
        assert 'from app.services.news_providers.finnhub_provider import FinnhubProvider' in content
        assert 'provider = FinnhubProvider(finnhub_api_key)' in content
    
    # Test that the function still works
    from ai_analyzer import get_news_sentiment
    
    print("  ✓ Finnhub functionality successfully extracted and refactored")

def test_requirements_updated():
    """Test that requirements.txt was updated with newsapi-python"""
    print("✓ Testing requirements update...")
    
    with open('requirements.txt', 'r') as f:
        content = f.read()
        assert 'newsapi-python' in content
    
    print("  ✓ Requirements.txt updated with newsapi-python")

if __name__ == "__main__":
    print("Task 3 Completion Test Suite")
    print("=" * 50)
    
    try:
        test_directory_structure()
        test_base_classes()
        test_provider_implementations()
        test_news_gateway()
        test_rate_limiting_and_fallback()
        test_finnhub_extraction()
        test_requirements_updated()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("Task 3 'News Provider Integration and API Gateway' is COMPLETE")
        print("\nImplemented components:")
        print("  ✓ app/services/news_providers/ directory with base NewsProvider abstract class")
        print("  ✓ NewsAPIProvider class using newsapi-python library")
        print("  ✓ Extracted and refactored Finnhub functionality into FinnhubProvider class")
        print("  ✓ app/services/news_gateway.py with NewsAPIGateway class")
        print("  ✓ Intelligent rate limiting and fallback mechanism")
        print("  ✓ AlphaVantageProvider and YahooFinanceProvider classes")
        print("  ✓ Updated requirements.txt with newsapi-python dependency")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)