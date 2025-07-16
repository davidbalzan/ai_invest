"""
Web routes for HTML interface
"""
from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import os

from app.database import get_db
from app.services.database_service import DatabaseService
from app.services.analysis_service import AnalysisService

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db_service(db: Session = Depends(get_db)) -> DatabaseService:
    return DatabaseService(db)

def get_analysis_service(db: Session = Depends(get_db)) -> AnalysisService:
    return AnalysisService(db)

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user_id: Optional[str] = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",  # Default user ID
    db_service: DatabaseService = Depends(get_db_service)
):
    """Main dashboard"""
    try:
        user_uuid = UUID(user_id)
        user = db_service.get_user(user_uuid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        portfolios = db_service.get_user_portfolios(user_uuid)
        
        # Get summary for first portfolio if exists
        portfolio_summary = None
        if portfolios:
            portfolio_summary = db_service.get_portfolio_summary(portfolios[0].id)
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user": user,
            "portfolios": portfolios,
            "portfolio_summary": portfolio_summary,
            "current_portfolio": portfolios[0] if portfolios else None
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@router.get("/portfolio/{portfolio_id}", response_class=HTMLResponse)
async def portfolio_detail(
    request: Request,
    portfolio_id: UUID,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Portfolio detail page"""
    try:
        portfolio_summary = db_service.get_portfolio_summary(portfolio_id)
        if not portfolio_summary:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        holdings = db_service.get_portfolio_holdings(portfolio_id)
        transactions = db_service.get_portfolio_transactions(portfolio_id, limit=50)
        analysis_sessions = db_service.get_portfolio_analysis_sessions(portfolio_id, limit=10)
        
        return templates.TemplateResponse("portfolio_detail.html", {
            "request": request,
            "portfolio_summary": portfolio_summary,
            "holdings": holdings,
            "transactions": transactions,
            "analysis_sessions": analysis_sessions
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@router.get("/analysis/{portfolio_id}", response_class=HTMLResponse)
async def analysis_page(
    request: Request,
    portfolio_id: UUID,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Analysis page"""
    try:
        portfolio = db_service.get_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        analysis_sessions = db_service.get_portfolio_analysis_sessions(portfolio_id, limit=20)
        
        # Simple market status
        market_status = {
            "current_session": "market_closed",
            "is_trading_day": True,
            "market_timezone": "America/New_York",
            "status": "operational"
        }
        
        return templates.TemplateResponse("analysis.html", {
            "request": request,
            "portfolio": portfolio,
            "analysis_history": analysis_sessions,
            "market_status": market_status
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@router.post("/analysis/run")
async def run_analysis_form(
    portfolio_id: UUID = Form(...),
    analysis_type: str = Form("full_analysis"),
    db_service: DatabaseService = Depends(get_db_service)
):
    """Run analysis from form submission"""
    try:
        # Create analysis session (simplified for now)
        from app import schemas
        session_create = schemas.AnalysisSessionCreate(
            portfolio_id=portfolio_id,
            analysis_type=analysis_type,
            status=schemas.AnalysisStatus.PENDING
        )
        session = db_service.create_analysis_session(session_create)
        
        # Redirect to analysis page
        return RedirectResponse(
            url=f"/analysis/{portfolio_id}",
            status_code=302
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/transactions/{portfolio_id}", response_class=HTMLResponse)
async def transactions_page(
    request: Request,
    portfolio_id: UUID,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Transactions page"""
    try:
        portfolio = db_service.get_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        transactions = db_service.get_portfolio_transactions(portfolio_id, limit=100)
        
        return templates.TemplateResponse("transactions.html", {
            "request": request,
            "portfolio": portfolio,
            "transactions": transactions
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@router.get("/portfolio/{portfolio_id}/analysis", response_class=HTMLResponse)
async def portfolio_analysis(
    request: Request,
    portfolio_id: UUID,
    db_service: DatabaseService = Depends(get_db_service),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """Portfolio analysis page"""
    try:
        portfolio = db_service.get_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Get analysis history
        analysis_history = analysis_service.get_portfolio_analysis_history(str(portfolio_id), limit=10)
        
        # Get market status
        market_status = analysis_service.get_market_status()
        
        return templates.TemplateResponse("analysis.html", {
            "request": request,
            "portfolio": portfolio,
            "analysis_history": analysis_history,
            "market_status": market_status
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@router.post("/portfolio/{portfolio_id}/analysis/run")
async def run_portfolio_analysis_web(
    request: Request,
    portfolio_id: UUID,
    analysis_type: str = Form("comprehensive"),
    db_service: DatabaseService = Depends(get_db_service),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """Run portfolio analysis from web interface"""
    try:
        # Run the analysis
        result = analysis_service.run_portfolio_analysis(
            portfolio_id=str(portfolio_id),
            analysis_type=analysis_type,
            include_pdf=True,
            user_id=None
        )
        
        if "error" in result:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": result["error"]
            })
        
        # Redirect to analysis results
        return RedirectResponse(
            url=f"/portfolio/{portfolio_id}/analysis/results/{result['analysis_session_id']}", 
            status_code=303
        )
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@router.get("/portfolio/{portfolio_id}/analysis/results/{session_id}", response_class=HTMLResponse)
async def analysis_results(
    request: Request,
    portfolio_id: UUID,
    session_id: str,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """View analysis results"""
    try:
        # Get analysis session
        session = analysis_service.get_analysis_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Analysis session not found")
        
        # First priority: Check if session has a stored report_path (direct from database)
        if session.get("report_path") and os.path.exists(session["report_path"]):
            # Serve the rich HTML report content directly from stored path
            with open(session["report_path"], 'r', encoding='utf-8') as f:
                html_content = f.read()
            return HTMLResponse(content=html_content)
        
        # Second priority: Check if analysis has cached report paths in results
        if session.get("results") and session["results"].get("report_paths", {}).get("html"):
            html_path = session["results"]["report_paths"]["html"]
            if os.path.exists(html_path):
                # Serve the rich HTML report content directly
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                return HTMLResponse(content=html_content)
        
        # If no report file found, fall back to template with available data
        results = session.get("results", {})
        
        return templates.TemplateResponse("analysis_results.html", {
            "request": request,
            "portfolio_id": portfolio_id,
            "session": session,
            "results": results
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@router.get("/portfolio/{portfolio_id}/analysis/pdf/{session_id}")
async def download_analysis_pdf(
    portfolio_id: UUID,
    session_id: str,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """Download analysis PDF report"""
    try:
        # Get analysis session
        session = analysis_service.get_analysis_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Analysis session not found")
        
        # First priority: Get PDF path from session results
        pdf_path = None
        if session.get("results") and session["results"].get("report_paths", {}).get("pdf"):
            pdf_path = session["results"]["report_paths"]["pdf"]
        
        # Second priority: Try to find PDF by looking for files with matching timestamp
        if not pdf_path or not os.path.exists(pdf_path):
            # Extract date from session to find matching PDF files
            started_at = session.get("started_at", "")
            if started_at:
                try:
                    from datetime import datetime
                    # Parse the ISO timestamp and format as needed for filename
                    dt = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                    date_pattern = dt.strftime('%Y%m%d')
                    
                    # Look for PDF files with matching date
                    import glob
                    pdf_pattern = f"reports/portfolio_analysis_{date_pattern}_*.pdf"
                    pdf_files = sorted(glob.glob(pdf_pattern), key=os.path.getmtime, reverse=True)
                    
                    # Use the most recent PDF file for this date
                    if pdf_files:
                        pdf_path = pdf_files[0]
                except Exception as e:
                    print(f"Error finding PDF by pattern: {e}")
        
        # Check if PDF file exists
        if pdf_path and os.path.exists(pdf_path):
            from fastapi.responses import FileResponse
            # Use the original filename but make it more descriptive
            original_filename = os.path.basename(pdf_path)
            descriptive_filename = f"portfolio_analysis_{portfolio_id}_{session_id}.pdf"
            return FileResponse(
                path=pdf_path,
                filename=descriptive_filename,
                media_type='application/pdf'
            )
        
        # If no PDF found, provide helpful error
        raise HTTPException(
            status_code=404, 
            detail="PDF report not found. The analysis may not have completed successfully or PDF generation was disabled."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accessing PDF report: {str(e)}")

@router.get("/reports/{filename}")
async def serve_report_file(filename: str):
    """Serve report files (HTML/PDF) from the reports directory"""
    import os
    from fastapi.responses import FileResponse
    
    # Validate filename to prevent directory traversal
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = os.path.join("reports", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    
    # Determine media type based on extension
    if filename.endswith('.html'):
        media_type = 'text/html'
    elif filename.endswith('.pdf'):
        media_type = 'application/pdf'
    else:
        media_type = 'application/octet-stream'
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )

@router.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    """Settings page - displays environment configuration"""
    # Collect environment variables for display
    def get_env_bool(key: str, default: bool = False) -> bool:
        return os.getenv(key, str(default).lower()).lower() in ['true', '1', 'yes', 'on']
    
    def get_env_str(key: str, default: str = '') -> str:
        return os.getenv(key, default)
    
    def get_env_float(key: str, default: float = 0.0) -> float:
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    def get_env_int(key: str, default: int = 0) -> int:
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    # Mask sensitive values for display
    def mask_sensitive(value: str) -> str:
        if not value or value == 'Not configured':
            return value
        if len(value) <= 8:
            return '*' * len(value)
        return value[:4] + '*' * (len(value) - 8) + value[-4:]

    settings_data = {
        # API Configuration
        'OPENAI_API_KEY': mask_sensitive(get_env_str('OPENAI_API_KEY')),
        'FINNHUB_API_KEY': mask_sensitive(get_env_str('FINNHUB_API_KEY')),
        
        # Portfolio Configuration
        'PORTFOLIO_MODE': get_env_bool('PORTFOLIO_MODE'),
        'RUN_ONCE_MODE': get_env_bool('RUN_ONCE_MODE'),
        'PORTFOLIO_HOLDINGS': get_env_str('PORTFOLIO_HOLDINGS'),
        
        # Market & Scheduling Configuration
        'MARKET_TIMEZONE': get_env_str('MARKET_TIMEZONE'),
        'ENABLE_STRATEGIC_SCHEDULING': get_env_bool('ENABLE_STRATEGIC_SCHEDULING'),
        'SCHEDULING_STRATEGY': get_env_str('SCHEDULING_STRATEGY'),
        'SCHEDULE_TIME': get_env_str('SCHEDULE_TIME'),
        'RUN_IMMEDIATE_ANALYSIS': get_env_bool('RUN_IMMEDIATE_ANALYSIS'),
        'AUTO_DETECT_ANALYSIS_TYPE': get_env_bool('AUTO_DETECT_ANALYSIS_TYPE'),
        
        # Caching Configuration
        'ENABLE_CACHING': get_env_bool('ENABLE_CACHING'),
        'CACHE_DIRECTORY': get_env_str('CACHE_DIRECTORY'),
        'CACHE_CLEANUP_ON_START': get_env_bool('CACHE_CLEANUP_ON_START'),
        'CACHE_STATS_ON_START': get_env_bool('CACHE_STATS_ON_START'),
        'CACHE_STOCK_DATA_MARKET_HOURS': get_env_str('CACHE_STOCK_DATA_MARKET_HOURS'),
        'CACHE_SENTIMENT_MARKET_HOURS': get_env_str('CACHE_SENTIMENT_MARKET_HOURS'),
        'CACHE_AI_RECOMMENDATIONS_MARKET_HOURS': get_env_str('CACHE_AI_RECOMMENDATIONS_MARKET_HOURS'),
        
        # Risk Management
        'STOP_LOSS_PERCENT': get_env_float('STOP_LOSS_PERCENT'),
        'TAKE_PROFIT_PERCENT': get_env_float('TAKE_PROFIT_PERCENT'),
        'MAX_POSITION_SIZE': get_env_str('MAX_POSITION_SIZE'),
        'DAILY_LOSS_LIMIT': get_env_str('DAILY_LOSS_LIMIT'),
        'RSI_OVERSOLD': get_env_str('RSI_OVERSOLD'),
        'RSI_OVERBOUGHT': get_env_str('RSI_OVERBOUGHT'),
        
        # Notification Settings
        'ENABLE_NOTIFICATIONS': get_env_bool('ENABLE_NOTIFICATIONS'),
        'NOTIFICATION_TYPE': get_env_str('NOTIFICATION_TYPE'),
        'DISCORD_WEBHOOK_URL': mask_sensitive(get_env_str('DISCORD_WEBHOOK_URL')),
        'SLACK_CHANNEL': get_env_str('SLACK_CHANNEL'),
        'EMAIL_SMTP_SERVER': get_env_str('EMAIL_SMTP_SERVER'),
        
        # System Configuration
        'DATABASE_URL': mask_sensitive(get_env_str('DATABASE_URL')),
        'DEBUG': get_env_bool('DEBUG'),
        'REPORT_OUTPUT_DIR': get_env_str('REPORT_OUTPUT_DIR'),
        'GENERATE_PDF_REPORTS': get_env_bool('GENERATE_PDF_REPORTS', True),
        'INCLUDE_INDIVIDUAL_CHARTS': get_env_bool('INCLUDE_INDIVIDUAL_CHARTS', True),
    }
    
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "settings": settings_data
    })