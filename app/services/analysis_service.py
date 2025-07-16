import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

# Add project root to path to access existing modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.models import (
    Portfolio, StockDataCache, NewsSentimentCache, AIAnalysisCache, 
    AnalysisSession, MarketSession as DBMarketSession
)
from app.schemas import AnalysisSessionCreate, AnalysisStatus
from analyzer import analyze_portfolio, analyze_single_stock
from strategy_manager import StrategyManager
from market_scheduler import MarketScheduler, MarketSession
from cache_manager import CacheManager
from data_storage import InvestmentDataStorage

class AnalysisService:
    """Service layer for portfolio and stock analysis with database-backed caching"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache_manager = CacheManager()
        self.market_scheduler = MarketScheduler()
        self.data_storage = InvestmentDataStorage()
        self.strategy_manager = StrategyManager()
        
    def run_portfolio_analysis(
        self, 
        portfolio_id: str, 
        analysis_type: str = "comprehensive",
        include_pdf: bool = True,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive portfolio analysis with database caching
        """
        try:
            # Get portfolio data
            portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
            if not portfolio:
                return {"error": "Portfolio not found"}
            
            # Get holdings data
            holdings = {}
            for holding in portfolio.holdings:
                holdings[holding.symbol] = {
                    'quantity': float(holding.shares),
                    'cost_basis': float(holding.average_cost)
                }
            
            if not holdings:
                return {"error": "No holdings found in portfolio"}
            
            # Create analysis session record
            analysis_session = AnalysisSession(
                portfolio_id=portfolio_id,
                analysis_type=analysis_type,
                status=AnalysisStatus.RUNNING,
                started_at=datetime.utcnow()
            )
            self.db.add(analysis_session)
            self.db.commit()
            self.db.refresh(analysis_session)
            
            # Get current strategy
            active_strategy = self.strategy_manager.get_active_strategy()
            
            # Set up analysis context
            analysis_context = {
                'analysis_type': analysis_type,
                'market_session': self.market_scheduler.get_market_session().value,
                'scheduled': False,
                'portfolio_id': portfolio_id,
                'analysis_session_id': str(analysis_session.id)
            }
            
            # Run the analysis using existing system
            results = self._run_cached_portfolio_analysis(
                holdings=holdings,
                portfolio_name=portfolio.name,
                include_pdf=include_pdf,
                analysis_context=analysis_context
            )
            
            # Update analysis session with results
            analysis_session.status = AnalysisStatus.COMPLETED if "error" not in results else AnalysisStatus.FAILED
            analysis_session.completed_at = datetime.utcnow()
            
            # Set report path if generated (prioritize HTML for web display)
            if "error" not in results and "report_paths" in results:
                html_path = results["report_paths"].get("html")
                pdf_path = results["report_paths"].get("pdf")
                
                # Store HTML path as primary report_path for web display
                if html_path and os.path.exists(html_path):
                    analysis_session.report_path = html_path
                # Fallback to PDF if no HTML
                elif pdf_path and os.path.exists(pdf_path):
                    analysis_session.report_path = pdf_path
            
            # Store cache results in database
            if "error" not in results:
                self._store_analysis_cache(analysis_session.id, results)
            
            # Commit all changes to database
            self.db.commit()
            self.db.refresh(analysis_session)
            
            return {
                "analysis_session_id": str(analysis_session.id),
                "portfolio_id": portfolio_id,
                "status": analysis_session.status,
                "results": results,
                "started_at": analysis_session.started_at.isoformat(),
                "completed_at": analysis_session.completed_at.isoformat() if analysis_session.completed_at else None
            }
            
        except Exception as e:
            # Update analysis session with error
            if 'analysis_session' in locals():
                analysis_session.status = AnalysisStatus.FAILED
                analysis_session.completed_at = datetime.utcnow()
                analysis_session.error_message = str(e)
                self.db.commit()
            
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _run_cached_portfolio_analysis(
        self, 
        holdings: Dict, 
        portfolio_name: str,
        include_pdf: bool = True,
        analysis_context: Dict = None
    ) -> Dict[str, Any]:
        """
        Run portfolio analysis with intelligent caching
        """
        try:
            # Import OpenAI client setup (from existing system)
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Risk management settings
            stop_loss_percent = float(os.getenv('STOP_LOSS_PERCENT', '-10.0'))
            take_profit_percent = float(os.getenv('TAKE_PROFIT_PERCENT', '20.0'))
            
            # Report settings
            report_output_dir = os.getenv('REPORT_OUTPUT_DIR', 'reports')
            
            # Use existing analyze_portfolio function but capture results
            import io
            import contextlib
            
            # Capture stdout to get analysis results
            captured_output = io.StringIO()
            
            # Call existing portfolio analysis
            with contextlib.redirect_stdout(captured_output):
                analyze_portfolio(
                    portfolio_holdings=holdings,
                    client=client,
                    stop_loss_percent=stop_loss_percent,
                    take_profit_percent=take_profit_percent,
                    generate_pdf_reports=include_pdf,
                    notification_type='none',  # Disable notifications for server mode
                    enable_notifications=False,
                    report_output_dir=report_output_dir,
                    include_individual_charts=True,
                    generate_html_reports=True,
                    store_historical_data=True,
                    analysis_context=analysis_context
                )
            
            # Get the output
            analysis_output = captured_output.getvalue()
            
            # Get generated report paths by looking for the latest files
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            report_output_dir = os.getenv('REPORT_OUTPUT_DIR', 'reports')
            
            # Find the most recent report files
            import glob
            
            # Look for HTML and PDF files with today's date
            today = datetime.utcnow().strftime('%Y%m%d')
            html_pattern = f"{report_output_dir}/portfolio_analysis_{today}_*.html"
            pdf_pattern = f"{report_output_dir}/portfolio_analysis_{today}_*.pdf"
            
            html_files = sorted(glob.glob(html_pattern), key=os.path.getmtime, reverse=True)
            pdf_files = sorted(glob.glob(pdf_pattern), key=os.path.getmtime, reverse=True)
            
            # Get the most recent files (likely just generated)
            html_path = html_files[0] if html_files else None
            pdf_path = pdf_files[0] if pdf_files else None
            
            # Load the stored results from data storage
            report_data = self._get_latest_analysis_results(holdings, analysis_context)
            
            return {
                "status": "success",
                "portfolio_name": portfolio_name,
                "analysis_output": analysis_output,
                "report_data": report_data,
                "report_paths": {
                    "html": html_path,
                    "pdf": pdf_path
                },
                "analysis_context": analysis_context,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Portfolio analysis failed: {str(e)}"}
    
    def _get_latest_analysis_results(self, holdings: Dict, context: Dict) -> Dict:
        """Get the latest analysis results from data storage"""
        try:
            # This would integrate with the existing data storage system
            # For now, return a structured response based on holdings
            results = {
                "portfolio_summary": {
                    "total_positions": len(holdings),
                    "symbols": list(holdings.keys()),
                    "analysis_type": context.get('analysis_type', 'comprehensive'),
                    "market_session": context.get('market_session', 'unknown')
                },
                "individual_stocks": {},
                "performance_metrics": {},
                "recommendations": [],
                "risk_assessment": {}
            }
            
            return results
            
        except Exception as e:
            return {"error": f"Failed to retrieve analysis results: {str(e)}"}
    
    def _store_analysis_cache(self, analysis_session_id: str, results: Dict):
        """Store analysis results in database cache tables"""
        try:
            # Store in AI analysis cache - fix the field name
            cache_entry = AIAnalysisCache(
                cache_key=f"analysis_session_{analysis_session_id}",
                context_hash="",  # Add a default context hash
                analysis_type=results.get('analysis_context', {}).get('analysis_type', 'comprehensive'),
                response=results,  # Store full results in 'response' field
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=24)  # Cache for 24 hours
            )
            self.db.add(cache_entry)
            self.db.commit()
            
        except Exception as e:
            # Log error but don't fail the analysis
            print(f"Warning: Failed to store analysis cache: {e}")
            # Don't re-raise the exception
    
    def get_analysis_session(self, session_id: str) -> Optional[Dict]:
        """Get analysis session by ID"""
        session = self.db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
        if not session:
            return None
        
        # Try to get results from cache
        results = None
        cache_entry = self.db.query(AIAnalysisCache).filter(
            AIAnalysisCache.cache_key == f"analysis_session_{session_id}"
        ).first()
        if cache_entry:
            results = cache_entry.response  # Use 'response' field from cache model
            
        return {
            "id": str(session.id),
            "portfolio_id": str(session.portfolio_id),
            "analysis_type": session.analysis_type,
            "status": session.status,
            "started_at": session.started_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "results": results,
            "error_message": session.error_message,
            "report_path": session.report_path  # Include the stored report path
        }
    
    def get_portfolio_analysis_history(self, portfolio_id: str, limit: int = 10) -> List[Dict]:
        """Get analysis history for a portfolio"""
        sessions = (
            self.db.query(AnalysisSession)
            .filter(AnalysisSession.portfolio_id == portfolio_id)
            .order_by(AnalysisSession.started_at.desc())
            .limit(limit)
            .all()
        )
        
        return [
            {
                "id": str(session.id),
                "analysis_type": session.analysis_type,
                "status": session.status.value,
                "started_at": session.started_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "has_results": session.results is not None
            }
            for session in sessions
        ]
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get current market status for analysis timing"""
        try:
            # Get basic market info from scheduler
            current_session = self.market_scheduler.get_market_session()
            is_trading_day = self.market_scheduler.is_market_day()
            
            return {
                "current_session": current_session.value if hasattr(current_session, 'value') else str(current_session),
                "is_trading_day": is_trading_day,
                "market_timezone": "America/New_York",
                "status": "operational",
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            # Fallback to simple status if market scheduler fails
            return {
                "current_session": "market_closed",
                "is_trading_day": True,
                "market_timezone": "America/New_York", 
                "status": "limited",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "note": "Using simplified market status"
            }
    
    def run_single_stock_analysis(
        self, 
        symbol: str, 
        portfolio_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run analysis for a single stock"""
        try:
            # Create analysis session
            analysis_session = AnalysisSession(
                portfolio_id=portfolio_id,
                analysis_type="single_stock",
                status=AnalysisStatus.RUNNING,
                started_at=datetime.utcnow()
            )
            self.db.add(analysis_session)
            self.db.commit()
            self.db.refresh(analysis_session)
            
            # Set up analysis context
            analysis_context = {
                'analysis_type': 'single_stock',
                'market_session': self.market_scheduler.get_market_session().value,
                'scheduled': False,
                'symbol': symbol,
                'analysis_session_id': str(analysis_session.id)
            }
            
            # Run single stock analysis
            results = self._run_cached_single_stock_analysis(symbol, analysis_context)
            
            # Update session
            analysis_session.status = AnalysisStatus.COMPLETED if "error" not in results else AnalysisStatus.FAILED
            analysis_session.completed_at = datetime.utcnow()
            # Store results in cache instead of session directly
            self.db.commit()
            
            return {
                "analysis_session_id": str(analysis_session.id),
                "symbol": symbol,
                "status": analysis_session.status,
                "results": results,
                "started_at": analysis_session.started_at.isoformat(),
                "completed_at": analysis_session.completed_at.isoformat() if analysis_session.completed_at else None
            }
            
        except Exception as e:
            if 'analysis_session' in locals():
                analysis_session.status = AnalysisStatus.FAILED
                analysis_session.completed_at = datetime.utcnow()
                analysis_session.error_message = str(e)
                self.db.commit()
            
            return {"error": f"Single stock analysis failed: {str(e)}"}
    
    def _run_cached_single_stock_analysis(self, symbol: str, context: Dict) -> Dict[str, Any]:
        """Run single stock analysis with caching"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Risk management settings
            stop_loss_percent = float(os.getenv('STOP_LOSS_PERCENT', '-10.0'))
            take_profit_percent = float(os.getenv('TAKE_PROFIT_PERCENT', '20.0'))
            report_output_dir = os.getenv('REPORT_OUTPUT_DIR', 'reports')
            
            # Use existing analyze_single_stock function
            import io
            import contextlib
            
            captured_output = io.StringIO()
            
            with contextlib.redirect_stdout(captured_output):
                analyze_single_stock(
                    symbol=symbol,
                    client=client,
                    stop_loss_percent=stop_loss_percent,
                    take_profit_percent=take_profit_percent,
                    generate_pdf_reports=True,
                    notification_type='none',
                    enable_notifications=False,
                    report_output_dir=report_output_dir,
                    include_individual_charts=True,
                    portfolio_holdings={},
                    analysis_context=context
                )
            
            analysis_output = captured_output.getvalue()
            
            return {
                "status": "success",
                "symbol": symbol,
                "analysis_output": analysis_output,
                "analysis_context": context,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Single stock analysis failed: {str(e)}"} 