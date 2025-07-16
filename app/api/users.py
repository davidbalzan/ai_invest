"""
User API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from passlib.context import CryptContext

from app.database import get_db
from app.services.database_service import DatabaseService
from app import schemas

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_service(db: Session = Depends(get_db)) -> DatabaseService:
    return DatabaseService(db)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: schemas.UserCreate,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Create a new user"""
    # Check if username exists
    if db_service.get_user_by_username(user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )
    
    # Check if email exists
    if db_service.get_user_by_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists"
        )
    
    hashed_password = hash_password(user.password)
    return db_service.create_user(user, hashed_password)

@router.get("/{user_id}", response_model=schemas.User)
async def get_user(
    user_id: UUID,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Get user by ID"""
    user = db_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/{user_id}", response_model=schemas.User)
async def update_user(
    user_id: UUID,
    user_update: schemas.UserUpdate,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Update user"""
    user = db_service.update_user(user_id, user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.get("/{user_id}/portfolios", response_model=List[schemas.Portfolio])
async def get_user_portfolios(
    user_id: UUID,
    include_inactive: bool = False,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Get all portfolios for a user"""
    # Check if user exists
    user = db_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return db_service.get_user_portfolios(user_id, include_inactive) 