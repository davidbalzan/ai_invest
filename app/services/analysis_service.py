import os
import sys
from datetime import datetime, timezone, timedelta, date
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import json
import io
import contextlib
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
        # Progress tracking
        self.current_session_id = None
        self.progress_logs = []
        
    def run_portfolio_analysis(
        self, 
        portfolio_id: str, 
        analysis_type: str = "comprehensive",
        include_pdf: bool = False,  # Disable PDF generation by default
        user_id: Optional[str] = None,
        existing_session_id: Optional[str] = None,  # Allow using existing session
        force_refresh: bool = False  # Bypass cache and fetch fresh data
    ) -> Dict[str, Any]:
        """
        Run comprehensive portfolio analysis with database storage
        """
        print(f"===== DEBUG: AnalysisService.run_portfolio_analysis CALLED for portfolio {portfolio_id} =====")
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

            # Use existing session or create new one
            if existing_session_id:
                analysis_session = self.db.query(AnalysisSession).filter(
                    AnalysisSession.id == existing_session_id
                ).first()
                if not analysis_session:
                    return {"error": "Existing session not found"}
                # Update session status to running
                analysis_session.status = AnalysisStatus.RUNNING
                analysis_session.started_at = datetime.utcnow()
                analysis_session.progress_logs = []
            else:
                # Create analysis session record
                analysis_session = AnalysisSession(
                    portfolio_id=portfolio_id,
                    analysis_type=analysis_type,
                    status=AnalysisStatus.RUNNING,
                    started_at=datetime.utcnow(),
                    progress_logs=[]
                )
                self.db.add(analysis_session)
            
            self.db.commit()
            self.db.refresh(analysis_session)
            
            # Set current session for progress tracking
            self.current_session_id = str(analysis_session.id)
            self.progress_logs = []
            self._log_progress(f"🚀 Starting {analysis_type} analysis for portfolio: {portfolio.name}")
            self._update_progress_logs()
            
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
            
            # Run the analysis and store data in database
            self._log_progress(f"📊 Found {len(holdings)} holdings to analyze: {', '.join(holdings.keys())}")
            self._log_progress(f"🔧 Initializing analysis context and market data systems")
            self._update_progress_logs()
            results = self._run_database_portfolio_analysis(
                holdings=holdings,
                portfolio=portfolio,
                analysis_context=analysis_context,
                analysis_session=analysis_session,
                force_refresh=force_refresh
            )
            
            # Update analysis session with results
            analysis_session.status = AnalysisStatus.COMPLETED if "error" not in results else AnalysisStatus.FAILED
            analysis_session.completed_at = datetime.utcnow()
            
            if "error" in results:
                analysis_session.error_message = results["error"]
            
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
    
    def _run_database_portfolio_analysis(
        self, 
        holdings: Dict, 
        portfolio,
        analysis_context: Dict,
        analysis_session: AnalysisSession,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Run portfolio analysis and store data directly in database
        """
        import time
        start_time = time.time()
        
        try:
            from openai import OpenAI
            from data_fetcher import get_stock_data, calculate_technical_indicators
            from ai_analyzer import get_sentiment_analysis, get_ai_recommendation
            
            setup_time = time.time()
            print(f"⏱️ Setup completed in {setup_time - start_time:.1f}s")
            
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Store portfolio snapshot
            portfolio_snapshot = {
                "portfolio_id": str(portfolio.id),
                "name": portfolio.name,
                "total_value": float(portfolio.total_value or 0),
                "cash_balance": float(portfolio.cash_balance or 0),
                "holdings": {}
            }
            
            # Collect market data and analysis for each holding
            market_data_snapshot = {}
            technical_indicators = {}
            sentiment_analysis = {}
            ai_recommendations = {}
            risk_metrics = {}
            trading_signals = {}
            
            analysis_summary = {
                "total_positions": len(holdings),
                "symbols": list(holdings.keys()),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "market_session": analysis_context.get('market_session', 'unknown')
            }
            
            for symbol, holding_info in holdings.items():
                symbol_start_time = time.time()
                symbol_index = list(holdings.keys()).index(symbol) + 1
                self._log_progress(f"🔍 Analyzing {symbol}... ({symbol_index}/{len(holdings)})", data={"symbol": symbol, "progress": symbol_index/len(holdings)*100})
                self._update_progress_logs()
                
                # Get market data
                try:
                    self._log_progress(f"  📊 Fetching market data for {symbol}...")
                    market_data = get_stock_data(symbol, force_refresh=force_refresh)
                    # Convert pandas DataFrame to JSON-serializable format for database storage
                    if market_data is not None and hasattr(market_data, 'to_dict'):
                        self._log_progress(f"  💾 Converting market data to JSON format for {symbol}...")
                        
                        market_data_dict = {
                            'data': market_data.to_dict('records'),
                            'index': market_data.index.strftime('%Y-%m-%d').tolist() if hasattr(market_data.index, 'strftime') else market_data.index.tolist(),
                            'columns': market_data.columns.tolist(),
                            'symbol': symbol,
                            'cached': getattr(market_data, 'attrs', {}).get('cached', False),
                            'retrieval_timestamp': str(getattr(market_data, 'attrs', {}).get('retrieval_timestamp', 'N/A')),
                            # Add chart data arrays for HTML rendering (extract directly from market_data)
                            'dates': market_data.index.strftime('%Y-%m-%d').tolist()[-90:] if hasattr(market_data.index, 'strftime') else [str(d)[:10] for d in market_data.index.tolist()][-90:],
                            'price_history': [None if pd.isna(x) else float(x) for x in market_data['Close'].tail(90).tolist()],
                            'volume_history': [None if pd.isna(x) else float(x) for x in market_data['Volume'].tail(90).tolist()] if 'Volume' in market_data.columns else [],
                            'ma_20_history': [None if pd.isna(x) else float(x) for x in market_data['Close'].rolling(window=20).mean().tail(90).tolist()],
                            'ma_50_history': [None if pd.isna(x) else float(x) for x in market_data['Close'].rolling(window=50).mean().tail(90).tolist()]
                        }
                        # Make sure everything is JSON serializable
                        market_data_dict = self._make_json_serializable(market_data_dict)
                        market_data_snapshot[symbol] = market_data_dict
                        self._log_progress(f"  ✅ Market data and chart data extracted for {symbol}")
                    else:
                        market_data_snapshot[symbol] = {}
                except Exception as e:
                    self._log_progress(f"  ⚠️ Failed to fetch market data for {symbol}: {e}", level="warning")
                    market_data = None
                
                self._update_progress_logs()  # Update after market data
                
                # Get technical indicators
                try:
                    if market_data is not None:
                        self._log_progress(f"  📈 Calculating technical indicators for {symbol}...")
                        tech_indicators = calculate_technical_indicators(market_data, force_refresh=force_refresh)
                        # Convert any datetime objects to strings for JSON serialization
                        tech_indicators = self._make_json_serializable(tech_indicators)
                        technical_indicators[symbol] = tech_indicators
                        self._log_progress(f"  ✅ Technical indicators calculated for {symbol}")
                except Exception as e:
                    self._log_progress(f"  ⚠️ Failed to calculate technical indicators for {symbol}: {e}", level="warning")
                    tech_indicators = {}
                
                self._update_progress_logs()  # Update after technical indicators
                
                # Get sentiment analysis
                try:
                    self._log_progress(f"  📰 Getting sentiment analysis for {symbol}...")
                    sentiment = get_sentiment_analysis(symbol, force_refresh=force_refresh)
                    # Convert any datetime objects to strings for JSON serialization
                    sentiment = self._make_json_serializable(sentiment)
                    sentiment_analysis[symbol] = sentiment
                    self._log_progress(f"  ✅ Sentiment analysis completed for {symbol}")
                except Exception as e:
                    self._log_progress(f"  ⚠️ Failed to get sentiment for {symbol}: {e}", level="warning")
                    sentiment = {}
                
                self._update_progress_logs()  # Update after sentiment analysis
                
                # Get AI recommendation
                try:
                    if market_data is not None and tech_indicators:
                        self._log_progress(f"  🤖 Getting AI recommendation for {symbol}...")
                        ai_rec_raw = get_ai_recommendation(
                            symbol=symbol, 
                            stock_data=market_data,
                            indicators=tech_indicators,
                            sentiment=sentiment,
                            client=client,
                            portfolio_holdings=holding_info,
                            stop_loss_percent=5.0,  # Default values
                            take_profit_percent=20.0,
                            force_refresh=force_refresh
                        )
                        # Convert string response to dictionary format with improved parsing
                        if isinstance(ai_rec_raw, str):
                            # Extract recommendation from string - FIXED: Look for exact recommendation format
                            import re
                            recommendation = "HOLD"  # Default
                            
                            # Look for "RECOMMENDATION: [ACTION]" pattern first (most reliable)
                            rec_match = re.search(r'RECOMMENDATION:\s*(BUY|SELL|HOLD)', ai_rec_raw.upper())
                            if rec_match:
                                recommendation = rec_match.group(1)
                                print(f"REGEX MATCH FOUND for {symbol}: {recommendation}")
                            else:
                                # Fallback: Look for standalone recommendation words (whole words only)
                                first_200_chars = ai_rec_raw[:200].upper()
                                if re.search(r'\bBUY\b', first_200_chars) and not re.search(r'\bSELL\b', first_200_chars):
                                    recommendation = "BUY"
                                    print(f"FALLBACK BUY for {symbol}")
                                elif re.search(r'\bSELL\b', first_200_chars) and not re.search(r'\bBUY\b', first_200_chars):
                                    recommendation = "SELL"
                                    print(f"FALLBACK SELL for {symbol}")
                                print(f"FINAL RECOMMENDATION for {symbol}: {recommendation}")
                            
                            # ENHANCED: Extract confidence from AI response if available
                            confidence = 50.0  # Default moderate confidence instead of hardcoded 70%
                            if "Confidence:" in ai_rec_raw:
                                import re
                                confidence_match = re.search(r'Confidence:\s*(\d+\.?\d*)%?', ai_rec_raw)
                                if confidence_match:
                                    confidence = float(confidence_match.group(1))
                            else:
                                # ENHANCED: Use dynamic confidence calculation if no explicit confidence in response
                                try:
                                    from ai_analyzer import _calculate_recommendation_confidence
                                    # Get technical indicators and sentiment for this symbol
                                    symbol_indicators = {k: v for k, v in technical_indicators.items() if k.endswith(f"_{symbol}")}
                                    symbol_sentiment = {"sentiment": "neutral", "score": 0.0}  # Default sentiment
                                    confidence = _calculate_recommendation_confidence(symbol_indicators, symbol_sentiment)
                                except Exception as e:
                                    self._log_progress(f"  ⚠️ Could not calculate dynamic confidence for {symbol}: {e}", level="warning")
                                    confidence = 50.0  # Safe fallback
                            
                            ai_rec = {
                                "recommendation": recommendation,
                                "reasoning": ai_rec_raw,
                                "confidence": confidence,
                                "raw_response": ai_rec_raw
                            }
                        else:
                            ai_rec = ai_rec_raw
                        
                        ai_recommendations[symbol] = ai_rec
                        self._log_progress(f"  ✅ AI recommendation completed for {symbol}: {ai_rec.get('recommendation', 'HOLD')}")
                except Exception as e:
                    self._log_progress(f"  ⚠️ Failed to get AI recommendation for {symbol}: {e}", level="warning")
                    ai_rec = {"recommendation": "HOLD", "reasoning": "Error in analysis", "confidence": 0}
                
                self._update_progress_logs()  # Update after AI recommendations
                
                # Extract current price from the latest market data
                current_price = None
                if market_data is not None and hasattr(market_data, 'tail') and len(market_data) > 0:
                    current_price = market_data['Close'].iloc[-1] if 'Close' in market_data.columns else None
                
                # Calculate risk metrics
                try:
                    if market_data is not None and current_price is not None:
                        # Create a simple dict with current price for risk calculation
                        market_data_for_risk = {"current_price": float(current_price)}
                        risk_data = self._calculate_risk_metrics(symbol, market_data_for_risk, holding_info)
                        risk_metrics[symbol] = risk_data
                except Exception as e:
                    print(f"⚠️ Failed to calculate risk metrics for {symbol}: {e}")
                    risk_data = {}
                
                # Generate trading signals
                try:
                    if tech_indicators and ai_rec:
                        signals = self._generate_trading_signals(symbol, tech_indicators, ai_rec)
                        trading_signals[symbol] = signals
                except Exception as e:
                    print(f"⚠️ Failed to generate trading signals for {symbol}: {e}")
                    signals = {}
                
                portfolio_snapshot["holdings"][symbol] = {
                    "quantity": holding_info['quantity'],
                    "cost_basis": holding_info['cost_basis'],
                    "current_price": float(current_price) if current_price is not None else None,
                    "market_value": float(current_price * holding_info['quantity']) if current_price is not None else 0,
                    "recommendation": ai_rec.get('recommendation') if isinstance(ai_rec, dict) and ai_rec else 'HOLD',
                    "risk_level": risk_data.get('risk_level') if isinstance(risk_data, dict) and risk_data else 'UNKNOWN'
                }
                
                symbol_end_time = time.time()
                self._log_progress(f"  ⏱️ {symbol} completed in {symbol_end_time - symbol_start_time:.1f}s")
                self._update_progress_logs()  # Update after each symbol completes
            
            self._log_progress(f"🔧 Processing analysis data for {len(holdings)} holdings...")
            self._log_progress(f"📊 Collected data: market({len(market_data_snapshot)}), tech({len(technical_indicators)}), sentiment({len(sentiment_analysis)}), ai({len(ai_recommendations)})")
            self._update_progress_logs()  # Update after data collection summary
            
            # Store all data in analysis session JSONB fields (will be made JSON serializable in commit section)
            analysis_session.market_data_snapshot = market_data_snapshot
            analysis_session.portfolio_snapshot = portfolio_snapshot
            analysis_session.ai_recommendations = ai_recommendations
            analysis_session.sentiment_analysis = sentiment_analysis
            analysis_session.technical_indicators = technical_indicators
            analysis_session.risk_metrics = risk_metrics
            analysis_session.trading_signals = trading_signals
            analysis_session.backtesting_context = {
                "analysis_summary": analysis_summary,
                "strategy_used": analysis_context.get('strategy', 'default'),
                "market_conditions": analysis_context.get('market_session', 'unknown')
            }
            
            # CRITICAL: Commit the JSONB data to database immediately
            self._log_progress(f"💾 Storing analysis data to database for session {analysis_session.id}")
            self._log_progress(f"📊 Market data: {len(market_data_snapshot)} symbols, Portfolio: {len(portfolio_snapshot.get('holdings', {}))}, AI recs: {len(ai_recommendations)}")
            
            try:
                # Make sure all data is JSON serializable before committing
                analysis_session.market_data_snapshot = self._make_json_serializable(market_data_snapshot)
                analysis_session.portfolio_snapshot = self._make_json_serializable(portfolio_snapshot)
                analysis_session.ai_recommendations = self._make_json_serializable(ai_recommendations)
                analysis_session.sentiment_analysis = self._make_json_serializable(sentiment_analysis)
                analysis_session.technical_indicators = self._make_json_serializable(technical_indicators)
                analysis_session.risk_metrics = self._make_json_serializable(risk_metrics)
                analysis_session.trading_signals = self._make_json_serializable(trading_signals)
                analysis_session.backtesting_context = self._make_json_serializable({
                    "analysis_summary": analysis_summary,
                    "strategy_used": analysis_context.get('strategy', 'default'),
                    "market_conditions": analysis_context.get('market_session', 'unknown')
                })
                
                self._log_progress(f"💾 Committing to database...")
                self.db.commit()
                self.db.refresh(analysis_session)
                self._log_progress(f"✅ Data successfully stored in database!")
            except Exception as e:
                self._log_progress(f"❌ Database commit failed: {e}", level="error")
                self.db.rollback()
                raise e
            
            total_time = time.time() - start_time
            self._log_progress(f"🏁 Portfolio analysis completed in {total_time:.1f}s")
            self._update_progress_logs()  # Final progress update
            
            return {
                "status": "success",
                "portfolio_name": portfolio.name,
                "analysis_summary": analysis_summary,
                "data_stored_in_database": True,
                "analysis_context": analysis_context,
                "timestamp": datetime.utcnow().isoformat(),
                "execution_time_seconds": round(total_time, 1)
            }
            
        except Exception as e:
            return {"error": f"Database portfolio analysis failed: {str(e)}"}
    


    def _calculate_risk_metrics(self, symbol: str, market_data: Dict, holding_info: Dict) -> Dict:
        """Calculate risk metrics for a holding"""
        try:
            current_price = market_data.get('current_price', 0)
            cost_basis = holding_info.get('cost_basis', 0)
            
            # Calculate basic risk metrics
            price_change_percent = ((current_price - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0
            
            # Determine risk level based on price change and volatility
            if abs(price_change_percent) > 20:
                risk_level = "HIGH"
            elif abs(price_change_percent) > 10:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            return {
                "price_change_percent": round(price_change_percent, 2),
                "risk_level": risk_level,
                "current_price": current_price,
                "cost_basis": cost_basis,
                "unrealized_gain_loss": (current_price - cost_basis) * holding_info.get('quantity', 0)
            }
        except Exception:
            return {"risk_level": "UNKNOWN", "error": "Failed to calculate risk metrics"}
    
    def _generate_trading_signals(self, symbol: str, technical_indicators: Dict, ai_recommendation: Dict) -> Dict:
        """Generate trading signals based on technical and AI analysis"""
        try:
            # Handle both string and dict AI recommendations
            if isinstance(ai_recommendation, str):
                # Extract recommendation from string
                ai_rec = "HOLD"  # Default
                if "BUY" in ai_recommendation.upper():
                    ai_rec = "BUY"
                elif "SELL" in ai_recommendation.upper():
                    ai_rec = "SELL"
                
                signals = {
                    "recommendation": ai_rec,
                    "confidence": 0.7,
                    "technical_signal": "NEUTRAL", 
                    "combined_signal": "HOLD"
                }
            else:
                signals = {
                    "recommendation": ai_recommendation.get('recommendation', 'HOLD') if ai_recommendation else 'HOLD',
                    "confidence": ai_recommendation.get('confidence', 0) if ai_recommendation else 0,
                    "technical_signal": "NEUTRAL",
                    "combined_signal": "HOLD"
                }
            
            # Basic technical signal logic
            rsi = technical_indicators.get('rsi')
            if rsi:
                if rsi > 70:
                    signals["technical_signal"] = "SELL"
                elif rsi < 30:
                    signals["technical_signal"] = "BUY"
            
            # Combine AI and technical signals
            ai_rec = signals["recommendation"]
            tech_signal = signals["technical_signal"]
            
            if ai_rec == tech_signal:
                signals["combined_signal"] = ai_rec
            else:
                signals["combined_signal"] = "HOLD"  # Conservative when signals conflict
            
            return signals
        except Exception:
            return {"recommendation": "HOLD", "error": "Failed to generate trading signals"}
    
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
        """Get current market status for analysis timing with detailed information"""
        try:
            # Get comprehensive market status from scheduler
            market_status = self.market_scheduler.get_market_status_summary()
            
            # Add additional API-friendly fields
            market_status.update({
                "status": "operational",
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
            
            return market_status
            
        except Exception as e:
            # Fallback to simple status if market scheduler fails
            print(f"Warning: Market scheduler failed, using fallback status: {e}")
            return {
                "current_session": "market_closed",
                "is_trading_day": True,
                "market_timezone": "America/New_York", 
                "status": "limited",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "note": f"Using simplified market status due to error: {str(e)}"
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

    def _make_json_serializable(self, obj: Any) -> Any:
        """Convert datetime objects and other non-serializable objects to JSON-serializable format"""
        if isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif hasattr(obj, 'isoformat'):  # pandas Timestamp
            return obj.isoformat()
        elif hasattr(obj, 'to_pydatetime'):  # pandas Timestamp
            return obj.to_pydatetime().isoformat()
        else:
            return obj 

    def _log_progress(self, message: str, level: str = "info", data: Dict = None):
        """Log progress message with timestamp"""
        timestamp = datetime.utcnow()
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "message": message,
            "level": level,
            "data": data or {}
        }
        
        self.progress_logs.append(log_entry)
        print(f"[{timestamp.strftime('%H:%M:%S')}] {message}")
    
    def _update_progress_logs(self):
        """Update progress logs in database (called periodically during analysis)"""
        if self.current_session_id:
            try:
                # Use a separate database session for progress updates
                # This ensures updates are immediately visible to other sessions
                from app.database import SessionLocal
                progress_db = SessionLocal()
                try:
                    session = progress_db.query(AnalysisSession).filter(
                        AnalysisSession.id == self.current_session_id
                    ).first()
                    if session:
                        # Update progress logs
                        session.progress_logs = self.progress_logs.copy()
                        progress_db.commit()  # Commit immediately for real-time updates
                finally:
                    progress_db.close()
            except Exception as e:
                print(f"Failed to update progress logs: {e}")

    def get_session_progress(self, session_id: str) -> Dict[str, Any]:
        """Get detailed progress for a session"""
        try:
            session = self.db.query(AnalysisSession).filter(
                AnalysisSession.id == session_id
            ).first()
            
            if not session:
                return {"error": "Session not found"}
            
            return {
                "session_id": str(session.id),
                "status": session.status,
                "progress_logs": session.progress_logs or [],
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "error_message": session.error_message
            }
        except Exception as e:
            return {"error": f"Failed to get progress: {str(e)}"} 