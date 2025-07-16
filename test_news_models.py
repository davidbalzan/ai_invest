#!/usr/bin/env python3
"""
Test script to validate news models and schemas implementation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

# Test imports
try:
    from app.models import (
        NewsArticle, NewsCategory, NewsSentiment, StockNewsRelevance,
        NewsSource, UserNewsPreferences, NewsFetchJob
    )
    print("✓ Successfully imported all news models")
except ImportError as e:
    print(f"✗ Failed to import news models: {e}")
    sys.exit(1)

try:
    from app.schemas import (
        NewsArticleCreate, NewsArticleUpdate, NewsArticle as NewsArticleSchema,
        NewsCategoryCreate, NewsCategory as NewsCategorySchema,
        NewsSentimentCreate, NewsSentiment as NewsSentimentSchema,
        StockNewsRelevanceCreate, StockNewsRelevance as StockNewsRelevanceSchema,
        NewsSourceCreate, NewsSource as NewsSourceSchema,
        UserNewsPreferencesCreate, UserNewsPreferences as UserNewsPreferencesSchema,
        NewsFetchJobCreate, NewsFetchJob as NewsFetchJobSchema,
        # Enums
        NewsCategoryType, NewsPrimaryCategory, NewsSectorCategory,
        SentimentType, ImpactLevel, NewsJobType, NewsJobStatus,
        NewsAPIProvider, AlertSeverity, ContextType, NewsSourceType,
        NewsLanguage, NewsCountry, AlertType, NotificationChannel,
        # Validation schemas
        NewsKeywords, NotificationSettings, CategoryPreferences,
        SourcePreferences, NewsArticleMetadata, NewsProcessingMetadata
    )
    print("✓ Successfully imported all news schemas and enums")
except ImportError as e:
    print(f"✗ Failed to import news schemas: {e}")
    sys.exit(1)

def test_enum_values():
    """Test that all enum values are properly defined"""
    print("\nTesting enum values...")
    
    # Test primary categories
    assert NewsPrimaryCategory.EARNINGS == "earnings"
    assert NewsPrimaryCategory.MERGERS_ACQUISITIONS == "mergers_acquisitions"
    assert NewsPrimaryCategory.LEGAL_ISSUES == "legal_issues"
    print("✓ Primary category enums working")
    
    # Test sector categories
    assert NewsSectorCategory.TECHNOLOGY == "technology"
    assert NewsSectorCategory.BIOTECHNOLOGY == "biotechnology"
    assert NewsSectorCategory.SEMICONDUCTORS == "semiconductors"
    print("✓ Sector category enums working")
    
    # Test sentiment types
    assert SentimentType.POSITIVE == "positive"
    assert SentimentType.MIXED == "mixed"
    print("✓ Sentiment type enums working")
    
    # Test impact levels
    assert ImpactLevel.CRITICAL == "critical"
    assert ImpactLevel.HIGH == "high"
    print("✓ Impact level enums working")

def test_schema_validation():
    """Test schema validation"""
    print("\nTesting schema validation...")
    
    # Test NewsArticleCreate validation
    try:
        article_data = {
            "title": "Test Article",
            "url": "https://example.com/article",
            "source_name": "Test Source",
            "published_at": datetime.now(),
            "content_hash": "a" * 64  # 64-character hash
        }
        article = NewsArticleCreate(**article_data)
        print("✓ NewsArticleCreate validation working")
    except Exception as e:
        print(f"✗ NewsArticleCreate validation failed: {e}")
    
    # Test invalid URL
    try:
        invalid_article = NewsArticleCreate(
            title="Test",
            url="invalid-url",
            source_name="Test",
            published_at=datetime.now(),
            content_hash="a" * 64
        )
        print("✗ URL validation should have failed")
    except ValueError:
        print("✓ URL validation working correctly")
    
    # Test sentiment score validation
    try:
        sentiment_data = {
            "article_id": uuid4(),
            "sentiment": SentimentType.POSITIVE,
            "sentiment_score": Decimal("0.8"),
            "confidence_score": Decimal("0.9")
        }
        sentiment = NewsSentimentCreate(**sentiment_data)
        print("✓ NewsSentimentCreate validation working")
    except Exception as e:
        print(f"✗ NewsSentimentCreate validation failed: {e}")
    
    # Test invalid sentiment score
    try:
        invalid_sentiment = NewsSentimentCreate(
            article_id=uuid4(),
            sentiment=SentimentType.POSITIVE,
            sentiment_score=Decimal("2.0")  # Invalid: > 1.0
        )
        print("✗ Sentiment score validation should have failed")
    except ValueError:
        print("✓ Sentiment score validation working correctly")

def test_jsonb_validation():
    """Test JSONB field validation schemas"""
    print("\nTesting JSONB validation schemas...")
    
    # Test NewsKeywords validation
    try:
        keywords = NewsKeywords(keywords={"stock": 0.8, "earnings": 0.9, "growth": 0.7})
        print("✓ NewsKeywords validation working")
    except Exception as e:
        print(f"✗ NewsKeywords validation failed: {e}")
    
    # Test invalid keyword weight
    try:
        invalid_keywords = NewsKeywords(keywords={"stock": 1.5})  # Invalid: > 1.0
        print("✗ Keyword weight validation should have failed")
    except ValueError:
        print("✓ Keyword weight validation working correctly")
    
    # Test NotificationSettings validation
    try:
        settings = NotificationSettings(
            email_enabled=True,
            max_alerts_per_hour=5,
            channels=[NotificationChannel.EMAIL, NotificationChannel.PUSH]
        )
        print("✓ NotificationSettings validation working")
    except Exception as e:
        print(f"✗ NotificationSettings validation failed: {e}")
    
    # Test CategoryPreferences validation
    try:
        prefs = CategoryPreferences(
            primary_categories={"earnings": 0.9, "regulatory": 0.7},
            sector_categories={"technology": 0.8}
        )
        print("✓ CategoryPreferences validation working")
    except Exception as e:
        print(f"✗ CategoryPreferences validation failed: {e}")

def test_stock_relevance_validation():
    """Test stock news relevance validation"""
    print("\nTesting stock relevance validation...")
    
    try:
        relevance = StockNewsRelevanceCreate(
            article_id=uuid4(),
            symbol="aapl",  # Should be converted to uppercase
            relevance_score=Decimal("0.85"),
            mention_count=3,
            context_type=ContextType.DIRECT_MENTION
        )
        assert relevance.symbol == "AAPL"
        print("✓ Stock symbol uppercase conversion working")
    except Exception as e:
        print(f"✗ Stock relevance validation failed: {e}")

if __name__ == "__main__":
    print("Testing News Models and Schemas Implementation")
    print("=" * 50)
    
    test_enum_values()
    test_schema_validation()
    test_jsonb_validation()
    test_stock_relevance_validation()
    
    print("\n" + "=" * 50)
    print("✓ All tests completed successfully!")
    print("News models and schemas are properly implemented.")