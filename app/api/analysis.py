"""
Analysis API endpoints with integrated analysis service
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import asyncio
from datetime import datetime

from app.database import get_db
from app.services.database_service import DatabaseService
from app.services.analysis_service import AnalysisService
from app import schemas

router = APIRouter()

def get_db_service(db: Session = Depends(get_db)) -> DatabaseService:
    return DatabaseService(db)

def get_analysis_service(db: Session = Depends(get_db)) -> AnalysisService:
    return AnalysisService(db)

async def run_portfolio_analysis_background(
    portfolio_id: str,
    session_id: UUID,
    analysis_request: schemas.AnalysisRequest,
    db_service: DatabaseService,
    analysis_service: AnalysisService
):
    """Background task to run portfolio analysis using existing analysis system"""
    try:
        # Update session status to running and commit immediately
        session_update = schemas.AnalysisSessionUpdate(
            status=schemas.AnalysisStatus.RUNNING
        )
        db_service.update_analysis_session(session_id, session_update)
        
        # Commit the status change immediately so it's visible to progress polling
        db_service.db.commit()
        
        # Run the actual analysis using the existing session
        result = analysis_service.run_portfolio_analysis(
            portfolio_id=str(portfolio_id),
            analysis_type=analysis_request.analysis_type,
            include_pdf=True,
            user_id=None,  # TODO: Get from authentication context
            existing_session_id=str(session_id),  # Use existing session
            force_refresh=analysis_request.force_refresh  # Pass force refresh parameter
        )
        
        if "error" in result:
            # Update session as failed and commit immediately
            session_update = schemas.AnalysisSessionUpdate(
                status=schemas.AnalysisStatus.FAILED,
                completed_at=datetime.utcnow(),
                error_message=result["error"]
            )
        else:
            # Update session as completed and commit immediately
            session_update = schemas.AnalysisSessionUpdate(
                status=schemas.AnalysisStatus.COMPLETED,
                completed_at=datetime.utcnow(),
                execution_time_ms=5000,  # TODO: Track actual execution time
                api_calls_made=10,  # TODO: Track actual API calls
                cache_hits=5,  # TODO: Track actual cache hits
                cost_estimate=0.15,  # TODO: Calculate actual cost
                report_path=f"reports/portfolio_{portfolio_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
        
        db_service.update_analysis_session(session_id, session_update)
        # Commit the final status immediately
        db_service.db.commit()
        
    except Exception as e:
        # Update session as failed and commit immediately
        session_update = schemas.AnalysisSessionUpdate(
            status=schemas.AnalysisStatus.FAILED,
            completed_at=datetime.utcnow(),
            error_message=str(e)
        )
        db_service.update_analysis_session(session_id, session_update)
        # Commit the error status immediately
        db_service.db.commit()

@router.post("/run", response_model=schemas.AnalysisSession, status_code=status.HTTP_202_ACCEPTED)
async def run_analysis(
    analysis_request: schemas.AnalysisRequest,
    background_tasks: BackgroundTasks,
    db_service: DatabaseService = Depends(get_db_service),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """Start portfolio analysis"""
    # Check if portfolio exists
    portfolio = db_service.get_portfolio(analysis_request.portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Create analysis session
    session_create = schemas.AnalysisSessionCreate(
        portfolio_id=analysis_request.portfolio_id,
        analysis_type=analysis_request.analysis_type,
        status=schemas.AnalysisStatus.PENDING
    )
    session = db_service.create_analysis_session(session_create)
    
    # Start background task
    background_tasks.add_task(
        run_portfolio_analysis_background,
        analysis_request.portfolio_id,
        session.id,
        analysis_request,
        db_service,
        analysis_service
    )
    
    return session

@router.post("/portfolios/{portfolio_id}/run-sync")
def run_portfolio_analysis_sync(
    portfolio_id: UUID,
    analysis_type: str = "comprehensive",
    include_pdf: bool = True,
    user_id: Optional[str] = None,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """Run comprehensive portfolio analysis synchronously"""
    result = analysis_service.run_portfolio_analysis(
        portfolio_id=str(portfolio_id),
        analysis_type=analysis_type,
        include_pdf=include_pdf,
        user_id=user_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.post("/stocks/{symbol}/run")
def run_single_stock_analysis(
    symbol: str,
    portfolio_id: Optional[UUID] = None,
    user_id: Optional[str] = None,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """Run analysis for a single stock"""
    result = analysis_service.run_single_stock_analysis(
        symbol=symbol,
        portfolio_id=str(portfolio_id) if portfolio_id else None,
        user_id=user_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.get("/sessions/{session_id}", response_model=schemas.AnalysisSession)
async def get_analysis_session(
    session_id: UUID,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Get analysis session by ID"""
    session = db_service.get_analysis_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis session not found"
        )
    return session

@router.get("/sessions/{session_id}/progress")
async def get_session_progress(
    session_id: UUID,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """Get real-time progress for an analysis session"""
    progress = analysis_service.get_session_progress(str(session_id))
    if "error" in progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=progress["error"]
        )
    return progress

@router.get("/portfolio/{portfolio_id}/sessions", response_model=List[schemas.AnalysisSession])
async def get_portfolio_analysis_sessions(
    portfolio_id: UUID,
    limit: int = 20,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Get analysis sessions for a portfolio"""
    portfolio = db_service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    return db_service.get_portfolio_analysis_sessions(portfolio_id, limit)

@router.get("/portfolios/{portfolio_id}/history")
def get_portfolio_analysis_history(
    portfolio_id: UUID,
    limit: int = 10,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """Get analysis history for a portfolio"""
    return analysis_service.get_portfolio_analysis_history(str(portfolio_id), limit)

@router.get("/market-status")
def get_market_status(analysis_service: AnalysisService = Depends(get_analysis_service)):
    """Get current market status for analysis timing"""
    return analysis_service.get_market_status()

@router.post("/cache/clean")
async def clean_cache(
    db_service: DatabaseService = Depends(get_db_service)
):
    """Clean expired cache entries"""
    expired_count = db_service.clean_expired_cache()
    return {"message": f"Cleaned {expired_count} expired cache entries", "expired_count": expired_count}

@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics for monitoring data freshness"""
    try:
        from cache_manager import CacheManager
        cache_manager = CacheManager()
        stats = cache_manager.get_cache_stats()
        return stats
    except Exception as e:
        return {
            "error": str(e),
            "total_entries": 0,
            "total_size_mb": 0,
            "expired_entries": 0,
            "current_market_session": "unknown",
            "by_type": {}
        } 