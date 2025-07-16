"""
Portfolio API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.services.database_service import DatabaseService
from app import schemas

router = APIRouter()

def get_db_service(db: Session = Depends(get_db)) -> DatabaseService:
    """Get database service"""
    return DatabaseService(db)

@router.get("/", response_model=List[schemas.Portfolio])
async def get_portfolios(
    user_id: UUID,
    include_inactive: bool = False,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Get all portfolios for a user"""
    portfolios = db_service.get_user_portfolios(user_id, include_inactive)
    return portfolios

@router.post("/", response_model=schemas.Portfolio, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio: schemas.PortfolioCreate,
    user_id: UUID,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Create a new portfolio"""
    # Check if user exists
    user = db_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return db_service.create_portfolio(portfolio, user_id)

@router.get("/{portfolio_id}", response_model=schemas.Portfolio)
async def get_portfolio(
    portfolio_id: UUID,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Get portfolio by ID"""
    portfolio = db_service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    return portfolio

@router.put("/{portfolio_id}", response_model=schemas.Portfolio)
async def update_portfolio(
    portfolio_id: UUID,
    portfolio_update: schemas.PortfolioUpdate,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Update portfolio"""
    portfolio = db_service.update_portfolio(portfolio_id, portfolio_update)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    return portfolio

@router.get("/{portfolio_id}/summary", response_model=schemas.PortfolioSummary)
async def get_portfolio_summary(
    portfolio_id: UUID,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Get comprehensive portfolio summary"""
    summary = db_service.get_portfolio_summary(portfolio_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    return summary

@router.get("/{portfolio_id}/holdings", response_model=List[schemas.Holding])
async def get_portfolio_holdings(
    portfolio_id: UUID,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Get all holdings for a portfolio"""
    # Check if portfolio exists
    portfolio = db_service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    return db_service.get_portfolio_holdings(portfolio_id)

@router.post("/{portfolio_id}/holdings", response_model=schemas.Holding, status_code=status.HTTP_201_CREATED)
async def create_holding(
    portfolio_id: UUID,
    holding: schemas.HoldingBase,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Create a new holding in portfolio"""
    # Check if portfolio exists
    portfolio = db_service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Check if holding already exists
    existing = db_service.get_holding_by_symbol(portfolio_id, holding.symbol)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Holding for {holding.symbol} already exists in this portfolio"
        )
    
    holding_create = schemas.HoldingCreate(**holding.dict(), portfolio_id=portfolio_id)
    return db_service.create_holding(holding_create)

@router.put("/{portfolio_id}/holdings/{holding_id}", response_model=schemas.Holding)
async def update_holding(
    portfolio_id: UUID,
    holding_id: UUID,
    holding_update: schemas.HoldingUpdate,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Update a holding"""
    # Verify holding belongs to portfolio
    holding = db_service.get_holding(holding_id)
    if not holding or holding.portfolio_id != portfolio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holding not found in this portfolio"
        )
    
    updated_holding = db_service.update_holding(holding_id, holding_update)
    if not updated_holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holding not found"
        )
    return updated_holding

@router.delete("/{portfolio_id}/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holding(
    portfolio_id: UUID,
    holding_id: UUID,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Delete a holding"""
    # Verify holding belongs to portfolio
    holding = db_service.get_holding(holding_id)
    if not holding or holding.portfolio_id != portfolio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holding not found in this portfolio"
        )
    
    success = db_service.delete_holding(holding_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holding not found"
        )

@router.get("/{portfolio_id}/transactions", response_model=List[schemas.Transaction])
async def get_portfolio_transactions(
    portfolio_id: UUID,
    limit: int = 100,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Get transactions for a portfolio"""
    # Check if portfolio exists
    portfolio = db_service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    return db_service.get_portfolio_transactions(portfolio_id, limit)

@router.get("/{portfolio_id}/analysis-sessions", response_model=List[schemas.AnalysisSession])
async def get_portfolio_analysis_sessions(
    portfolio_id: UUID,
    limit: int = 20,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Get analysis sessions for a portfolio"""
    # Check if portfolio exists
    portfolio = db_service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    return db_service.get_portfolio_analysis_sessions(portfolio_id, limit) 