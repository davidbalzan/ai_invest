#!/usr/bin/env python3
"""
Test script for the News Processing and Analysis Engine
"""

import sys
import os
from datetime import datetime, timezone

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.news_processor import (
    NewsProcessor, SentimentAnalyzer, NewsCategorizer, 
    RelevanceScorer, NewsDeduplicator
)
from app.services.news_providers.base import NewsArticle


def create_test_articles():
    """Create test news articles for processing"""
    articles = [
        NewsArticle(
            title="Apple Reports Record Q4 Earnings, Beats Wall Street Expectations",
            description="Apple Inc. announced strong quarterly results with revenue growth driven by iPhone sales and services.",
            content=None,
            url="https://example.com/apple-earnings",
            url_to_image=None,
            source_name="Financial News",
            source_id="fn001",
            author="John Smith",
            published_at=datetime.now(timezone.utc),
            symbol="AAPL"
        ),
        NewsArticle(
            title="Tesla Stock Plunges After CEO Elon Musk Announces Production Delays",
            description="Tesla shares fell sharply following news of manufacturing challenges at the company's new facility.",
            content=None,
            url="https://example.com/tesla-delays",
            url_to_image=None,
            source_name="Tech Today",
            source_id="tt002",
            author="Jane Doe",
            published_at=datetime.now(timezone.utc),
            symbol="TSLA"
        ),
        NewsArticle(
            title="Microsoft Announces Strategic Partnership with OpenAI for Cloud Services",
            description="Microsoft and OpenAI expand their collaboration to integrate AI capabilities across Azure platform.",
            content=None,
            url="https://example.com/msft-openai",
            url_to_image=None,
            source_name="Cloud Computing Weekly",
            source_id="ccw003",
            author="Tech Reporter",
            published_at=datetime.now(timezone.utc),
            symbol="MSFT"
        ),
        NewsArticle(
            title="FDA Approves New Drug from Biotech Startup, Shares Surge 200%",
            description="Regulatory approval for breakthrough therapy sends biotech stock soaring in after-hours trading.",
            content=None,
            url="https://example.com/biotech-approval",
            url_to_image=None,
            source_name="Healthcare News",
            source_id="hn004",
            author="Medical Writer",
            published_at=datetime.now(timezone.utc),
            symbol=None
        ),
        # Duplicate article to test deduplication
        NewsArticle(
            title="Apple Reports Record Q4 Earnings, Exceeds Wall Street Expectations",
            description="Apple Inc. announced strong quarterly results with revenue growth driven by iPhone sales and services.",
            content=None,
            url="https://example.com/apple-earnings-duplicate",
            url_to_image=None,
            source_name="Financial News",
            source_id="fn005",
            author="John Smith",
            published_at=datetime.now(timezone.utc),
            symbol="AAPL"
        )
    ]
    return articles


def test_sentiment_analyzer():
    """Test the SentimentAnalyzer component"""
    print("🧪 Testing SentimentAnalyzer...")
    
    analyzer = SentimentAnalyzer()
    
    test_cases = [
        ("Apple beats earnings expectations with record revenue", "positive"),
        ("Tesla stock crashes after production delays announced", "negative"),
        ("Microsoft announces new product launch", "neutral"),
        ("Company files for bankruptcy amid financial troubles", "negative"),
        ("Strong quarterly growth drives stock surge", "positive")
    ]
    
    for title, expected in test_cases:
        result = analyzer.analyze(title)
        print(f"  📝 '{title[:40]}...'")
        print(f"     Sentiment: {result.sentiment.value} (expected: {expected})")
        print(f"     Score: {result.score:.3f}, Confidence: {result.confidence:.3f}")
        print(f"     Impact: {result.impact_level.value}, Keywords: {result.keywords[:3]}")
        print()


def test_news_categorizer():
    """Test the NewsCategorizer component"""
    print("🧪 Testing NewsCategorizer...")
    
    categorizer = NewsCategorizer()
    
    test_cases = [
        "Apple reports quarterly earnings results",
        "Microsoft announces merger with tech startup",
        "FDA approves new pharmaceutical drug",
        "Tesla launches new electric vehicle model",
        "CEO resigns from major corporation"
    ]
    
    for title in test_cases:
        article = NewsArticle(
            title=title, description="", content=None, url="", url_to_image=None,
            source_name="Test", source_id="test", author="Test", 
            published_at=datetime.now(timezone.utc)
        )
        
        categories = categorizer.categorize(article)
        print(f"  📝 '{title}'")
        for cat in categories:
            print(f"     {cat.category_type}: {cat.category_value} (confidence: {cat.confidence_score:.2f})")
            print(f"     Keywords: {cat.matched_keywords}")
        print()


def test_relevance_scorer():
    """Test the RelevanceScorer component"""
    print("🧪 Testing RelevanceScorer...")
    
    scorer = RelevanceScorer()
    
    test_article = NewsArticle(
        title="Apple iPhone sales drive strong quarterly performance for tech giant",
        description="Apple Inc. reported better than expected results driven by iPhone demand",
        content=None, url="", url_to_image=None, source_name="Test", 
        source_id="test", author="Test", published_at=datetime.now(timezone.utc),
        symbol="AAPL"
    )
    
    target_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
    scores = scorer.score_relevance(test_article, target_symbols)
    
    print(f"  📝 Article: '{test_article.title[:50]}...'")
    for score in scores:
        print(f"     {score.symbol}: {score.relevance_score:.3f} ({score.context_type})")
        print(f"     Mentions: {score.mention_count}, Terms: {score.matched_terms}")
    print()


def test_news_deduplicator():
    """Test the NewsDeduplicator component"""
    print("🧪 Testing NewsDeduplicator...")
    
    deduplicator = NewsDeduplicator()
    
    # Create similar articles
    article1 = NewsArticle(
        title="Apple reports strong quarterly earnings",
        description="Company beats expectations", content=None, url="url1",
        url_to_image=None, source_name="Source1", source_id="1", 
        author="Author1", published_at=datetime.now(timezone.utc)
    )
    
    article2 = NewsArticle(
        title="Apple reports strong quarterly earnings results",  # Very similar
        description="Company beats expectations", content=None, url="url2",
        url_to_image=None, source_name="Source2", source_id="2", 
        author="Author2", published_at=datetime.now(timezone.utc)
    )
    
    article3 = NewsArticle(
        title="Microsoft announces new product launch",  # Different
        description="New software release", content=None, url="url3",
        url_to_image=None, source_name="Source3", source_id="3", 
        author="Author3", published_at=datetime.now(timezone.utc)
    )
    
    # Test deduplication
    is_dup1, hash1 = deduplicator.is_duplicate(article1)
    print(f"  📝 Article 1: Duplicate = {is_dup1}")
    
    is_dup2, hash2 = deduplicator.is_duplicate(article2)
    print(f"  📝 Article 2 (similar): Duplicate = {is_dup2}")
    
    is_dup3, hash3 = deduplicator.is_duplicate(article3)
    print(f"  📝 Article 3 (different): Duplicate = {is_dup3}")
    print()


def test_full_news_processor():
    """Test the complete NewsProcessor pipeline"""
    print("🧪 Testing Full NewsProcessor Pipeline...")
    
    processor = NewsProcessor()
    articles = create_test_articles()
    
    print(f"  📥 Processing {len(articles)} test articles...")
    
    # Process articles
    processed_articles = processor.process_articles(articles, target_symbols=["AAPL", "TSLA", "MSFT"])
    
    print(f"  ✅ Successfully processed {len(processed_articles)} articles")
    
    # Display results
    for i, processed in enumerate(processed_articles):
        print(f"\n  📰 Article {i+1}: {processed.original_article.title[:50]}...")
        print(f"     Sentiment: {processed.sentiment.sentiment.value} ({processed.sentiment.score:.3f})")
        print(f"     Impact: {processed.sentiment.impact_level.value}")
        
        if processed.categories:
            print(f"     Categories: {[f'{cat.category_type}:{cat.category_value}' for cat in processed.categories]}")
        
        if processed.relevance_scores:
            top_relevance = processed.relevance_scores[0]
            print(f"     Top Relevance: {top_relevance.symbol} ({top_relevance.relevance_score:.3f})")
    
    # Get processing stats
    stats = processor.get_processing_stats()
    print(f"\n  📊 Processing Stats:")
    print(f"     Seen articles: {stats['seen_articles']}")
    print(f"     Unique hashes: {stats['unique_hashes']}")


def main():
    """Run all tests"""
    print("🚀 Starting News Processor Tests\n")
    
    try:
        test_sentiment_analyzer()
        test_news_categorizer()
        test_relevance_scorer()
        test_news_deduplicator()
        test_full_news_processor()
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())