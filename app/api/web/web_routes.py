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
from app.models import AnalysisSession

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
        recent_analyses = []
        if portfolios:
            portfolio_summary = db_service.get_portfolio_summary(portfolios[0].id)
            # Get recent analysis sessions for the first portfolio
            recent_analyses = db_service.get_portfolio_analysis_sessions(portfolios[0].id, limit=5)
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user": user,
            "portfolios": portfolios,
            "portfolio_summary": portfolio_summary,
            "current_portfolio": portfolios[0] if portfolios else None,
            "recent_analyses": recent_analyses
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
    db_service: DatabaseService = Depends(get_db_service),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """Analysis page"""
    try:
        portfolio = db_service.get_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        analysis_sessions = db_service.get_portfolio_analysis_sessions(portfolio_id, limit=20)
        
        # Get comprehensive market status from analysis service
        market_status = analysis_service.get_market_status()
        
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

@router.get("/portfolio/{portfolio_id}/transactions", response_class=HTMLResponse)
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
    db_service: DatabaseService = Depends(get_db_service)
):
    """Portfolio analysis page"""
    try:
        portfolio = db_service.get_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Use simple approach like the working analysis route
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

@router.get("/portfolio/{portfolio_id}/analysis/results/{session_id}")
async def get_analysis_results_dynamic(portfolio_id: str, session_id: str, db: Session = Depends(get_db)):
    """Get dynamically rendered analysis results from database data"""
    try:
        from app.services.analysis_service import AnalysisService
        from html_renderer import HTMLReportRenderer
        
        # Get analysis session from database
        analysis_service = AnalysisService(db)
        session_data = analysis_service.get_analysis_session(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Analysis session not found")
        
        if session_data["status"] != "COMPLETED":
            return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Analysis in Progress</title>
                <meta http-equiv="refresh" content="5">
            </head>
            <body>
                <h1>Analysis in Progress</h1>
                <p>Status: {session_data["status"]}</p>
                <p>Started: {session_data["started_at"]}</p>
                <p>This page will refresh automatically...</p>
            </body>
            </html>
            """)
        
        # Get the analysis session with all JSONB data
        # Convert session_id string to UUID for proper database query
        import uuid
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session ID format")
        
        analysis_session = db.query(AnalysisSession).filter(AnalysisSession.id == session_uuid).first()
        
        if not analysis_session:
            raise HTTPException(status_code=404, detail="Analysis session not found")
        
        # Build report data from database JSONB fields in the format expected by HTMLReportRenderer
        portfolio_snapshot = analysis_session.portfolio_snapshot or {}
        market_data = analysis_session.market_data_snapshot or {}
        technical_indicators = analysis_session.technical_indicators or {}
        sentiment_analysis = analysis_session.sentiment_analysis or {}
        ai_recommendations = analysis_session.ai_recommendations or {}
        risk_metrics = analysis_session.risk_metrics or {}
        trading_signals = analysis_session.trading_signals or {}
        
        # Transform data to expected structure
        stocks_data = {}
        portfolio_holdings = portfolio_snapshot.get("holdings", {})
        
        # Debug: Check what we actually have in the database
        if not portfolio_holdings:
            print(f"WARNING: No portfolio holdings found in database for session {session_id}")
            print(f"Portfolio snapshot keys: {list(portfolio_snapshot.keys()) if portfolio_snapshot else 'Empty'}")
            print(f"Market data keys: {list(market_data.keys()) if market_data else 'Empty'}")
            
        # Fix: If portfolio_holdings is empty, check if symbols are in market_data
        if not portfolio_holdings and market_data:
            print(f"Creating fallback holdings from market data symbols: {list(market_data.keys())}")
            # Fallback: create basic holdings from market data
            for symbol in market_data.keys():
                portfolio_holdings[symbol] = {
                    "quantity": 1.0,  # Default quantity
                    "cost_basis": market_data[symbol].get("current_price", 0)
                }
        
        print(f"Processing {len(portfolio_holdings)} holdings: {list(portfolio_holdings.keys())}")
        
        for symbol in portfolio_holdings.keys():
            stock_market_data = market_data.get(symbol, {})
            stock_tech_data = technical_indicators.get(symbol, {})
            stock_sentiment = sentiment_analysis.get(symbol, {})
            stock_ai_rec = ai_recommendations.get(symbol, {})
            stock_risk = risk_metrics.get(symbol, {})
            stock_signals = trading_signals.get(symbol, {})
            
            # Get current price from portfolio snapshot (correctly extracted during analysis)
            holding_data = portfolio_holdings[symbol]
            current_price = holding_data.get("current_price", 0)
            quantity = holding_data.get("quantity", 0)
            cost_basis = holding_data.get("cost_basis", 0)
            market_value = holding_data.get("market_value", 0)
            
            # DEBUG: Print the actual holding data to see what's available
            print(f"DEBUG {symbol} holding_data: {holding_data}")
            
            # If market_value is 0 or None, but we have current_price and quantity, recalculate
            if (not market_value or market_value == 0) and current_price and quantity:
                market_value = current_price * quantity
                print(f"RECALCULATED {symbol}: {current_price} * {quantity} = {market_value}")
            
            # If current_price is still 0, try to get it from market_data
            if (not current_price or current_price == 0) and stock_market_data:
                # Try to extract current price from market data
                if "current_price" in stock_market_data:
                    current_price = stock_market_data["current_price"]
                elif "close" in stock_market_data:
                    current_price = stock_market_data["close"]
                elif "price" in stock_market_data:
                    current_price = stock_market_data["price"]
                    
                if current_price and quantity:
                    market_value = current_price * quantity
                    print(f"FALLBACK {symbol}: Using market data price {current_price} * {quantity} = {market_value}")
            
            print(f"FINAL {symbol}: price={current_price}, qty={quantity}, cost={cost_basis}, value={market_value}")
            
            # DEBUG: Print AI recommendation data to see what's available
            print(f"DEBUG {symbol} AI recommendation: {stock_ai_rec}")
            
            # Extract AI recommendation properly
            ai_recommendation = "HOLD"  # Default
            if stock_ai_rec:
                if isinstance(stock_ai_rec, dict):
                    ai_recommendation = stock_ai_rec.get("recommendation", "HOLD")
                elif isinstance(stock_ai_rec, str):
                    ai_recommendation = stock_ai_rec
            
            print(f"FINAL {symbol} AI recommendation: {ai_recommendation}")
            
            # Build stock data in the nested format expected by HTMLReportRenderer
            stocks_data[symbol] = {
                "symbol": symbol,
                "current_price": current_price,
                "price_change": stock_market_data.get("price_change", 0),
                "price_change_percent": stock_market_data.get("price_change_percent", 0),
                "volume": stock_market_data.get("volume", 0),
                "market_cap": stock_market_data.get("market_cap", "N/A"),
                "pe_ratio": stock_market_data.get("pe_ratio", "N/A"),
                "dividend_yield": stock_market_data.get("dividend_yield", "N/A"),
                "company_name": stock_market_data.get("company_name", symbol),
                "sector": stock_market_data.get("sector", "Unknown"),
                "industry": stock_market_data.get("industry", "Unknown"),
                
                # Portfolio specific data
                "quantity": quantity,
                "cost_basis": cost_basis,
                "market_value": market_value,  # Keep for portfolio calculations
                "current_value": market_value,  # HTML template expects this field name
                "unrealized_gain_loss": market_value - (cost_basis * quantity) if cost_basis and quantity else 0,
                "profit_loss": market_value - (cost_basis * quantity) if cost_basis and quantity else 0,  # HTML template expects this field name
                "profit_loss_percent": ((current_price - cost_basis) / cost_basis * 100) if cost_basis and cost_basis > 0 else 0,
                
                # Technical analysis (nested structure expected by renderer)
                "technical": {
                    "rsi": stock_tech_data.get("rsi", 50),
                    "ma_20": stock_tech_data.get("ma_20", current_price),
                    "ma_50": stock_tech_data.get("ma_50", current_price),
                    "bollinger_upper": stock_tech_data.get("bollinger_upper", current_price),
                    "bollinger_lower": stock_tech_data.get("bollinger_lower", current_price),
                },
                
                # Sentiment (nested structure expected by renderer)
                "sentiment": {
                    "score": stock_sentiment.get("sentiment_score", 0),
                    "overall": stock_sentiment.get("sentiment", "neutral").lower(),
                    "article_count": stock_sentiment.get("article_count", 0)
                },
                
                # AI Analysis (nested structure expected by renderer)
                "ai_analysis": {
                    "recommendation_type": ai_recommendation,  # Keep for portfolio calculations
                    "recommendation": ai_recommendation,  # HTML template expects this field name
                    "confidence": stock_ai_rec.get("confidence", 0) if isinstance(stock_ai_rec, dict) else 0,
                    "reasoning": stock_ai_rec.get("reasoning", "No analysis available") if isinstance(stock_ai_rec, dict) else "No analysis available"
                },
                
                # Risk (nested structure expected by renderer)
                "risk": {
                    "risk_level": stock_risk.get("risk_level", "medium").lower()
                },
                
                # Trading signals
                "trading_signal": stock_signals.get("combined_signal", "HOLD"),
                
                # Chart data in the format expected by HTMLReportRenderer
                "chart_data": {
                    "dates": stock_market_data.get("dates", []),
                    "prices": stock_market_data.get("price_history", []),
                    "volumes": stock_market_data.get("volume_history", []),
                    "ma_20": stock_market_data.get("ma_20_history", []),
                    "ma_50": stock_market_data.get("ma_50_history", [])
                } if stock_market_data.get("dates") else None
            }
        
        # Calculate portfolio totals
        total_value = sum(stock["market_value"] for stock in stocks_data.values())
        total_cost = sum(stock["cost_basis"] * stock["quantity"] for stock in stocks_data.values() if stock["cost_basis"] and stock["quantity"])
        total_gain_loss = total_value - total_cost
        total_gain_loss_percent = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
        
        # Calculate aggregated statistics for overview
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        rsi_values = []
        overbought_count = 0
        oversold_count = 0
        recommendation_counts = {"buy_signals": 0, "hold_signals": 0, "sell_signals": 0}
        
        for stock in stocks_data.values():
            # Count sentiment distribution
            sentiment = stock.get('sentiment', {}).get('overall', 'neutral').lower()
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1
            
            # Collect RSI values and count overbought/oversold
            rsi = stock.get('technical', {}).get('rsi', 50)
            rsi_values.append(rsi)
            if rsi > 70:
                overbought_count += 1
            elif rsi < 30:
                oversold_count += 1
            
            # Count AI recommendations
            recommendation = stock.get('ai_analysis', {}).get('recommendation_type', 'HOLD').upper()
            if recommendation == 'BUY':
                recommendation_counts["buy_signals"] += 1
            elif recommendation == 'SELL':
                recommendation_counts["sell_signals"] += 1
            else:
                recommendation_counts["hold_signals"] += 1
        
        # Calculate average RSI
        average_rsi = sum(rsi_values) / len(rsi_values) if rsi_values else 50.0
        
        # Count profitable positions
        profitable_positions = sum(1 for stock in stocks_data.values() 
                                 if stock.get("profit_loss_percent", 0) > 0)
        
        # Build portfolio summary in the FLAT format expected by HTML renderer
        portfolio_data = {
            # Direct portfolio totals (expected by HTMLReportRenderer._render_executive_summary)
            "total_value": total_value,
            "total_invested": total_cost,  # Note: HTML template expects 'total_invested', not 'total_cost'
            "total_profit_loss": total_gain_loss,
            "total_return_percent": total_gain_loss_percent,
            "position_count": len(portfolio_holdings),
            "profitable_positions": profitable_positions,
            
            # Additional portfolio metadata
            "portfolio_id": portfolio_id,
            "cash_balance": portfolio_snapshot.get("cash_balance", 0),
            "symbols": list(portfolio_holdings.keys()),
            "name": portfolio_snapshot.get("name", "Unknown")
        }
        
        # Create performance data for best/worst performers
        performance_data = {}
        if stocks_data:
            # Find best and worst performers
            best_symbol = max(stocks_data.keys(), key=lambda x: stocks_data[x].get("profit_loss_percent", 0))
            worst_symbol = min(stocks_data.keys(), key=lambda x: stocks_data[x].get("profit_loss_percent", 0))
            
            performance_data = {
                "best_performer": {
                    "symbol": best_symbol,
                    "return_percent": stocks_data[best_symbol].get("profit_loss_percent", 0)
                },
                "worst_performer": {
                    "symbol": worst_symbol, 
                    "return_percent": stocks_data[worst_symbol].get("profit_loss_percent", 0)
                }
            }
        
        report_data = {
            "analysis_id": session_id,
            "portfolio_id": portfolio_id,
            "date": analysis_session.started_at.strftime("%Y-%m-%d"),
            "time": analysis_session.started_at.strftime("%H:%M:%S"),
            "portfolio_name": portfolio_snapshot.get("name", "Unknown"),
            "market_session": analysis_session.backtesting_context.get("market_conditions", "unknown") if analysis_session.backtesting_context else "unknown",
            "portfolio": portfolio_data,
            "stocks": stocks_data,
            "performance": performance_data,
            "analysis_summary": analysis_session.backtesting_context.get("analysis_summary", {}) if analysis_session.backtesting_context else {},
            "market_analysis": {
                "sentiment_distribution": sentiment_counts,
                "technical_overview": {
                    "average_rsi": average_rsi,
                    "overbought_count": overbought_count,
                    "oversold_count": oversold_count
                },
                "recommendations_summary": recommendation_counts
            }
        }
        
        # Use HTML renderer to generate the report
        html_renderer = HTMLReportRenderer()
        html_content = html_renderer._generate_html(report_data)
        
        # Wrap with navigation (same as before)
        wrapped_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Analysis Report - AI Investment Tool</title>
            <style>
                /* Navigation Styles */
                .nav-wrapper {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 0;
                    margin: 0;
                    position: sticky;
                    top: 0;
                    z-index: 1000;
                }}
                .top-nav {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 1rem 2rem;
                    background: rgba(255,255,255,0.1);
                    backdrop-filter: blur(10px);
                    border-bottom: 1px solid rgba(255,255,255,0.2);
                }}
                .nav-brand {{
                    font-size: 1.5rem;
                    font-weight: bold;
                    color: white;
                    text-decoration: none;
                }}
                .nav-links {{
                    display: flex;
                    gap: 1rem;
                }}
                .nav-link {{
                    color: white;
                    text-decoration: none;
                    padding: 0.5rem 1rem;
                    border-radius: 5px;
                    transition: background-color 0.3s;
                }}
                .nav-link:hover {{
                    background-color: rgba(255,255,255,0.2);
                }}
                .report-content {{
                    max-width: none;
                    margin: 0;
                    padding: 0;
                }}
            </style>
        </head>
        <body>
            <div class="nav-wrapper">
                <nav class="top-nav">
                    <a href="/dashboard" class="nav-brand">🤖 AI Investment Tool</a>
                    <div class="nav-links">
                        <a href="/dashboard" class="nav-link">📊 Dashboard</a>
                        <a href="/portfolio/{portfolio_id}" class="nav-link">💼 Portfolio</a>
                        <a href="/portfolio/{portfolio_id}/analysis" class="nav-link">📈 Analysis</a>
                        <a href="/settings" class="nav-link">⚙️ Settings</a>
                    </div>
                </nav>
            </div>
            <div class="report-content">
                {html_content}
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=wrapped_html)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

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