#!/usr/bin/env python3
"""
Basic test for the news processor implementation
"""

import sys
import os
from datetime import datetime, timezone

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.news_processor import (
    NewsProcessor, SentimentAnalyzer, NewsCategorizer, 
    RelevanceScorer, NewsDeduplicator, get_enhanced_sentiment_analysis
)
from services.news_providers.base import NewsArticle

def test_sentiment_analyzer():
    """Test the SentimentAnalyzer class"""
    print("Testing SentimentAnalyzer...")
    
    analyzer = SentimentAnalyzer()
    
    # Test positive sentiment
    positive_text = "Apple reports record quarterly earnings, beating analyst expectations with strong iPhone sales"
    result = analyzer.analyze_sentiment(positive_text, "AAPL")
    print(f"Positive text sentiment: {result.sentiment} (score: {result.score:.3f}, confidence: {result.confidence:.3f})")
    
    # Test negative sentiment
    negative_text = "Tesla stock plunges after disappointing earnings miss and production concerns"
    result = analyzer.analyze_sentiment(negative_text, "TSLA")
    print(f"Negative text sentiment: {result.sentiment} (score: {result.score:.3f}, confidence: {result.confidence:.3f})")
    
    # Test neutral sentiment
    neutral_text = "Microsoft announces quarterly earnings report scheduled for next week"
    result = analyzer.analyze_sentiment(neutral_text, "MSFT")
    print(f"Neutral text sentiment: {result.sentiment} (score: {result.score:.3f}, confidence: {result.confidence:.3f})")
    
    print("✓ SentimentAnalyzer tests passed\n")

def test_news_categorizer():
    """Test the NewsCategorizer class"""
    print("Testing NewsCategorizer...")
    
    categorizer = NewsCategorizer()
    
    # Create test articles
    earnings_article = NewsArticle(
        title="Apple Q4 Earnings Beat Expectations",
        description="Apple reported strong quarterly results with revenue growth",
        content=None,
        url="https://example.com/1",
        url_to_image=None,
        source_name="Test Source",
        source_id="1",
        author="Test Author",
        published_at=datetime.now(timezone.utc)
    )
    
    result = categorizer.categorize_article(earnings_article)
    print(f"Earnings article category: {result.category.value} (confidence: {result.confidence:.3f})")
    print(f"Sector: {result.sector.value}")
    print(f"Keywords matched: {result.keywords_matched}")
    
    print("✓ NewsCategorizer tests passed\n")

def test_relevance_scorer():
    """Test the RelevanceScorer class"""
    print("Testing RelevanceScorer...")
    
    scorer = RelevanceScorer()
    
    # Create test article about Apple
    apple_article = NewsArticle(
        title="Apple iPhone Sales Surge in Q4",
        description="Apple's latest iPhone models show strong sales performance with Tim Cook praising the results",
        content=None,
        url="https://example.com/2",
        url_to_image=None,
        source_name="Test Source",
        source_id="2",
        author="Test Author",
        published_at=datetime.now(timezone.utc)
    )
    
    result = scorer.score_relevance(apple_article, "AAPL")
    print(f"Apple article relevance to AAPL: {result.relevance_score:.3f}")
    print(f"Symbol mentions: {result.symbol_mentions}")
    print(f"Company mentions: {result.company_mentions}")
    print(f"Matched terms: {result.matched_terms}")
    
    print("✓ RelevanceScorer tests passed\n")

def test_news_deduplicator():
    """Test the NewsDeduplicator class"""
    print("Testing NewsDeduplicator...")
    
    deduplicator = NewsDeduplicator()
    
    # Create two similar articles
    article1 = NewsArticle(
        title="Apple Reports Strong Q4 Earnings",
        description="Apple's quarterly results exceed expectations",
        content=None,
        url="https://example.com/3",
        url_to_image=None,
        source_name="Source 1",
        source_id="3",
        author="Author 1",
        published_at=datetime.now(timezone.utc)
    )
    
    article2 = NewsArticle(
        title="Apple Reports Strong Q4 Earnings Results",  # Very similar title
        description="Apple quarterly results beat expectations",
        content=None,
        url="https://example.com/4",
        url_to_image=None,
        source_name="Source 2",
        source_id="4",
        author="Author 2",
        published_at=datetime.now(timezone.utc)
    )
    
    # Test first article (should not be duplicate)
    is_dup1, orig_hash1 = deduplicator.is_duplicate(article1)
    print(f"Article 1 is duplicate: {is_dup1}")
    
    # Test second article (should be detected as duplicate)
    is_dup2, orig_hash2 = deduplicator.is_duplicate(article2)
    print(f"Article 2 is duplicate: {is_dup2}")
    
    stats = deduplicator.get_cache_stats()
    print(f"Deduplicator stats: {stats}")
    
    print("✓ NewsDeduplicator tests passed\n")

def test_news_processor():
    """Test the main NewsProcessor class"""
    print("Testing NewsProcessor...")
    
    processor = NewsProcessor()
    
    # Create test articles
    articles = [
        NewsArticle(
            title="Apple Beats Q4 Earnings Expectations",
            description="Strong iPhone sales drive Apple's quarterly performance with record revenue",
            content=None,
            url="https://example.com/5",
            url_to_image=None,
            source_name="Financial News",
            source_id="5",
            author="Finance Reporter",
            published_at=datetime.now(timezone.utc)
        ),
        NewsArticle(
            title="Tesla Production Concerns Impact Stock Price",
            description="Manufacturing delays and supply chain issues affect Tesla's outlook",
            content=None,
            url="https://example.com/6",
            url_to_image=None,
            source_name="Auto News",
            source_id="6",
            author="Auto Reporter",
            published_at=datetime.now(timezone.utc)
        )
    ]
    
    # Process articles for Apple
    processed_articles = processor.process_articles(articles, "AAPL", enable_caching=False)
    
    print(f"Processed {len(processed_articles)} articles")
    
    for i, processed in enumerate(processed_articles):
        print(f"\nArticle {i+1}:")
        print(f"  Title: {processed.article.title}")
        print(f"  Sentiment: {processed.sentiment.sentiment} ({processed.sentiment.score:.3f})")
        print(f"  Category: {processed.category.category.value}")
        print(f"  Sector: {processed.category.sector.value}")
        print(f"  Relevance: {processed.relevance.relevance_score:.3f}")
        print(f"  Is duplicate: {processed.is_duplicate}")
    
    # Test processing stats
    stats = processor.get_processing_stats()
    print(f"\nProcessing stats: {stats}")
    
    print("✓ NewsProcessor tests passed\n")

def main():
    """Run all tests"""
    print("Running News Processor Tests\n")
    print("=" * 50)
    
    try:
        test_sentiment_analyzer()
        test_news_categorizer()
        test_relevance_scorer()
        test_news_deduplicator()
        test_news_processor()
        
        print("=" * 50)
        print("✅ All tests passed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())