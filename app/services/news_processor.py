"""
News Processing and Analysis Engine

This module provides comprehensive news processing capabilities including:
- Sentiment analysis using VADER and enhanced algorithms
- News categorization by type and sector
- Relevance scoring for stock-specific news
- Article deduplication using content hashing
- Integration with caching system for performance optimization
"""

import os
import re
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from enum import Enum
from difflib import SequenceMatcher

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from cache_manager import CacheManager
from .news_providers.base import NewsArticle, NewsProvider
from .news_providers.finnhub_provider import FinnhubProvider


class NewsCategory(Enum):
    """News category classifications"""
    EARNINGS = "earnings"
    MERGER_ACQUISITION = "merger_acquisition"
    PRODUCT_LAUNCH = "product_launch"
    REGULATORY = "regulatory"
    LEADERSHIP = "leadership"
    FINANCIAL = "financial"
    MARKET_ANALYSIS = "market_analysis"
    PARTNERSHIP = "partnership"
    LEGAL = "legal"
    GENERAL = "general"


class NewsSector(Enum):
    """Market sector classifications"""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCIAL = "financial"
    ENERGY = "energy"
    CONSUMER = "consumer"
    INDUSTRIAL = "industrial"
    MATERIALS = "materials"
    UTILITIES = "utilities"
    REAL_ESTATE = "real_estate"
    TELECOMMUNICATIONS = "telecommunications"
    GENERAL = "general"


@dataclass
class SentimentResult:
    """Sentiment analysis result"""
    sentiment: str  # positive, negative, neutral
    score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    details: Dict[str, float] = field(default_factory=dict)
    analysis_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CategoryResult:
    """News categorization result"""
    category: NewsCategory
    confidence: float  # 0.0 to 1.0
    sector: NewsSector
    keywords_matched: List[str] = field(default_factory=list)


@dataclass
class RelevanceResult:
    """Article relevance scoring result"""
    relevance_score: float  # 0.0 to 1.0
    symbol_mentions: int
    company_mentions: int
    title_relevance: float
    content_relevance: float
    matched_terms: List[str] = field(default_factory=list)


@dataclass
class ProcessedArticle:
    """Fully processed news article with all analysis results"""
    article: NewsArticle
    sentiment: SentimentResult
    category: CategoryResult
    relevance: RelevanceResult
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None  # content_hash of original
    processing_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SentimentAnalyzer:
    """Enhanced sentiment analysis using VADER and custom financial lexicon"""
    
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer()
        self.financial_lexicon = self._load_financial_lexicon()
        
    def _load_financial_lexicon(self) -> Dict[str, float]:
        """Load financial-specific sentiment lexicon"""
        # Enhanced financial sentiment words with scores
        return {
            # Positive financial terms
            'bullish': 0.8, 'rally': 0.7, 'surge': 0.8, 'soar': 0.9, 'boom': 0.8,
            'profit': 0.6, 'revenue': 0.5, 'growth': 0.7, 'gain': 0.6, 'beat': 0.7,
            'outperform': 0.8, 'upgrade': 0.7, 'buy': 0.6, 'strong': 0.6, 'positive': 0.5,
            'exceed': 0.7, 'record': 0.6, 'milestone': 0.6, 'breakthrough': 0.8,
            'expansion': 0.6, 'acquisition': 0.5, 'merger': 0.4, 'partnership': 0.5,
            
            # Negative financial terms  
            'bearish': -0.8, 'crash': -0.9, 'plunge': -0.8, 'tumble': -0.7, 'decline': -0.6,
            'loss': -0.7, 'deficit': -0.7, 'miss': -0.7, 'underperform': -0.8, 'downgrade': -0.7,
            'sell': -0.6, 'weak': -0.6, 'negative': -0.5, 'concern': -0.5, 'risk': -0.4,
            'lawsuit': -0.8, 'investigation': -0.7, 'scandal': -0.9, 'bankruptcy': -0.9,
            'layoffs': -0.8, 'restructuring': -0.6, 'warning': -0.6, 'alert': -0.5,
            
            # Neutral but important terms
            'earnings': 0.0, 'report': 0.0, 'announcement': 0.0, 'statement': 0.0,
            'guidance': 0.0, 'forecast': 0.0, 'outlook': 0.0, 'update': 0.0
        }
    
    def analyze_sentiment(self, text: str, symbol: Optional[str] = None) -> SentimentResult:
        """
        Analyze sentiment of text using VADER and financial lexicon
        
        Args:
            text: Text to analyze
            symbol: Optional stock symbol for context
            
        Returns:
            SentimentResult with comprehensive sentiment analysis
        """
        if not text or not text.strip():
            return SentimentResult(
                sentiment="neutral",
                score=0.0,
                confidence=0.0,
                details={"error": "Empty text provided"}
            )
        
        # Get VADER sentiment scores
        vader_scores = self.vader_analyzer.polarity_scores(text.lower())
        
        # Apply financial lexicon enhancement
        financial_score = self._calculate_financial_sentiment(text.lower())
        
        # Combine scores with weighted average
        # VADER gets 70% weight, financial lexicon gets 30%
        combined_score = (vader_scores['compound'] * 0.7) + (financial_score * 0.3)
        
        # Calculate confidence based on score magnitude and text length
        confidence = self._calculate_confidence(combined_score, text, vader_scores)
        
        # Determine sentiment category
        if combined_score > 0.1:
            sentiment = "positive"
        elif combined_score < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return SentimentResult(
            sentiment=sentiment,
            score=combined_score,
            confidence=confidence,
            details={
                "vader_compound": vader_scores['compound'],
                "vader_positive": vader_scores['pos'],
                "vader_negative": vader_scores['neg'],
                "vader_neutral": vader_scores['neu'],
                "financial_score": financial_score,
                "text_length": len(text),
                "symbol": symbol
            }
        )
    
    def _calculate_financial_sentiment(self, text: str) -> float:
        """Calculate sentiment score using financial lexicon"""
        words = re.findall(r'\b\w+\b', text.lower())
        scores = []
        
        for word in words:
            if word in self.financial_lexicon:
                scores.append(self.financial_lexicon[word])
        
        if not scores:
            return 0.0
        
        # Return average of matched financial terms
        return sum(scores) / len(scores)
    
    def _calculate_confidence(self, score: float, text: str, vader_scores: Dict) -> float:
        """Calculate confidence score for sentiment analysis"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence for stronger sentiment scores
        confidence += min(abs(score) * 0.5, 0.3)
        
        # Higher confidence for longer text (more context)
        text_length_factor = min(len(text) / 500, 0.2)
        confidence += text_length_factor
        
        # Higher confidence when VADER neutral score is low (less ambiguity)
        if vader_scores['neu'] < 0.5:
            confidence += 0.1
        
        # Ensure confidence stays within bounds
        return min(max(confidence, 0.1), 1.0)


class NewsCategorizer:
    """Automatic news categorization using keyword matching and pattern recognition"""
    
    def __init__(self):
        self.category_keywords = self._load_category_keywords()
        self.sector_keywords = self._load_sector_keywords()
    
    def _load_category_keywords(self) -> Dict[NewsCategory, List[str]]:
        """Load keyword patterns for news categories"""
        return {
            NewsCategory.EARNINGS: [
                'earnings', 'quarterly', 'q1', 'q2', 'q3', 'q4', 'revenue', 'profit',
                'eps', 'guidance', 'forecast', 'beat', 'miss', 'results', 'report'
            ],
            NewsCategory.MERGER_ACQUISITION: [
                'merger', 'acquisition', 'acquire', 'merge', 'takeover', 'buyout',
                'deal', 'purchase', 'combine', 'consolidation'
            ],
            NewsCategory.PRODUCT_LAUNCH: [
                'launch', 'release', 'unveil', 'introduce', 'debut', 'announce',
                'product', 'service', 'feature', 'update', 'version'
            ],
            NewsCategory.REGULATORY: [
                'fda', 'sec', 'regulation', 'regulatory', 'approval', 'compliance',
                'investigation', 'fine', 'penalty', 'lawsuit', 'legal', 'court'
            ],
            NewsCategory.LEADERSHIP: [
                'ceo', 'cfo', 'cto', 'president', 'executive', 'director', 'chairman',
                'appoint', 'hire', 'resign', 'retire', 'leadership', 'management'
            ],
            NewsCategory.FINANCIAL: [
                'funding', 'investment', 'capital', 'loan', 'debt', 'credit',
                'ipo', 'stock', 'share', 'dividend', 'buyback', 'split'
            ],
            NewsCategory.MARKET_ANALYSIS: [
                'analyst', 'rating', 'upgrade', 'downgrade', 'target', 'price',
                'recommendation', 'outlook', 'forecast', 'estimate'
            ],
            NewsCategory.PARTNERSHIP: [
                'partnership', 'collaborate', 'alliance', 'joint', 'agreement',
                'contract', 'deal', 'cooperation', 'team'
            ],
            NewsCategory.LEGAL: [
                'lawsuit', 'litigation', 'court', 'judge', 'settlement', 'patent',
                'intellectual property', 'copyright', 'trademark'
            ]
        }
    
    def _load_sector_keywords(self) -> Dict[NewsSector, List[str]]:
        """Load keyword patterns for market sectors"""
        return {
            NewsSector.TECHNOLOGY: [
                'software', 'hardware', 'tech', 'digital', 'ai', 'artificial intelligence',
                'cloud', 'data', 'internet', 'mobile', 'app', 'platform', 'cyber'
            ],
            NewsSector.HEALTHCARE: [
                'healthcare', 'medical', 'pharmaceutical', 'drug', 'medicine',
                'hospital', 'clinical', 'patient', 'treatment', 'therapy', 'biotech'
            ],
            NewsSector.FINANCIAL: [
                'bank', 'banking', 'finance', 'insurance', 'credit', 'loan',
                'mortgage', 'investment', 'trading', 'fintech'
            ],
            NewsSector.ENERGY: [
                'oil', 'gas', 'energy', 'renewable', 'solar', 'wind', 'electric',
                'battery', 'power', 'utility', 'coal', 'nuclear'
            ],
            NewsSector.CONSUMER: [
                'retail', 'consumer', 'shopping', 'brand', 'product', 'store',
                'restaurant', 'food', 'beverage', 'apparel', 'fashion'
            ],
            NewsSector.INDUSTRIAL: [
                'manufacturing', 'industrial', 'factory', 'production', 'machinery',
                'equipment', 'construction', 'infrastructure', 'logistics'
            ],
            NewsSector.MATERIALS: [
                'materials', 'mining', 'metals', 'steel', 'aluminum', 'copper',
                'chemicals', 'plastics', 'paper', 'packaging'
            ],
            NewsSector.UTILITIES: [
                'utility', 'utilities', 'water', 'electricity', 'gas', 'power',
                'grid', 'infrastructure', 'municipal'
            ],
            NewsSector.REAL_ESTATE: [
                'real estate', 'property', 'housing', 'residential', 'commercial',
                'reit', 'development', 'construction', 'mortgage'
            ],
            NewsSector.TELECOMMUNICATIONS: [
                'telecom', 'telecommunications', 'wireless', 'network', 'broadband',
                'internet', 'phone', 'mobile', 'carrier', '5g'
            ]
        }
    
    def categorize_article(self, article: NewsArticle) -> CategoryResult:
        """
        Categorize news article by type and sector
        
        Args:
            article: NewsArticle to categorize
            
        Returns:
            CategoryResult with category, sector, and confidence scores
        """
        # Combine title and description for analysis
        text = f"{article.title} {article.description or ''}".lower()
        
        # Find best matching category
        category, category_confidence, category_keywords = self._match_category(text)
        
        # Find best matching sector
        sector, sector_confidence = self._match_sector(text)
        
        # Overall confidence is average of category and sector confidence
        overall_confidence = (category_confidence + sector_confidence) / 2
        
        return CategoryResult(
            category=category,
            confidence=overall_confidence,
            sector=sector,
            keywords_matched=category_keywords
        )
    
    def _match_category(self, text: str) -> Tuple[NewsCategory, float, List[str]]:
        """Match text against category keywords"""
        best_category = NewsCategory.GENERAL
        best_score = 0.0
        matched_keywords = []
        
        for category, keywords in self.category_keywords.items():
            score = 0.0
            category_matches = []
            
            for keyword in keywords:
                if keyword in text:
                    score += 1.0
                    category_matches.append(keyword)
            
            # Normalize score by number of keywords in category
            normalized_score = score / len(keywords)
            
            if normalized_score > best_score:
                best_score = normalized_score
                best_category = category
                matched_keywords = category_matches
        
        # Convert to confidence (0-1 scale)
        confidence = min(best_score * 2, 1.0)  # Scale up for better sensitivity
        
        return best_category, confidence, matched_keywords
    
    def _match_sector(self, text: str) -> Tuple[NewsSector, float]:
        """Match text against sector keywords"""
        best_sector = NewsSector.GENERAL
        best_score = 0.0
        
        for sector, keywords in self.sector_keywords.items():
            score = 0.0
            
            for keyword in keywords:
                if keyword in text:
                    score += 1.0
            
            # Normalize score by number of keywords in sector
            normalized_score = score / len(keywords)
            
            if normalized_score > best_score:
                best_score = normalized_score
                best_sector = sector
        
        # Convert to confidence (0-1 scale)
        confidence = min(best_score * 2, 1.0)
        
        return best_sector, confidence


class RelevanceScorer:
    """Score article relevance to specific stocks using symbol/company matching"""
    
    def __init__(self):
        self.company_symbols = self._load_company_symbols()
    
    def _load_company_symbols(self) -> Dict[str, List[str]]:
        """Load mapping of company names to stock symbols"""
        # This could be expanded with a comprehensive database
        return {
            'AAPL': ['apple', 'iphone', 'ipad', 'mac', 'ios', 'tim cook'],
            'GOOGL': ['google', 'alphabet', 'android', 'youtube', 'chrome', 'sundar pichai'],
            'MSFT': ['microsoft', 'windows', 'office', 'azure', 'xbox', 'satya nadella'],
            'AMZN': ['amazon', 'aws', 'prime', 'alexa', 'jeff bezos', 'andy jassy'],
            'TSLA': ['tesla', 'elon musk', 'model s', 'model 3', 'model x', 'model y'],
            'META': ['meta', 'facebook', 'instagram', 'whatsapp', 'mark zuckerberg'],
            'NVDA': ['nvidia', 'gpu', 'graphics', 'ai chip', 'jensen huang'],
            'NFLX': ['netflix', 'streaming', 'reed hastings']
        }
    
    def score_relevance(self, article: NewsArticle, symbol: str) -> RelevanceResult:
        """
        Score article relevance to a specific stock symbol
        
        Args:
            article: NewsArticle to score
            symbol: Stock symbol to check relevance for
            
        Returns:
            RelevanceResult with detailed relevance scoring
        """
        symbol = symbol.upper()
        
        # Get text content for analysis
        title = article.title.lower() if article.title else ""
        description = article.description.lower() if article.description else ""
        content = article.content.lower() if article.content else ""
        
        # Count direct symbol mentions
        symbol_mentions = (
            title.count(symbol.lower()) +
            description.count(symbol.lower()) +
            content.count(symbol.lower())
        )
        
        # Count company-related term mentions
        company_mentions = 0
        matched_terms = []
        
        if symbol in self.company_symbols:
            company_terms = self.company_symbols[symbol]
            for term in company_terms:
                term_count = title.count(term) + description.count(term) + content.count(term)
                if term_count > 0:
                    company_mentions += term_count
                    matched_terms.append(term)
        
        # Calculate relevance scores for different parts
        title_relevance = self._calculate_text_relevance(title, symbol, symbol_mentions > 0)
        content_relevance = self._calculate_text_relevance(
            f"{description} {content}", symbol, company_mentions > 0
        )
        
        # Calculate overall relevance score
        relevance_score = self._calculate_overall_relevance(
            symbol_mentions, company_mentions, title_relevance, content_relevance
        )
        
        return RelevanceResult(
            relevance_score=relevance_score,
            symbol_mentions=symbol_mentions,
            company_mentions=company_mentions,
            title_relevance=title_relevance,
            content_relevance=content_relevance,
            matched_terms=matched_terms
        )
    
    def _calculate_text_relevance(self, text: str, symbol: str, has_mentions: bool) -> float:
        """Calculate relevance score for a piece of text"""
        if not text:
            return 0.0
        
        # Base score from mentions
        score = 0.3 if has_mentions else 0.0
        
        # Boost for symbol in title (very relevant)
        if symbol.lower() in text:
            score += 0.5
        
        # Check for financial keywords that increase relevance
        financial_keywords = [
            'earnings', 'revenue', 'profit', 'stock', 'share', 'price',
            'analyst', 'upgrade', 'downgrade', 'target', 'buy', 'sell'
        ]
        
        keyword_matches = sum(1 for keyword in financial_keywords if keyword in text)
        score += min(keyword_matches * 0.1, 0.3)
        
        return min(score, 1.0)
    
    def _calculate_overall_relevance(self, symbol_mentions: int, company_mentions: int,
                                   title_relevance: float, content_relevance: float) -> float:
        """Calculate overall relevance score"""
        # Weight different factors
        mention_score = min((symbol_mentions * 0.3 + company_mentions * 0.2), 0.6)
        title_weight = 0.4
        content_weight = 0.3
        
        overall_score = (
            mention_score +
            (title_relevance * title_weight) +
            (content_relevance * content_weight)
        )
        
        return min(overall_score, 1.0)

class NewsDeduplicator:
    """Deduplicate news articles using content hashing and similarity algorithms"""
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        self.seen_hashes: Set[str] = set()
        self.article_cache: Dict[str, NewsArticle] = {}
    
    def is_duplicate(self, article: NewsArticle) -> Tuple[bool, Optional[str]]:
        """
        Check if article is a duplicate of previously seen articles
        
        Args:
            article: NewsArticle to check
            
        Returns:
            Tuple of (is_duplicate, original_hash)
        """
        # Get content hash
        content_hash = article.content_hash
        
        # Check for exact hash match first
        if content_hash in self.seen_hashes:
            return True, content_hash
        
        # Check for similar articles using title similarity
        for existing_hash, existing_article in self.article_cache.items():
            if self._are_similar(article, existing_article):
                return True, existing_hash
        
        # Not a duplicate - add to cache
        self.seen_hashes.add(content_hash)
        self.article_cache[content_hash] = article
        
        return False, None
    
    def _are_similar(self, article1: NewsArticle, article2: NewsArticle) -> bool:
        """Check if two articles are similar using title and description comparison"""
        # Compare titles
        title_similarity = self._calculate_similarity(
            article1.title or "", article2.title or ""
        )
        
        # Compare descriptions if available
        desc_similarity = 0.0
        if article1.description and article2.description:
            desc_similarity = self._calculate_similarity(
                article1.description, article2.description
            )
        
        # Use the higher similarity score
        max_similarity = max(title_similarity, desc_similarity)
        
        return max_similarity >= self.similarity_threshold
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        if not text1 or not text2:
            return 0.0
        
        # Use SequenceMatcher for similarity calculation
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def clear_cache(self):
        """Clear the deduplication cache"""
        self.seen_hashes.clear()
        self.article_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get deduplication cache statistics"""
        return {
            "unique_articles": len(self.seen_hashes),
            "cached_articles": len(self.article_cache)
        }


class NewsProcessor:
    """
    Main news processing engine that coordinates all analysis components
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.cache_manager = cache_manager or CacheManager()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.categorizer = NewsCategorizer()
        self.relevance_scorer = RelevanceScorer()
        self.deduplicator = NewsDeduplicator()
        
    def process_articles(self, articles: List[NewsArticle], symbol: Optional[str] = None,
                        enable_caching: bool = True) -> List[ProcessedArticle]:
        """
        Process a list of news articles with full analysis pipeline
        
        Args:
            articles: List of NewsArticle objects to process
            symbol: Optional stock symbol for relevance scoring
            enable_caching: Whether to use caching for processed results
            
        Returns:
            List of ProcessedArticle objects with complete analysis
        """
        processed_articles = []
        
        for article in articles:
            try:
                # Check cache first if enabled
                if enable_caching and symbol:
                    cached_result = self._get_cached_processed_article(article, symbol)
                    if cached_result:
                        processed_articles.append(cached_result)
                        continue
                
                # Process the article
                processed_article = self._process_single_article(article, symbol)
                
                # Cache the result if enabled
                if enable_caching and symbol:
                    self._cache_processed_article(processed_article, symbol)
                
                processed_articles.append(processed_article)
                
            except Exception as e:
                print(f"Error processing article '{article.title}': {e}")
                # Create a minimal processed article for failed processing
                processed_articles.append(self._create_error_processed_article(article, str(e)))
        
        return processed_articles
    
    def _process_single_article(self, article: NewsArticle, symbol: Optional[str] = None) -> ProcessedArticle:
        """Process a single article through the full analysis pipeline"""
        # Sentiment analysis
        text_for_sentiment = f"{article.title} {article.description or ''}"
        sentiment = self.sentiment_analyzer.analyze_sentiment(text_for_sentiment, symbol)
        
        # Categorization
        category = self.categorizer.categorize_article(article)
        
        # Relevance scoring (if symbol provided)
        if symbol:
            relevance = self.relevance_scorer.score_relevance(article, symbol)
        else:
            relevance = RelevanceResult(
                relevance_score=0.5,  # Default neutral relevance
                symbol_mentions=0,
                company_mentions=0,
                title_relevance=0.0,
                content_relevance=0.0
            )
        
        # Deduplication check
        is_duplicate, duplicate_of = self.deduplicator.is_duplicate(article)
        
        return ProcessedArticle(
            article=article,
            sentiment=sentiment,
            category=category,
            relevance=relevance,
            is_duplicate=is_duplicate,
            duplicate_of=duplicate_of
        )
    
    def _get_cached_processed_article(self, article: NewsArticle, symbol: str) -> Optional[ProcessedArticle]:
        """Retrieve cached processed article if available"""
        try:
            cache_key = f"{symbol}_{article.content_hash}"
            cached_data = self.cache_manager.get_cached_data('processed_news', cache_key)
            
            if cached_data:
                # Reconstruct ProcessedArticle from cached data
                return self._deserialize_processed_article(cached_data)
            
        except Exception as e:
            print(f"Error retrieving cached processed article: {e}")
        
        return None
    
    def _cache_processed_article(self, processed_article: ProcessedArticle, symbol: str):
        """Cache processed article for future use"""
        try:
            cache_key = f"{symbol}_{processed_article.article.content_hash}"
            serialized_data = self._serialize_processed_article(processed_article)
            
            self.cache_manager.cache_data('processed_news', cache_key, serialized_data)
            
        except Exception as e:
            print(f"Error caching processed article: {e}")
    
    def _create_error_processed_article(self, article: NewsArticle, error_msg: str) -> ProcessedArticle:
        """Create a ProcessedArticle for failed processing"""
        return ProcessedArticle(
            article=article,
            sentiment=SentimentResult(
                sentiment="neutral",
                score=0.0,
                confidence=0.0,
                details={"error": error_msg}
            ),
            category=CategoryResult(
                category=NewsCategory.GENERAL,
                confidence=0.0,
                sector=NewsSector.GENERAL
            ),
            relevance=RelevanceResult(
                relevance_score=0.0,
                symbol_mentions=0,
                company_mentions=0,
                title_relevance=0.0,
                content_relevance=0.0
            )
        )
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            "deduplication_stats": self.deduplicator.get_cache_stats(),
            "cache_stats": self.cache_manager.get_cache_stats() if self.cache_manager else None,
            "processing_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def clear_caches(self):
        """Clear all processing caches"""
        self.deduplicator.clear_cache()
        if self.cache_manager:
            self.cache_manager.invalidate_cache('processed_news')  
  
    def _serialize_processed_article(self, processed_article: ProcessedArticle) -> Dict:
        """Serialize ProcessedArticle for caching"""
        return {
            'article': {
                'title': processed_article.article.title,
                'description': processed_article.article.description,
                'content': processed_article.article.content,
                'url': processed_article.article.url,
                'url_to_image': processed_article.article.url_to_image,
                'source_name': processed_article.article.source_name,
                'source_id': processed_article.article.source_id,
                'author': processed_article.article.author,
                'published_at': processed_article.article.published_at.isoformat(),
                'symbol': processed_article.article.symbol
            },
            'sentiment': {
                'sentiment': processed_article.sentiment.sentiment,
                'score': processed_article.sentiment.score,
                'confidence': processed_article.sentiment.confidence,
                'details': processed_article.sentiment.details,
                'analysis_timestamp': processed_article.sentiment.analysis_timestamp.isoformat()
            },
            'category': {
                'category': processed_article.category.category.value,
                'confidence': processed_article.category.confidence,
                'sector': processed_article.category.sector.value,
                'keywords_matched': processed_article.category.keywords_matched
            },
            'relevance': {
                'relevance_score': processed_article.relevance.relevance_score,
                'symbol_mentions': processed_article.relevance.symbol_mentions,
                'company_mentions': processed_article.relevance.company_mentions,
                'title_relevance': processed_article.relevance.title_relevance,
                'content_relevance': processed_article.relevance.content_relevance,
                'matched_terms': processed_article.relevance.matched_terms
            },
            'is_duplicate': processed_article.is_duplicate,
            'duplicate_of': processed_article.duplicate_of,
            'processing_timestamp': processed_article.processing_timestamp.isoformat()
        }
    
    def _deserialize_processed_article(self, data: Dict) -> ProcessedArticle:
        """Deserialize ProcessedArticle from cached data"""
        # Reconstruct NewsArticle
        article_data = data['article']
        article = NewsArticle(
            title=article_data['title'],
            description=article_data['description'],
            content=article_data['content'],
            url=article_data['url'],
            url_to_image=article_data['url_to_image'],
            source_name=article_data['source_name'],
            source_id=article_data['source_id'],
            author=article_data['author'],
            published_at=datetime.fromisoformat(article_data['published_at']),
            symbol=article_data['symbol']
        )
        
        # Reconstruct SentimentResult
        sentiment_data = data['sentiment']
        sentiment = SentimentResult(
            sentiment=sentiment_data['sentiment'],
            score=sentiment_data['score'],
            confidence=sentiment_data['confidence'],
            details=sentiment_data['details'],
            analysis_timestamp=datetime.fromisoformat(sentiment_data['analysis_timestamp'])
        )
        
        # Reconstruct CategoryResult
        category_data = data['category']
        category = CategoryResult(
            category=NewsCategory(category_data['category']),
            confidence=category_data['confidence'],
            sector=NewsSector(category_data['sector']),
            keywords_matched=category_data['keywords_matched']
        )
        
        # Reconstruct RelevanceResult
        relevance_data = data['relevance']
        relevance = RelevanceResult(
            relevance_score=relevance_data['relevance_score'],
            symbol_mentions=relevance_data['symbol_mentions'],
            company_mentions=relevance_data['company_mentions'],
            title_relevance=relevance_data['title_relevance'],
            content_relevance=relevance_data['content_relevance'],
            matched_terms=relevance_data['matched_terms']
        )
        
        return ProcessedArticle(
            article=article,
            sentiment=sentiment,
            category=category,
            relevance=relevance,
            is_duplicate=data['is_duplicate'],
            duplicate_of=data['duplicate_of'],
            processing_timestamp=datetime.fromisoformat(data['processing_timestamp'])
        )


# Convenience function for backward compatibility with existing ai_analyzer.py
def get_enhanced_sentiment_analysis(symbol: str, articles: List[NewsArticle] = None, 
                                   force_refresh: bool = False) -> Dict:
    """
    Enhanced sentiment analysis function for backward compatibility
    
    Args:
        symbol: Stock symbol
        articles: Optional list of articles (if None, will fetch from provider)
        force_refresh: Whether to force refresh cached data
        
    Returns:
        Dictionary with sentiment analysis results
    """
    try:
        # Initialize processor
        processor = NewsProcessor()
        
        # Get articles if not provided
        if articles is None:
            finnhub_api_key = os.getenv('FINNHUB_API_KEY')
            if not finnhub_api_key:
                return {
                    "sentiment": "neutral",
                    "score": 0.0,
                    "articles_analyzed": 0,
                    "retrieval_timestamp": datetime.now(timezone.utc),
                    "news_age_minutes": "no_api_key",
                    "symbol": symbol
                }
            
            provider = FinnhubProvider(finnhub_api_key)
            articles = provider.fetch_news_for_symbol(symbol, limit=10)
        
        if not articles:
            return {
                "sentiment": "neutral",
                "score": 0.0,
                "articles_analyzed": 0,
                "retrieval_timestamp": datetime.now(timezone.utc),
                "news_age_minutes": "no_news",
                "symbol": symbol
            }
        
        # Process articles
        processed_articles = processor.process_articles(articles, symbol, not force_refresh)
        
        # Calculate aggregate sentiment
        sentiment_scores = []
        latest_timestamp = None
        
        for processed in processed_articles:
            if not processed.is_duplicate:
                sentiment_scores.append(processed.sentiment.score)
                
                # Track latest news timestamp
                if (latest_timestamp is None or 
                    processed.article.published_at > latest_timestamp):
                    latest_timestamp = processed.article.published_at
        
        if not sentiment_scores:
            overall_score = 0.0
            news_age_minutes = "unknown"
        else:
            overall_score = sum(sentiment_scores) / len(sentiment_scores)
            
            # Calculate news age
            if latest_timestamp:
                now = datetime.now(timezone.utc)
                age_delta = now - latest_timestamp
                news_age_minutes = int(age_delta.total_seconds() / 60)
            else:
                news_age_minutes = "unknown"
        
        # Determine sentiment category
        if overall_score > 0.1:
            sentiment = "positive"
        elif overall_score < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "score": overall_score,
            "articles_analyzed": len(sentiment_scores),
            "retrieval_timestamp": datetime.now(timezone.utc),
            "latest_news_timestamp": latest_timestamp,
            "news_age_minutes": news_age_minutes,
            "symbol": symbol,
            "processed_articles": processed_articles  # Additional detail
        }
        
    except Exception as e:
        print(f"Error in enhanced sentiment analysis for {symbol}: {e}")
        return {
            "sentiment": "neutral",
            "score": 0.0,
            "articles_analyzed": 0,
            "retrieval_timestamp": datetime.now(timezone.utc),
            "news_age_minutes": "error",
            "symbol": symbol,
            "error": str(e)
        }