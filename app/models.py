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