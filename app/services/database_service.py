"""
Database service layer for CRUD operations
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, and_, or_
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal

from app import models, schemas
from app.database import get_db
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service class for database operations"""
    
    def __init__(self, db: Session):
        self.db = db

    # User operations
    def get_user(self, user_id: UUID) -> Optional[models.User]:
        """Get user by ID"""
        return self.db.query(models.User).filter(models.User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[models.User]:
        """Get user by username"""
        return self.db.query(models.User).filter(models.User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[models.User]:
        """Get user by email"""
        return self.db.query(models.User).filter(models.User.email == email).first()
    
    def create_user(self, user: schemas.UserCreate, password_hash: str) -> models.User:
        """Create new user"""
        db_user = models.User(
            username=user.username,
            email=user.email,
            password_hash=password_hash,
            first_name=user.first_name,
            last_name=user.last_name,
            timezone=user.timezone
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update_user(self, user_id: UUID, user_update: schemas.UserUpdate) -> Optional[models.User]:
        """Update user"""
        db_user = self.get_user(user_id)
        if not db_user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    # Portfolio operations
    def get_portfolio(self, portfolio_id: UUID) -> Optional[models.Portfolio]:
        """Get portfolio by ID"""
        return self.db.query(models.Portfolio).filter(models.Portfolio.id == portfolio_id).first()
    
    def get_user_portfolios(self, user_id: UUID, include_inactive: bool = False) -> List[models.Portfolio]:
        """Get all portfolios for a user"""
        query = self.db.query(models.Portfolio).filter(models.Portfolio.user_id == user_id)
        if not include_inactive:
            query = query.filter(models.Portfolio.is_active == True)
        return query.order_by(models.Portfolio.created_at).all()
    
    def create_portfolio(self, portfolio: schemas.PortfolioCreate, user_id: UUID) -> models.Portfolio:
        """Create new portfolio"""
        db_portfolio = models.Portfolio(
            user_id=user_id,
            name=portfolio.name,
            description=portfolio.description,
            cash_balance=portfolio.cash_balance or Decimal('0.00'),
            # Strategy and Risk Management
            strategy=portfolio.strategy,
            risk_level=portfolio.risk_level,
            max_position_percent=portfolio.max_position_percent,
            stop_loss_percent=portfolio.stop_loss_percent,
            take_profit_percent=portfolio.take_profit_percent,
            daily_loss_limit=portfolio.daily_loss_limit,
            rebalance_frequency=portfolio.rebalance_frequency
        )
        self.db.add(db_portfolio)
        self.db.commit()
        self.db.refresh(db_portfolio)
        return db_portfolio
    
    def update_portfolio(self, portfolio_id: UUID, portfolio_update: schemas.PortfolioUpdate) -> Optional[models.Portfolio]:
        """Update portfolio"""
        db_portfolio = self.get_portfolio(portfolio_id)
        if not db_portfolio:
            return None
        
        update_data = portfolio_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_portfolio, field, value)
        
        self.db.commit()
        self.db.refresh(db_portfolio)
        return db_portfolio

    # Holding operations
    def get_holding(self, holding_id: UUID) -> Optional[models.Holding]:
        """Get holding by ID"""
        return self.db.query(models.Holding).filter(models.Holding.id == holding_id).first()
    
    def get_portfolio_holdings(self, portfolio_id: UUID) -> List[models.Holding]:
        """Get all holdings for a portfolio"""
        return self.db.query(models.Holding).filter(
            models.Holding.portfolio_id == portfolio_id
        ).order_by(models.Holding.symbol).all()
    
    def get_holding_by_symbol(self, portfolio_id: UUID, symbol: str) -> Optional[models.Holding]:
        """Get holding by portfolio and symbol"""
        return self.db.query(models.Holding).filter(
            and_(
                models.Holding.portfolio_id == portfolio_id,
                models.Holding.symbol == symbol
            )
        ).first()
    
    def create_holding(self, holding: schemas.HoldingCreate) -> models.Holding:
        """Create new holding"""
        db_holding = models.Holding(
            portfolio_id=holding.portfolio_id,
            symbol=holding.symbol.upper(),
            company_name=holding.company_name,
            shares=holding.shares,
            average_cost=holding.average_cost,
            sector=holding.sector,
            industry=holding.industry
        )
        self.db.add(db_holding)
        self.db.commit()
        self.db.refresh(db_holding)
        return db_holding
    
    def update_holding(self, holding_id: UUID, holding_update: schemas.HoldingUpdate) -> Optional[models.Holding]:
        """Update holding"""
        db_holding = self.get_holding(holding_id)
        if not db_holding:
            return None
        
        update_data = holding_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_holding, field, value)
        
        self.db.commit()
        self.db.refresh(db_holding)
        return db_holding
    
    def delete_holding(self, holding_id: UUID) -> bool:
        """Delete holding"""
        db_holding = self.get_holding(holding_id)
        if not db_holding:
            return False
        
        self.db.delete(db_holding)
        self.db.commit()
        return True

    # Transaction operations
    def get_transaction(self, transaction_id: UUID) -> Optional[models.Transaction]:
        """Get transaction by ID"""
        return self.db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    
    def get_portfolio_transactions(self, portfolio_id: UUID, limit: int = 100) -> List[models.Transaction]:
        """Get transactions for a portfolio"""
        return self.db.query(models.Transaction).filter(
            models.Transaction.portfolio_id == portfolio_id
        ).order_by(desc(models.Transaction.transaction_date)).limit(limit).all()
    
    def get_symbol_transactions(self, portfolio_id: UUID, symbol: str) -> List[models.Transaction]:
        """Get transactions for a specific symbol in a portfolio"""
        return self.db.query(models.Transaction).filter(
            and_(
                models.Transaction.portfolio_id == portfolio_id,
                models.Transaction.symbol == symbol.upper()
            )
        ).order_by(desc(models.Transaction.transaction_date)).all()
    
    def create_transaction(self, transaction: schemas.TransactionCreate) -> models.Transaction:
        """Create new transaction"""
        db_transaction = models.Transaction(
            portfolio_id=transaction.portfolio_id,
            symbol=transaction.symbol.upper(),
            transaction_type=transaction.transaction_type,
            shares=transaction.shares,
            price=transaction.price,
            total_amount=transaction.total_amount,
            fees=transaction.fees,
            transaction_date=transaction.transaction_date,
            settlement_date=transaction.settlement_date,
            notes=transaction.notes,
            external_reference=transaction.external_reference
        )
        self.db.add(db_transaction)
        self.db.commit()
        self.db.refresh(db_transaction)
        return db_transaction

    # Analysis Session operations
    def get_analysis_session(self, session_id: UUID) -> Optional[models.AnalysisSession]:
        """Get analysis session by ID"""
        return self.db.query(models.AnalysisSession).filter(models.AnalysisSession.id == session_id).first()
    
    def get_portfolio_analysis_sessions(self, portfolio_id: UUID, limit: int = 20) -> List[models.AnalysisSession]:
        """Get analysis sessions for a portfolio"""
        return self.db.query(models.AnalysisSession).filter(
            models.AnalysisSession.portfolio_id == portfolio_id
        ).order_by(desc(models.AnalysisSession.started_at)).limit(limit).all()
    
    def create_analysis_session(self, session: schemas.AnalysisSessionCreate) -> models.AnalysisSession:
        """Create new analysis session"""
        db_session = models.AnalysisSession(
            portfolio_id=session.portfolio_id,
            analysis_type=session.analysis_type,
            status=session.status
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session
    
    def update_analysis_session(self, session_id: UUID, session_update: schemas.AnalysisSessionUpdate) -> Optional[models.AnalysisSession]:
        """Update analysis session"""
        db_session = self.get_analysis_session(session_id)
        if not db_session:
            return None
        
        update_data = session_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_session, field, value)
        
        self.db.commit()
        self.db.refresh(db_session)
        return db_session
    
    def get_analysis_sessions(self, portfolio_id: Optional[UUID] = None, user_id: Optional[UUID] = None, limit: int = 20) -> List[models.AnalysisSession]:
        """Get analysis sessions with optional filtering"""
        query = self.db.query(models.AnalysisSession)
        
        if portfolio_id:
            query = query.filter(models.AnalysisSession.portfolio_id == portfolio_id)
        if user_id:
            query = query.filter(models.AnalysisSession.user_id == user_id)
        
        return query.order_by(desc(models.AnalysisSession.started_at)).limit(limit).all()

    # Cache operations
    def get_stock_data_cache(self, cache_key: str) -> Optional[models.StockDataCache]:
        """Get stock data from cache"""
        return self.db.query(models.StockDataCache).filter(
            and_(
                models.StockDataCache.cache_key == cache_key,
                models.StockDataCache.expires_at > datetime.utcnow()
            )
        ).first()
    
    def set_stock_data_cache(self, cache_key: str, symbol: str, data_type: str, 
                           data: Dict[str, Any], expires_at: datetime, 
                           market_session: str = None) -> models.StockDataCache:
        """Set stock data in cache"""
        # Check if exists and update, otherwise create
        existing = self.db.query(models.StockDataCache).filter(
            models.StockDataCache.cache_key == cache_key
        ).first()
        
        if existing:
            existing.data = data
            existing.expires_at = expires_at
            existing.accessed_at = datetime.utcnow()
            existing.access_count += 1
            existing.market_session = market_session
            db_cache = existing
        else:
            db_cache = models.StockDataCache(
                cache_key=cache_key,
                symbol=symbol.upper(),
                data_type=data_type,
                data=data,
                expires_at=expires_at,
                market_session=market_session
            )
            self.db.add(db_cache)
        
        self.db.commit()
        self.db.refresh(db_cache)
        return db_cache
    
    def clean_expired_cache(self) -> int:
        """Clean expired cache entries"""
        expired_count = self.db.query(models.StockDataCache).filter(
            models.StockDataCache.expires_at <= datetime.utcnow()
        ).delete()
        
        expired_count += self.db.query(models.NewsSentimentCache).filter(
            models.NewsSentimentCache.expires_at <= datetime.utcnow()
        ).delete()
        
        expired_count += self.db.query(models.AIAnalysisCache).filter(
            models.AIAnalysisCache.expires_at <= datetime.utcnow()
        ).delete()
        
        self.db.commit()
        return expired_count

    # Portfolio statistics
    def calculate_portfolio_value(self, portfolio_id: UUID) -> Decimal:
        """Calculate total portfolio value"""
        holdings = self.get_portfolio_holdings(portfolio_id)
        total_value = Decimal('0.00')
        
        for holding in holdings:
            if holding.market_value:
                total_value += holding.market_value
        
        portfolio = self.get_portfolio(portfolio_id)
        if portfolio and portfolio.cash_balance:
            total_value += portfolio.cash_balance
        
        return total_value
    
    def get_portfolio_summary(self, portfolio_id: UUID) -> Optional[schemas.PortfolioSummary]:
        """Get comprehensive portfolio summary"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None
        
        holdings = self.get_portfolio_holdings(portfolio_id)
        transactions = self.get_portfolio_transactions(portfolio_id, limit=10)
        
        total_value = self.calculate_portfolio_value(portfolio_id)
        total_gain_loss = total_value - sum(h.shares * h.average_cost for h in holdings if h.shares and h.average_cost)
        
        # Calculate gain/loss percentage
        total_cost = sum(h.shares * h.average_cost for h in holdings if h.shares and h.average_cost)
        total_gain_loss_percent = (total_gain_loss / total_cost * 100) if total_cost > 0 else Decimal('0.00')
        
        # Top and worst performers
        performers = sorted(holdings, key=lambda h: h.unrealized_gain_loss_percent or 0, reverse=True)
        top_performers = performers[:3] if len(performers) >= 3 else performers
        worst_performers = performers[-3:] if len(performers) >= 3 else []
        
        # Sector allocation
        sector_allocation = {}
        for holding in holdings:
            if holding.sector and holding.market_value:
                sector_allocation[holding.sector] = sector_allocation.get(holding.sector, Decimal('0.00')) + holding.market_value
        
        return schemas.PortfolioSummary(
            portfolio=portfolio,
            total_holdings=len(holdings),
            total_value=total_value,
            total_gain_loss=total_gain_loss,
            total_gain_loss_percent=total_gain_loss_percent,
            top_performers=top_performers,
            worst_performers=worst_performers,
            sector_allocation=sector_allocation,
            recent_transactions=transactions
        )

def get_database_service(db: Session = None) -> DatabaseService:
    """Get database service instance"""
    if db is None:
        db = next(get_db())
    return DatabaseService(db) 