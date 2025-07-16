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