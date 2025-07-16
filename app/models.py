"""
SQLAlchemy models for AI Investment Tool
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, Date, Time, ForeignKey, JSON, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    timezone = Column(String(50), default='UTC')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    total_value = Column(Numeric(15, 2), default=0.00)
    cash_balance = Column(Numeric(15, 2), default=0.00)
    
    # Strategy and Risk Management
    strategy = Column(String(50), default='balanced_growth')  # conservative_growth, balanced_growth, aggressive_growth
    risk_level = Column(String(20), default='moderate')      # low, moderate, high
    max_position_percent = Column(Numeric(5, 2))             # Maximum position size as percentage
    stop_loss_percent = Column(Numeric(6, 2))                # Stop loss percentage (negative)
    take_profit_percent = Column(Numeric(6, 2))              # Take profit percentage (positive)
    daily_loss_limit = Column(Numeric(15, 2))                # Maximum daily loss in dollars
    rebalance_frequency = Column(String(20), default='monthly')  # never, weekly, monthly, quarterly
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")
    analysis_sessions = relationship("AnalysisSession", back_populates="portfolio", cascade="all, delete-orphan")

class Holding(Base):
    __tablename__ = "holdings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    company_name = Column(String(255))
    shares = Column(Numeric(15, 6), nullable=False, default=0)
    average_cost = Column(Numeric(15, 4), default=0.00)
    current_price = Column(Numeric(15, 4))
    market_value = Column(Numeric(15, 2))
    unrealized_gain_loss = Column(Numeric(15, 2))
    unrealized_gain_loss_percent = Column(Numeric(8, 4))
    sector = Column(String(100))
    industry = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    transaction_type = Column(String(20), nullable=False, index=True)  # BUY, SELL, DIVIDEND, SPLIT, DEPOSIT, WITHDRAWAL
    shares = Column(Numeric(15, 6))
    price = Column(Numeric(15, 4))
    total_amount = Column(Numeric(15, 2), nullable=False)
    fees = Column(Numeric(15, 2), default=0.00)
    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    settlement_date = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    external_reference = Column(String(255))
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")

class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_type = Column(String(50), nullable=False)
    status = Column(String(20), default='PENDING', index=True)  # PENDING, RUNNING, COMPLETED, FAILED
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True))
    execution_time_ms = Column(Integer)
    api_calls_made = Column(Integer, default=0)
    cache_hits = Column(Integer, default=0)
    cost_estimate = Column(Numeric(10, 4))
    error_message = Column(Text)
    report_path = Column(String(500))
    
    # Raw Analysis Data Storage (Critical for Backtesting)
    market_data_snapshot = Column(JSONB)          # Complete market data at analysis time
    portfolio_snapshot = Column(JSONB)           # Portfolio state at analysis time
    ai_recommendations = Column(JSONB)           # Raw AI recommendations with confidence scores
    sentiment_analysis = Column(JSONB)           # News sentiment and market sentiment data
    technical_indicators = Column(JSONB)         # All technical indicators calculated
    risk_metrics = Column(JSONB)                 # Risk assessment and metrics
    trading_signals = Column(JSONB)              # Generated buy/sell/hold signals
    backtesting_context = Column(JSONB)          # Additional context for backtesting
    progress_logs = Column(JSONB)                # Real-time progress logging for UI
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="analysis_sessions")

class StockDataCache(Base):
    __tablename__ = "stock_data_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    data_type = Column(String(50), nullable=False)  # price_data, technical_indicators, company_info
    data = Column(JSONB, nullable=False)
    market_session = Column(String(20))
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    access_count = Column(Integer, default=1)

class NewsSentimentCache(Base):
    __tablename__ = "news_sentiment_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    articles = Column(JSONB, nullable=False)
    sentiment_score = Column(Numeric(5, 4))
    article_count = Column(Integer)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    access_count = Column(Integer, default=1)

class AIAnalysisCache(Base):
    __tablename__ = "ai_analysis_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    context_hash = Column(String(64), nullable=False, index=True)
    analysis_type = Column(String(50), nullable=False)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    response = Column(JSONB, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    access_count = Column(Integer, default=1)

class MarketSession(Base):
    __tablename__ = "market_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False, unique=True, index=True)
    session_type = Column(String(20), nullable=False, index=True)  # MARKET_OPEN, MARKET_CLOSE, PRE_MARKET, POST_MARKET, WEEKEND, HOLIDAY
    market_open_time = Column(Time)
    market_close_time = Column(Time)
    is_trading_day = Column(Boolean, default=True)
    holiday_name = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# News-related models
class NewsArticle(Base):
    __tablename__ = "news_articles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    content = Column(Text)
    url = Column(String(1000), nullable=False)
    url_to_image = Column(String(1000))
    source_name = Column(String(100), nullable=False, index=True)
    source_id = Column(String(50))
    author = Column(String(200))
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    content_hash = Column(String(64), unique=True, index=True)  # For deduplication
    
    # Additional metadata fields for enhanced functionality
    word_count = Column(Integer)
    reading_time_minutes = Column(Integer)
    language = Column(String(10))  # ISO language code
    country = Column(String(10))   # ISO country code
    
    # JSONB fields for flexible metadata storage
    article_metadata = Column(JSONB)  # Additional article metadata
    processing_metadata = Column(JSONB)  # Processing pipeline metadata
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    categories = relationship("NewsCategory", back_populates="article", cascade="all, delete-orphan")
    sentiment = relationship("NewsSentiment", back_populates="article", uselist=False, cascade="all, delete-orphan")
    stock_relevance = relationship("StockNewsRelevance", back_populates="article", cascade="all, delete-orphan")

class NewsCategory(Base):
    __tablename__ = "news_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False, index=True)
    category_type = Column(String(50), nullable=False)  # 'primary', 'sector', 'custom'
    category_value = Column(String(100), nullable=False)  # 'earnings', 'technology', etc.
    confidence_score = Column(Numeric(3, 2))  # 0.00 to 1.00
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    article = relationship("NewsArticle", back_populates="categories")

class NewsSentiment(Base):
    __tablename__ = "news_sentiment"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False, index=True)
    sentiment = Column(String(20), nullable=False, index=True)  # 'positive', 'negative', 'neutral'
    sentiment_score = Column(Numeric(4, 3))  # -1.000 to 1.000
    confidence_score = Column(Numeric(3, 2))  # 0.00 to 1.00
    impact_level = Column(String(20))  # 'high', 'medium', 'low'
    keywords = Column(JSONB)  # Extracted keywords and their weights
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    article = relationship("NewsArticle", back_populates="sentiment")

class StockNewsRelevance(Base):
    __tablename__ = "stock_news_relevance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    relevance_score = Column(Numeric(4, 3), nullable=False)  # 0.000 to 1.000
    mention_count = Column(Integer, default=1)
    context_type = Column(String(50))  # 'direct_mention', 'sector_related', 'competitor'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    article = relationship("NewsArticle", back_populates="stock_relevance")

class NewsSource(Base):
    __tablename__ = "news_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    url = Column(String(500))
    category = Column(String(50))
    language = Column(String(10))
    country = Column(String(10))
    quality_score = Column(Numeric(3, 2), default=0.50)  # 0.00 to 1.00
    is_active = Column(Boolean, default=True)
    api_provider = Column(String(50))  # 'newsapi', 'alpha_vantage', 'finnhub'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class UserNewsPreferences(Base):
    __tablename__ = "user_news_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    categories = Column(JSONB)  # Preferred categories and weights
    sources = Column(JSONB)  # Preferred/blocked sources
    sentiment_threshold = Column(Numeric(3, 2), default=0.30)
    impact_threshold = Column(String(20), default='medium')
    notification_settings = Column(JSONB)
    refresh_frequency = Column(Integer, default=60)  # minutes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")

class NewsFetchJob(Base):
    __tablename__ = "news_fetch_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(50), nullable=False)  # 'scheduled', 'manual', 'portfolio_triggered'
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), index=True)
    symbols = Column(JSONB)  # Array of symbols to fetch news for
    status = Column(String(20), default='pending', index=True)  # 'pending', 'running', 'completed', 'failed'
    api_provider = Column(String(50))
    articles_fetched = Column(Integer, default=0)
    api_calls_made = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    portfolio = relationship("Portfolio")

# Add indexes for performance optimization
from sqlalchemy import Index

# Create indexes for news tables
Index('idx_news_articles_published_at', NewsArticle.published_at.desc())
Index('idx_news_articles_source', NewsArticle.source_name)
Index('idx_news_articles_content_hash', NewsArticle.content_hash)
Index('idx_stock_news_relevance_symbol', StockNewsRelevance.symbol)
Index('idx_stock_news_relevance_score', StockNewsRelevance.relevance_score.desc())
Index('idx_news_sentiment_sentiment', NewsSentiment.sentiment)
Index('idx_news_categories_category', NewsCategory.category_type, NewsCategory.category_value)
Index('idx_news_fetch_jobs_status', NewsFetchJob.status)
Index('idx_user_news_preferences_user', UserNewsPreferences.user_id) 