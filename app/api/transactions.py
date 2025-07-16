"""
Transaction API endpoints
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
    return DatabaseService(db)

@router.post("/", response_model=schemas.Transaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: schemas.TransactionCreate,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Create a new transaction"""
    # Check if portfolio exists
    portfolio = db_service.get_portfolio(transaction.portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    return db_service.create_transaction(transaction)

@router.get("/{transaction_id}", response_model=schemas.Transaction)
async def get_transaction(
    transaction_id: UUID,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Get transaction by ID"""
    transaction = db_service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return transaction

@router.get("/portfolio/{portfolio_id}", response_model=List[schemas.Transaction])
async def get_portfolio_transactions(
    portfolio_id: UUID,
    limit: int = 100,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Get transactions for a portfolio"""
    portfolio = db_service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    return db_service.get_portfolio_transactions(portfolio_id, limit)

@router.get("/portfolio/{portfolio_id}/symbol/{symbol}", response_model=List[schemas.Transaction])
async def get_symbol_transactions(
    portfolio_id: UUID,
    symbol: str,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Get transactions for a specific symbol"""
    portfolio = db_service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    return db_service.get_symbol_transactions(portfolio_id, symbol) 