"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID
from enum import Enum

# Enums
class TransactionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    SPLIT = "SPLIT"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"

class AnalysisStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class MarketSessionType(str, Enum):
    MARKET_OPEN = "MARKET_OPEN"
    MARKET_CLOSE = "MARKET_CLOSE"
    PRE_MARKET = "PRE_MARKET"
    POST_MARKET = "POST_MARKET"
    WEEKEND = "WEEKEND"
    HOLIDAY = "HOLIDAY"

class InvestmentStrategy(str, Enum):
    CONSERVATIVE_GROWTH = "conservative_growth"
    BALANCED_GROWTH = "balanced_growth"
    AGGRESSIVE_GROWTH = "aggressive_growth"

class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"

class RebalanceFrequency(str, Enum):
    NEVER = "never"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

# Base schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    timezone: str = "UTC"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

# Portfolio schemas
class PortfolioBase(BaseModel):
    name: str
    description: Optional[str] = None
    cash_balance: Optional[Decimal] = Decimal('0.00')
    
    # Strategy and Risk Management
    strategy: Optional[InvestmentStrategy] = InvestmentStrategy.BALANCED_GROWTH
    risk_level: Optional[RiskLevel] = RiskLevel.MODERATE
    max_position_percent: Optional[Decimal] = None
    stop_loss_percent: Optional[Decimal] = None
    take_profit_percent: Optional[Decimal] = None
    daily_loss_limit: Optional[Decimal] = None
    rebalance_frequency: Optional[RebalanceFrequency] = RebalanceFrequency.MONTHLY

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cash_balance: Optional[Decimal] = None
    is_active: Optional[bool] = None
    
    # Strategy and Risk Management
    strategy: Optional[InvestmentStrategy] = None
    risk_level: Optional[RiskLevel] = None
    max_position_percent: Optional[Decimal] = None
    stop_loss_percent: Optional[Decimal] = None
    take_profit_percent: Optional[Decimal] = None
    daily_loss_limit: Optional[Decimal] = None
    rebalance_frequency: Optional[RebalanceFrequency] = None

class Portfolio(PortfolioBase):
    id: UUID
    user_id: UUID
    total_value: Decimal
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

# Holding schemas
class HoldingBase(BaseModel):
    symbol: str
    company_name: Optional[str] = None
    shares: Decimal
    average_cost: Optional[Decimal] = Decimal('0.00')
    sector: Optional[str] = None
    industry: Optional[str] = None

class HoldingCreate(HoldingBase):
    portfolio_id: UUID

class HoldingUpdate(BaseModel):
    company_name: Optional[str] = None
    shares: Optional[Decimal] = None
    average_cost: Optional[Decimal] = None
    current_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    unrealized_gain_loss: Optional[Decimal] = None
    unrealized_gain_loss_percent: Optional[Decimal] = None
    sector: Optional[str] = None
    industry: Optional[str] = None

class Holding(HoldingBase):
    id: UUID
    portfolio_id: UUID
    current_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    unrealized_gain_loss: Optional[Decimal] = None
    unrealized_gain_loss_percent: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Transaction schemas
class TransactionBase(BaseModel):
    symbol: str
    transaction_type: TransactionType
    shares: Optional[Decimal] = None
    price: Optional[Decimal] = None
    total_amount: Decimal
    fees: Optional[Decimal] = Decimal('0.00')
    transaction_date: datetime
    settlement_date: Optional[datetime] = None
    notes: Optional[str] = None
    external_reference: Optional[str] = None

class TransactionCreate(TransactionBase):
    portfolio_id: UUID

class TransactionUpdate(BaseModel):
    shares: Optional[Decimal] = None
    price: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    transaction_date: Optional[datetime] = None
    settlement_date: Optional[datetime] = None
    notes: Optional[str] = None
    external_reference: Optional[str] = None

class Transaction(TransactionBase):
    id: UUID
    portfolio_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

# Analysis Session schemas
class AnalysisSessionBase(BaseModel):
    analysis_type: str
    status: AnalysisStatus = AnalysisStatus.PENDING

class AnalysisSessionCreate(AnalysisSessionBase):
    portfolio_id: UUID

class AnalysisSessionUpdate(BaseModel):
    status: Optional[AnalysisStatus] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    api_calls_made: Optional[int] = None
    cache_hits: Optional[int] = None
    cost_estimate: Optional[Decimal] = None
    error_message: Optional[str] = None
    report_path: Optional[str] = None

class AnalysisSession(AnalysisSessionBase):
    id: UUID
    portfolio_id: UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    api_calls_made: Optional[int] = None
    cache_hits: Optional[int] = None
    cost_estimate: Optional[Decimal] = None
    error_message: Optional[str] = None
    report_path: Optional[str] = None
    
    class Config:
        from_attributes = True

# Portfolio with relationships
class PortfolioWithDetails(Portfolio):
    holdings: List[Holding] = []
    transactions: List[Transaction] = []
    analysis_sessions: List[AnalysisSession] = []

# User with portfolios
class UserWithPortfolios(User):
    portfolios: List[Portfolio] = []

# Cache schemas
class CacheStats(BaseModel):
    total_entries: int
    expired_entries: int
    cache_size_mb: float
    hit_rate: float
    most_accessed: List[Dict[str, Any]]

# Analysis request schemas
class AnalysisRequest(BaseModel):
    portfolio_id: UUID
    analysis_type: str = "full_analysis"
    include_charts: bool = True
    include_ai_recommendations: bool = True
    include_sentiment_analysis: bool = True
    force_refresh: bool = False  # Bypass cache and fetch fresh data

# Portfolio summary schema
class PortfolioSummary(BaseModel):
    portfolio: Portfolio
    total_holdings: int
    total_value: Decimal
    total_gain_loss: Decimal
    total_gain_loss_percent: Decimal
    top_performers: List[Holding]
    worst_performers: List[Holding]
    sector_allocation: Dict[str, Decimal]
    recent_transactions: List[Transaction]

# News-related enums
class NewsCategoryType(str, Enum):
    PRIMARY = "primary"
    SECTOR = "sector"
    CUSTOM = "custom"

class NewsPrimaryCategory(str, Enum):
    EARNINGS = "earnings"
    MERGERS_ACQUISITIONS = "mergers_acquisitions"
    REGULATORY = "regulatory"
    PRODUCT_LAUNCH = "product_launch"
    MANAGEMENT_CHANGES = "management_changes"
    MARKET_ANALYSIS = "market_analysis"
    ANALYST_RATING = "analyst_rating"
    DIVIDEND = "dividend"
    STOCK_SPLIT = "stock_split"
    BANKRUPTCY = "bankruptcy"
    IPO = "ipo"
    PARTNERSHIP = "partnership"
    LEGAL_ISSUES = "legal_issues"
    CLINICAL_TRIALS = "clinical_trials"
    GUIDANCE_UPDATE = "guidance_update"
    SHARE_BUYBACK = "share_buyback"
    DEBT_RESTRUCTURING = "debt_restructuring"

class NewsSectorCategory(str, Enum):
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    ENERGY = "energy"
    CONSUMER_DISCRETIONARY = "consumer_discretionary"
    CONSUMER_STAPLES = "consumer_staples"
    INDUSTRIAL = "industrial"
    MATERIALS = "materials"
    UTILITIES = "utilities"
    REAL_ESTATE = "real_estate"
    TELECOMMUNICATIONS = "telecommunications"
    AEROSPACE_DEFENSE = "aerospace_defense"
    BIOTECHNOLOGY = "biotechnology"
    PHARMACEUTICALS = "pharmaceuticals"
    AUTOMOTIVE = "automotive"
    RETAIL = "retail"
    MEDIA_ENTERTAINMENT = "media_entertainment"
    SOFTWARE = "software"
    SEMICONDUCTORS = "semiconductors"
    BANKING = "banking"
    INSURANCE = "insurance"

class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"

class ImpactLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CRITICAL = "critical"

class NewsJobType(str, Enum):
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    PORTFOLIO_TRIGGERED = "portfolio_triggered"
    BREAKING_NEWS = "breaking_news"
    BACKFILL = "backfill"

class NewsJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class NewsAPIProvider(str, Enum):
    NEWSAPI = "newsapi"
    ALPHA_VANTAGE = "alpha_vantage"
    FINNHUB = "finnhub"
    YAHOO_FINANCE = "yahoo_finance"
    POLYGON = "polygon"
    MARKETAUX = "marketaux"

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"

class ContextType(str, Enum):
    DIRECT_MENTION = "direct_mention"
    SECTOR_RELATED = "sector_related"
    COMPETITOR = "competitor"
    MARKET_RELATED = "market_related"
    SUPPLY_CHAIN = "supply_chain"
    REGULATORY_IMPACT = "regulatory_impact"
    ECONOMIC_INDICATOR = "economic_indicator"

class NewsSourceType(str, Enum):
    FINANCIAL_NEWS = "financial_news"
    GENERAL_NEWS = "general_news"
    PRESS_RELEASE = "press_release"
    ANALYST_REPORT = "analyst_report"
    SOCIAL_MEDIA = "social_media"
    REGULATORY_FILING = "regulatory_filing"
    BLOG = "blog"
    PODCAST = "podcast"

class NewsLanguage(str, Enum):
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    IT = "it"
    PT = "pt"
    RU = "ru"
    ZH = "zh"
    JA = "ja"
    KO = "ko"

class NewsCountry(str, Enum):
    US = "us"
    GB = "gb"
    CA = "ca"
    AU = "au"
    DE = "de"
    FR = "fr"
    IT = "it"
    ES = "es"
    JP = "jp"
    KR = "kr"
    CN = "cn"
    IN = "in"
    BR = "br"
    MX = "mx"

class AlertType(str, Enum):
    BREAKING_NEWS = "breaking_news"
    PORTFOLIO_NEWS = "portfolio_news"
    SENTIMENT_CHANGE = "sentiment_change"
    HIGH_IMPACT = "high_impact"
    EARNINGS_ALERT = "earnings_alert"
    PRICE_MOVEMENT = "price_movement"
    VOLUME_SPIKE = "volume_spike"
    ANALYST_UPGRADE = "analyst_upgrade"
    ANALYST_DOWNGRADE = "analyst_downgrade"

class NotificationChannel(str, Enum):
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"
    SMS = "sms"
    WEBHOOK = "webhook"

# News base schemas
class NewsArticleBase(BaseModel):
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    url: str
    url_to_image: Optional[str] = None
    source_name: str
    source_id: Optional[str] = None
    author: Optional[str] = None
    published_at: datetime
    word_count: Optional[int] = None
    reading_time_minutes: Optional[int] = None
    language: Optional[NewsLanguage] = None
    country: Optional[NewsCountry] = None
    
    @validator('title')
    def validate_title(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Title cannot be empty')
        if len(v) > 500:
            raise ValueError('Title cannot exceed 500 characters')
        return v.strip()
    
    @validator('url')
    def validate_url(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('URL cannot be empty')
        if len(v) > 1000:
            raise ValueError('URL cannot exceed 1000 characters')
        # Basic URL validation
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v.strip()
    
    @validator('source_name')
    def validate_source_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Source name cannot be empty')
        if len(v) > 100:
            raise ValueError('Source name cannot exceed 100 characters')
        return v.strip()
    
    @validator('word_count')
    def validate_word_count(cls, v):
        if v is not None and v < 0:
            raise ValueError('Word count must be non-negative')
        return v
    
    @validator('reading_time_minutes')
    def validate_reading_time(cls, v):
        if v is not None and v < 0:
            raise ValueError('Reading time must be non-negative')
        return v

class NewsArticleCreate(NewsArticleBase):
    content_hash: str
    article_metadata: Optional[Dict[str, Any]] = None
    processing_metadata: Optional[Dict[str, Any]] = None
    
    @validator('content_hash')
    def validate_content_hash(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Content hash cannot be empty')
        if len(v) != 64:  # SHA-256 hash length
            raise ValueError('Content hash must be 64 characters long')
        return v.strip()

class NewsArticleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    url_to_image: Optional[str] = None
    author: Optional[str] = None
    word_count: Optional[int] = None
    reading_time_minutes: Optional[int] = None
    language: Optional[NewsLanguage] = None
    country: Optional[NewsCountry] = None
    article_metadata: Optional[Dict[str, Any]] = None
    processing_metadata: Optional[Dict[str, Any]] = None

class NewsArticle(NewsArticleBase):
    id: UUID
    content_hash: str
    article_metadata: Optional[Dict[str, Any]] = None
    processing_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# News category schemas
class NewsCategoryBase(BaseModel):
    category_type: NewsCategoryType
    category_value: str
    confidence_score: Optional[Decimal] = None
    
    @validator('category_value')
    def validate_category_value(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Category value cannot be empty')
        if len(v) > 100:
            raise ValueError('Category value cannot exceed 100 characters')
        return v.strip().lower()
    
    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        if v is not None:
            if not 0.0 <= v <= 1.0:
                raise ValueError('Confidence score must be between 0.0 and 1.0')
        return v

class NewsCategoryCreate(NewsCategoryBase):
    article_id: UUID

class NewsCategory(NewsCategoryBase):
    id: UUID
    article_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

# News sentiment schemas
class NewsSentimentBase(BaseModel):
    sentiment: SentimentType
    sentiment_score: Optional[Decimal] = None
    confidence_score: Optional[Decimal] = None
    impact_level: Optional[ImpactLevel] = None
    keywords: Optional[Dict[str, Any]] = None
    
    @validator('sentiment_score')
    def validate_sentiment_score(cls, v):
        if v is not None:
            if not -1.0 <= v <= 1.0:
                raise ValueError('Sentiment score must be between -1.0 and 1.0')
        return v
    
    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        if v is not None:
            if not 0.0 <= v <= 1.0:
                raise ValueError('Confidence score must be between 0.0 and 1.0')
        return v
    
    @validator('keywords')
    def validate_keywords(cls, v):
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Keywords must be a dictionary')
            for key, value in v.items():
                if not isinstance(key, str):
                    raise ValueError('Keyword keys must be strings')
                if not isinstance(value, (int, float)):
                    raise ValueError('Keyword values must be numeric')
        return v

class NewsSentimentCreate(NewsSentimentBase):
    article_id: UUID

class NewsSentiment(NewsSentimentBase):
    id: UUID
    article_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

# Stock news relevance schemas
class StockNewsRelevanceBase(BaseModel):
    symbol: str
    relevance_score: Decimal
    mention_count: Optional[int] = 1
    context_type: Optional[ContextType] = None
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Symbol cannot be empty')
        if len(v) > 20:
            raise ValueError('Symbol cannot exceed 20 characters')
        # Convert to uppercase for consistency
        return v.strip().upper()
    
    @validator('relevance_score')
    def validate_relevance_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Relevance score must be between 0.0 and 1.0')
        return v
    
    @validator('mention_count')
    def validate_mention_count(cls, v):
        if v is not None and v < 1:
            raise ValueError('Mention count must be at least 1')
        return v

class StockNewsRelevanceCreate(StockNewsRelevanceBase):
    article_id: UUID

class StockNewsRelevance(StockNewsRelevanceBase):
    id: UUID
    article_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

# News source schemas
class NewsSourceBase(BaseModel):
    source_id: str
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    category: Optional[NewsSourceType] = None
    language: Optional[NewsLanguage] = None
    country: Optional[NewsCountry] = None
    quality_score: Optional[Decimal] = Decimal('0.50')
    is_active: Optional[bool] = True
    api_provider: Optional[NewsAPIProvider] = None
    
    @validator('source_id')
    def validate_source_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Source ID cannot be empty')
        if len(v) > 50:
            raise ValueError('Source ID cannot exceed 50 characters')
        return v.strip()
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Source name cannot be empty')
        if len(v) > 100:
            raise ValueError('Source name cannot exceed 100 characters')
        return v.strip()
    
    @validator('url')
    def validate_url(cls, v):
        if v is not None and v.strip():
            if len(v) > 500:
                raise ValueError('URL cannot exceed 500 characters')
            if not v.startswith(('http://', 'https://')):
                raise ValueError('URL must start with http:// or https://')
            return v.strip()
        return v
    
    @validator('quality_score')
    def validate_quality_score(cls, v):
        if v is not None:
            if not 0.0 <= v <= 1.0:
                raise ValueError('Quality score must be between 0.0 and 1.0')
        return v

class NewsSourceCreate(NewsSourceBase):
    pass

class NewsSourceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    category: Optional[NewsSourceType] = None
    language: Optional[NewsLanguage] = None
    country: Optional[NewsCountry] = None
    quality_score: Optional[Decimal] = None
    is_active: Optional[bool] = None
    api_provider: Optional[NewsAPIProvider] = None

class NewsSource(NewsSourceBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# User news preferences schemas
class UserNewsPreferencesBase(BaseModel):
    categories: Optional[Dict[str, Any]] = None
    sources: Optional[Dict[str, Any]] = None
    sentiment_threshold: Optional[Decimal] = Decimal('0.30')
    impact_threshold: Optional[ImpactLevel] = ImpactLevel.MEDIUM
    notification_settings: Optional[Dict[str, Any]] = None
    refresh_frequency: Optional[int] = 60
    
    @validator('sentiment_threshold')
    def validate_sentiment_threshold(cls, v):
        if v is not None:
            if not 0.0 <= v <= 1.0:
                raise ValueError('Sentiment threshold must be between 0.0 and 1.0')
        return v
    
    @validator('refresh_frequency')
    def validate_refresh_frequency(cls, v):
        if v is not None:
            if v < 5 or v > 1440:  # 5 minutes to 24 hours
                raise ValueError('Refresh frequency must be between 5 and 1440 minutes')
        return v
    
    @validator('categories')
    def validate_categories(cls, v):
        if v is not None:
            # Validate that it's a proper CategoryPreferences structure
            try:
                CategoryPreferences(**v)
            except Exception as e:
                raise ValueError(f'Invalid categories format: {e}')
        return v
    
    @validator('sources')
    def validate_sources(cls, v):
        if v is not None:
            # Validate that it's a proper SourcePreferences structure
            try:
                SourcePreferences(**v)
            except Exception as e:
                raise ValueError(f'Invalid sources format: {e}')
        return v
    
    @validator('notification_settings')
    def validate_notification_settings(cls, v):
        if v is not None:
            # Validate that it's a proper NotificationSettings structure
            try:
                NotificationSettings(**v)
            except Exception as e:
                raise ValueError(f'Invalid notification settings format: {e}')
        return v

class UserNewsPreferencesCreate(UserNewsPreferencesBase):
    user_id: UUID

class UserNewsPreferencesUpdate(UserNewsPreferencesBase):
    pass

class UserNewsPreferences(UserNewsPreferencesBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# News fetch job schemas
class NewsFetchJobBase(BaseModel):
    job_type: NewsJobType
    symbols: Optional[List[str]] = None
    api_provider: Optional[NewsAPIProvider] = None

class NewsFetchJobCreate(NewsFetchJobBase):
    user_id: Optional[UUID] = None
    portfolio_id: Optional[UUID] = None

class NewsFetchJobUpdate(BaseModel):
    status: Optional[NewsJobStatus] = None
    articles_fetched: Optional[int] = None
    api_calls_made: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class NewsFetchJob(NewsFetchJobBase):
    id: UUID
    user_id: Optional[UUID] = None
    portfolio_id: Optional[UUID] = None
    status: NewsJobStatus
    articles_fetched: int
    api_calls_made: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Complex news schemas with relationships
class ProcessedNewsArticle(NewsArticle):
    categories: List[NewsCategory] = []
    sentiment: Optional[NewsSentiment] = None
    stock_relevance: List[StockNewsRelevance] = []

class NewsListResponse(BaseModel):
    articles: List[ProcessedNewsArticle]
    total_count: int
    page: int
    page_size: int
    filters_applied: Dict[str, Any]

class NewsCategoriesResponse(BaseModel):
    primary_categories: Dict[str, int]
    sector_categories: Dict[str, int]
    custom_categories: Dict[str, int]

class NewsAnalyticsResponse(BaseModel):
    sentiment_distribution: Dict[str, int]
    impact_distribution: Dict[str, int]
    trending_topics: List[str]
    most_mentioned_stocks: List[Dict[str, Any]]
    news_volume_trend: List[Dict[str, Any]]
    top_sources: List[Dict[str, Any]]

# News alert schemas
class NewsAlertBase(BaseModel):
    alert_type: str
    severity: AlertSeverity
    title: str
    message: str
    symbols: List[str]
    sentiment: Optional[SentimentType] = None
    impact_level: Optional[ImpactLevel] = None

class NewsAlertCreate(NewsAlertBase):
    article_id: UUID
    user_id: UUID

class NewsAlert(NewsAlertBase):
    id: UUID
    article_id: UUID
    user_id: UUID
    created_at: datetime
    is_read: bool = False
    
    class Config:
        from_attributes = True

# News filter and search schemas
class NewsFilterRequest(BaseModel):
    symbols: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    sentiment: Optional[List[SentimentType]] = None
    impact_level: Optional[List[ImpactLevel]] = None
    sources: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search_query: Optional[str] = None
    page: Optional[int] = 1
    page_size: Optional[int] = 50

class NewsRefreshRequest(BaseModel):
    symbols: Optional[List[str]] = None
    force_refresh: Optional[bool] = False
    priority: Optional[str] = "normal"

# Validation for JSONB fields
class NewsKeywords(BaseModel):
    keywords: Dict[str, float]  # keyword -> weight/score
    
    @validator('keywords')
    def validate_keywords(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Keywords must be a dictionary')
        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError('Keyword keys must be strings')
            if not isinstance(value, (int, float)):
                raise ValueError('Keyword values must be numeric')
            if not 0.0 <= value <= 1.0:
                raise ValueError('Keyword weights must be between 0.0 and 1.0')
        return v

class NotificationSettings(BaseModel):
    email_enabled: bool = True
    push_enabled: bool = True
    in_app_enabled: bool = True
    sms_enabled: bool = False
    webhook_enabled: bool = False
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
    min_impact_level: ImpactLevel = ImpactLevel.MEDIUM
    max_alerts_per_hour: int = 10
    max_alerts_per_day: int = 100
    channels: List[NotificationChannel] = [NotificationChannel.EMAIL, NotificationChannel.IN_APP]
    
    @validator('max_alerts_per_hour')
    def validate_hourly_limit(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Hourly alert limit must be between 1 and 100')
        return v
    
    @validator('max_alerts_per_day')
    def validate_daily_limit(cls, v):
        if v < 1 or v > 1000:
            raise ValueError('Daily alert limit must be between 1 and 1000')
        return v

class CategoryPreferences(BaseModel):
    primary_categories: Dict[str, float] = {}  # Using string keys for flexibility
    sector_categories: Dict[str, float] = {}
    custom_categories: Dict[str, float] = {}
    
    @validator('primary_categories', 'sector_categories', 'custom_categories')
    def validate_weights(cls, v):
        for category, weight in v.items():
            if not isinstance(category, str):
                raise ValueError('Category keys must be strings')
            if not isinstance(weight, (int, float)):
                raise ValueError('Category weights must be numeric')
            if not 0.0 <= weight <= 1.0:
                raise ValueError('Category weights must be between 0.0 and 1.0')
        return v

class SourcePreferences(BaseModel):
    enabled_sources: List[str] = []
    disabled_sources: List[str] = []
    source_weights: Dict[str, float] = {}
    
    @validator('source_weights')
    def validate_source_weights(cls, v):
        for source, weight in v.items():
            if not isinstance(source, str):
                raise ValueError('Source keys must be strings')
            if not isinstance(weight, (int, float)):
                raise ValueError('Source weights must be numeric')
            if not 0.0 <= weight <= 1.0:
                raise ValueError('Source weights must be between 0.0 and 1.0')
        return v

class NewsArticleMetadata(BaseModel):
    """Validation schema for news article JSONB metadata fields"""
    word_count: Optional[int] = None
    reading_time_minutes: Optional[int] = None
    language_detected: Optional[NewsLanguage] = None
    entities_mentioned: Optional[List[str]] = []
    topics: Optional[List[str]] = []
    geographic_focus: Optional[List[NewsCountry]] = []
    
    @validator('word_count')
    def validate_word_count(cls, v):
        if v is not None and v < 0:
            raise ValueError('Word count must be non-negative')
        return v
    
    @validator('reading_time_minutes')
    def validate_reading_time(cls, v):
        if v is not None and v < 0:
            raise ValueError('Reading time must be non-negative')
        return v

class NewsProcessingMetadata(BaseModel):
    """Validation schema for news processing metadata"""
    processing_version: str
    processed_at: datetime
    sentiment_model_version: Optional[str] = None
    categorization_model_version: Optional[str] = None
    relevance_model_version: Optional[str] = None
    processing_time_ms: Optional[int] = None
    
    @validator('processing_time_ms')
    def validate_processing_time(cls, v):
        if v is not None and v < 0:
            raise ValueError('Processing time must be non-negative')
        return v 