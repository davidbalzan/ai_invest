import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import hashlib

class InvestmentDataStorage:
    """Manages historical storage and retrieval of investment analysis data"""
    
    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = storage_dir
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories for data storage"""
        directories = [
            self.storage_dir,
            os.path.join(self.storage_dir, "daily_reports"),
            os.path.join(self.storage_dir, "stock_data"),
            os.path.join(self.storage_dir, "analysis_history"),
            os.path.join(self.storage_dir, "market_sentiment"),
            os.path.join(self.storage_dir, "portfolio_snapshots")
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def store_daily_report(self, analysis_results: Dict, portfolio_holdings: Dict, 
                          metadata: Dict = None, strategy_info: Dict = None) -> str:
        """Store complete daily analysis report in JSON format"""
        timestamp = datetime.now(timezone.utc)
        report_id = self._generate_report_id(timestamp)
        
        # Import here to avoid circular import
        from data_fetcher import get_stock_data
        
        # Comprehensive report structure
        report_data = {
            "report_id": report_id,
            "timestamp": timestamp.isoformat(),
            "date": timestamp.strftime("%Y-%m-%d"),
            "time": timestamp.strftime("%H:%M:%S"),
            "metadata": metadata or {},
            
            # Strategy Configuration
            "strategy": strategy_info or {},
            
            # Portfolio Overview
            "portfolio": {
                "total_value": sum(result.get('current_value', 0) for result in analysis_results.values()),
                "total_invested": sum(result.get('total_cost', 0) for result in analysis_results.values()),
                "total_profit_loss": 0,  # Will be calculated
                "total_return_percent": 0,  # Will be calculated
                "position_count": len(analysis_results),
                "profitable_positions": sum(1 for result in analysis_results.values() 
                                           if result.get('profit_loss', 0) > 0),
                "holdings_summary": portfolio_holdings
            },
            
            # Individual Stock Analysis
            "stocks": {},
            
            # Market Analysis
            "market_analysis": {
                "sentiment_distribution": {},
                "technical_overview": {},
                "risk_assessment": {},
                "recommendations_summary": {}
            },
            
            # Performance Metrics
            "performance": {
                "risk_alerts": [],
                "best_performer": {},
                "worst_performer": {}
            }
        }
        
        # Calculate portfolio totals
        total_profit_loss = sum(result.get('profit_loss', 0) for result in analysis_results.values())
        total_invested = sum(result.get('total_cost', 0) for result in analysis_results.values())
        total_return_percent = (total_profit_loss / total_invested * 100) if total_invested > 0 else 0
        
        report_data["portfolio"]["total_profit_loss"] = total_profit_loss
        report_data["portfolio"]["total_return_percent"] = total_return_percent
        
        # Process individual stocks
        for symbol, result in analysis_results.items():
            # Get historical stock data for charting (last 6 months for performance)
            historical_data = None
            chart_data = None
            try:
                stock_data = get_stock_data(symbol, period="6mo")
                if stock_data is not None and not stock_data.empty:
                    # Prepare chart data (last 90 days for better performance)
                    recent_data = stock_data.tail(90)
                    chart_data = {
                        "dates": recent_data.index.strftime('%Y-%m-%d').tolist(),
                        "prices": recent_data['Close'].round(2).tolist(),
                        "volumes": recent_data['Volume'].tolist(),
                        "ma_20": recent_data['Close'].rolling(window=20).mean().round(2).fillna(0).tolist(),
                        "ma_50": recent_data['Close'].rolling(window=50).mean().round(2).fillna(0).tolist()
                    }
            except Exception as e:
                print(f"Warning: Could not fetch chart data for {symbol}: {e}")
            
            stock_data = {
                "symbol": symbol,
                "current_price": result.get('current_price', 0),
                "cost_basis": result.get('cost_basis', 0),
                "quantity": result.get('quantity', 0),
                "current_value": result.get('current_value', 0),
                "total_cost": result.get('total_cost', 0),
                "profit_loss": result.get('profit_loss', 0),
                "profit_loss_percent": result.get('profit_loss_percent', 0),
                
                # Technical Indicators
                "technical": {
                    "rsi": result.get('rsi', 0),
                    "ma_20": result.get('ma_20', 0),
                    "ma_50": result.get('ma_50', 0),
                    "macd": result.get('macd', 0),
                    "signal": result.get('signal', 0)
                },
                
                # Sentiment Analysis
                "sentiment": {
                    "overall": result.get('sentiment', 'neutral'),
                    "score": result.get('sentiment_score', 0),
                    "articles_analyzed": result.get('articles_analyzed', 0)
                },
                
                # AI Analysis
                "ai_analysis": {
                    "recommendation": result.get('recommendation', ''),
                    "recommendation_type": self._extract_recommendation_type(result.get('recommendation', '')),
                    "confidence": result.get('confidence', 0)
                },
                
                # Risk Metrics
                "risk": {
                    "volatility": result.get('volatility', 0),
                    "beta": result.get('beta', 1.0),
                    "risk_level": self._calculate_risk_level(result)
                },
                
                # Historical chart data for HTML rendering
                "chart_data": chart_data
            }
            
            report_data["stocks"][symbol] = stock_data
        
        # Generate market analysis
        report_data["market_analysis"] = self._generate_market_analysis(analysis_results)
        report_data["performance"] = self._generate_performance_metrics(analysis_results)
        
        # Store the report
        filename = f"{report_id}.json"
        filepath = os.path.join(self.storage_dir, "daily_reports", filename)
        
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        # Also store individual stock snapshots
        for symbol, stock_data in report_data["stocks"].items():
            self._store_stock_snapshot(symbol, stock_data, timestamp)
        
        return report_id
    
    def load_report(self, report_id: str) -> Optional[Dict]:
        """Load a specific report by ID"""
        filepath = os.path.join(self.storage_dir, "daily_reports", f"{report_id}.json")
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def get_latest_report(self) -> Optional[Dict]:
        """Get the most recent report"""
        reports_dir = os.path.join(self.storage_dir, "daily_reports")
        
        if not os.path.exists(reports_dir):
            return None
        
        reports = [f for f in os.listdir(reports_dir) if f.endswith('.json')]
        
        if not reports:
            return None
        
        # Sort by filename (which includes timestamp)
        latest_report = sorted(reports)[-1]
        return self.load_report(latest_report[:-5])  # Remove .json extension
    
    def get_historical_reports(self, days: int = 30) -> List[Dict]:
        """Get historical reports for specified number of days"""
        reports_dir = os.path.join(self.storage_dir, "daily_reports")
        
        if not os.path.exists(reports_dir):
            return []
        
        reports = []
        report_files = [f for f in os.listdir(reports_dir) if f.endswith('.json')]
        
        # Sort by date (newest first)
        report_files.sort(reverse=True)
        
        for report_file in report_files[:days]:
            report_id = report_file[:-5]  # Remove .json
            report = self.load_report(report_id)
            if report:
                reports.append(report)
        
        return reports
    
    def get_stock_history(self, symbol: str, days: int = 30) -> List[Dict]:
        """Get historical data for a specific stock"""
        stock_dir = os.path.join(self.storage_dir, "stock_data", symbol)
        
        if not os.path.exists(stock_dir):
            return []
        
        history = []
        stock_files = [f for f in os.listdir(stock_dir) if f.endswith('.json')]
        
        # Sort by date (newest first)
        stock_files.sort(reverse=True)
        
        for stock_file in stock_files[:days]:
            filepath = os.path.join(stock_dir, stock_file)
            with open(filepath, 'r') as f:
                history.append(json.load(f))
        
        return history
    
    def generate_trend_analysis(self, symbol: str, days: int = 30) -> Dict:
        """Generate trend analysis for a stock over time"""
        history = self.get_stock_history(symbol, days)
        
        if len(history) < 2:
            return {"error": "Insufficient historical data"}
        
        # Calculate trends
        prices = [h['current_price'] for h in history]
        rsi_values = [h['technical']['rsi'] for h in history]
        sentiment_scores = [h['sentiment']['score'] for h in history]
        
        return {
            "symbol": symbol,
            "analysis_period": f"{len(history)} days",
            "price_trend": {
                "start_price": prices[-1],
                "end_price": prices[0],
                "change": prices[0] - prices[-1],
                "change_percent": ((prices[0] - prices[-1]) / prices[-1] * 100) if prices[-1] != 0 else 0,
                "trend": "bullish" if prices[0] > prices[-1] else "bearish"
            },
            "rsi_trend": {
                "average": sum(rsi_values) / len(rsi_values),
                "current": rsi_values[0],
                "previous": rsi_values[1] if len(rsi_values) > 1 else rsi_values[0],
                "volatility": max(rsi_values) - min(rsi_values)
            },
            "sentiment_trend": {
                "average": sum(sentiment_scores) / len(sentiment_scores),
                "current": sentiment_scores[0],
                "improving": sentiment_scores[0] > sentiment_scores[-1]
            }
        }
    
    def _generate_report_id(self, timestamp: datetime) -> str:
        """Generate unique report ID"""
        date_str = timestamp.strftime("%Y%m%d_%H%M%S")
        hash_input = f"{timestamp.isoformat()}_{timestamp.microsecond}"
        hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"report_{date_str}_{hash_suffix}"
    
    def _store_stock_snapshot(self, symbol: str, stock_data: Dict, timestamp: datetime):
        """Store individual stock snapshot"""
        stock_dir = os.path.join(self.storage_dir, "stock_data", symbol)
        os.makedirs(stock_dir, exist_ok=True)
        
        filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(stock_dir, filename)
        
        snapshot = {
            "timestamp": timestamp.isoformat(),
            **stock_data
        }
        
        with open(filepath, 'w') as f:
            json.dump(snapshot, f, indent=2, default=str)
    
    def _extract_recommendation_type(self, recommendation: str) -> str:
        """Extract BUY/HOLD/SELL from recommendation text"""
        rec_upper = recommendation.upper()
        if 'BUY' in rec_upper:
            return 'BUY'
        elif 'SELL' in rec_upper:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _calculate_risk_level(self, result: Dict) -> str:
        """Calculate risk level based on various factors"""
        rsi = result.get('rsi', 50)
        profit_loss_percent = result.get('profit_loss_percent', 0)
        
        risk_score = 0
        
        # RSI risk
        if rsi > 70 or rsi < 30:
            risk_score += 2
        elif rsi > 60 or rsi < 40:
            risk_score += 1
        
        # Loss risk
        if profit_loss_percent < -10:
            risk_score += 3
        elif profit_loss_percent < -5:
            risk_score += 2
        elif profit_loss_percent < 0:
            risk_score += 1
        
        if risk_score >= 4:
            return "HIGH"
        elif risk_score >= 2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_market_analysis(self, analysis_results: Dict) -> Dict:
        """Generate market-wide analysis"""
        sentiments = [result.get('sentiment', 'neutral') for result in analysis_results.values()]
        rsi_values = [result.get('rsi', 50) for result in analysis_results.values()]
        recommendations = [self._extract_recommendation_type(result.get('recommendation', '')) 
                          for result in analysis_results.values()]
        
        return {
            "sentiment_distribution": {
                "positive": sentiments.count('positive'),
                "neutral": sentiments.count('neutral'),
                "negative": sentiments.count('negative')
            },
            "technical_overview": {
                "average_rsi": sum(rsi_values) / len(rsi_values) if rsi_values else 50,
                "overbought_count": sum(1 for rsi in rsi_values if rsi > 70),
                "oversold_count": sum(1 for rsi in rsi_values if rsi < 30)
            },
            "recommendations_summary": {
                "buy_signals": recommendations.count('BUY'),
                "hold_signals": recommendations.count('HOLD'),
                "sell_signals": recommendations.count('SELL')
            }
        }
    
    def _generate_performance_metrics(self, analysis_results: Dict) -> Dict:
        """Generate performance metrics summary"""
        if not analysis_results:
            return {}
        
        # Find best and worst performers
        by_return = sorted(analysis_results.items(), 
                          key=lambda x: x[1].get('profit_loss_percent', 0), reverse=True)
        
        by_rsi = sorted(analysis_results.items(), 
                       key=lambda x: x[1].get('rsi', 50), reverse=True)
        
        return {
            "best_performer": {
                "symbol": by_return[0][0],
                "return_percent": by_return[0][1].get('profit_loss_percent', 0)
            } if by_return else None,
            "worst_performer": {
                "symbol": by_return[-1][0],
                "return_percent": by_return[-1][1].get('profit_loss_percent', 0)
            } if by_return else None,
            "highest_rsi": {
                "symbol": by_rsi[0][0],
                "rsi": by_rsi[0][1].get('rsi', 50)
            } if by_rsi else None,
            "lowest_rsi": {
                "symbol": by_rsi[-1][0],
                "rsi": by_rsi[-1][1].get('rsi', 50)
            } if by_rsi else None,
            "risk_alerts": [
                {"symbol": symbol, "reason": "High RSI", "value": result.get('rsi', 50)}
                for symbol, result in analysis_results.items()
                if result.get('rsi', 50) > 75
            ]
        } 
    
    def get_historical_reports(self, days_back: int = 30, symbol: str = None) -> List[Dict]:
        """Get historical reports for backtesting and analysis"""
        try:
            daily_reports_dir = os.path.join(self.storage_dir, "daily_reports")
            if not os.path.exists(daily_reports_dir):
                return []
            
            # Calculate cutoff date
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            historical_reports = []
            
            for filename in os.listdir(daily_reports_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(daily_reports_dir, filename)
                    
                    try:
                        with open(filepath, 'r') as f:
                            report_data = json.load(f)
                        
                        report_date = datetime.fromisoformat(report_data['timestamp'])
                        
                        if report_date >= cutoff_date:
                            # Filter by symbol if specified
                            if symbol is None or symbol in report_data.get('stocks', {}):
                                historical_reports.append(report_data)
                    except Exception as e:
                        print(f"Error loading report {filename}: {e}")
                        continue
            
            # Sort by date (newest first)
            historical_reports.sort(key=lambda x: x['timestamp'], reverse=True)
            return historical_reports
            
        except Exception as e:
            print(f"Error loading historical reports: {e}")
            return []
    
    def get_sentiment_history(self, symbol: str, days_back: int = 30) -> List[Dict]:
        """Get historical sentiment data for a specific symbol"""
        try:
            historical_reports = self.get_historical_reports(days_back, symbol)
            sentiment_history = []
            
            for report in historical_reports:
                if symbol in report.get('stocks', {}):
                    stock_data = report['stocks'][symbol]
                    sentiment_history.append({
                        'date': report['date'],
                        'timestamp': report['timestamp'],
                        'sentiment': stock_data.get('sentiment'),
                        'sentiment_score': stock_data.get('sentiment_score', 0),
                        'news_articles_count': stock_data.get('news_articles_count', 0),
                        'price': stock_data.get('current_price'),
                        'recommendation': stock_data.get('ai_recommendation', {}).get('action')
                    })
            
            return sentiment_history
            
        except Exception as e:
            print(f"Error loading sentiment history for {symbol}: {e}")
            return []
    
    def get_recommendation_history(self, symbol: str = None, days_back: int = 30) -> List[Dict]:
        """Get historical AI recommendations for validation"""
        try:
            historical_reports = self.get_historical_reports(days_back, symbol)
            recommendation_history = []
            
            for report in historical_reports:
                stocks_to_process = [symbol] if symbol else report.get('stocks', {}).keys()
                
                for stock_symbol in stocks_to_process:
                    if stock_symbol in report.get('stocks', {}):
                        stock_data = report['stocks'][stock_symbol]
                        ai_rec = stock_data.get('ai_recommendation', {})
                        
                        recommendation_history.append({
                            'date': report['date'],
                            'timestamp': report['timestamp'],
                            'symbol': stock_symbol,
                            'recommendation': ai_rec.get('action'),
                            'confidence': ai_rec.get('confidence', 0),
                            'reasoning': ai_rec.get('reasoning'),
                            'price_at_recommendation': stock_data.get('current_price'),
                            'market_session': report.get('metadata', {}).get('market_session'),
                            'analysis_type': report.get('metadata', {}).get('scheduled_analysis_type')
                        })
            
            return recommendation_history
            
        except Exception as e:
            print(f"Error loading recommendation history: {e}")
            return []
    
    def calculate_prediction_accuracy(self, symbol: str, days_back: int = 30, 
                                    prediction_horizon: int = 5) -> Dict:
        """Calculate accuracy of AI recommendations over time"""
        try:
            recommendations = self.get_recommendation_history(symbol, days_back)
            
            if len(recommendations) < 2:
                return {'error': 'Insufficient historical data for accuracy calculation'}
            
            correct_predictions = 0
            total_predictions = 0
            prediction_details = []
            
            for i, rec in enumerate(recommendations[:-prediction_horizon]):
                # Find the price after prediction_horizon days
                target_date = datetime.fromisoformat(rec['timestamp']) + timedelta(days=prediction_horizon)
                
                future_price = None
                for future_rec in recommendations[i+1:]:
                    future_date = datetime.fromisoformat(future_rec['timestamp'])
                    if future_date >= target_date:
                        future_price = future_rec['price_at_recommendation']
                        break
                
                if future_price and rec['price_at_recommendation']:
                    price_change_percent = ((future_price - rec['price_at_recommendation']) / 
                                          rec['price_at_recommendation']) * 100
                    
                    # Determine if prediction was correct
                    correct = False
                    if rec['recommendation'] == 'BUY' and price_change_percent > 2:  # 2% threshold
                        correct = True
                    elif rec['recommendation'] == 'SELL' and price_change_percent < -2:
                        correct = True
                    elif rec['recommendation'] == 'HOLD' and abs(price_change_percent) <= 5:
                        correct = True
                    
                    if correct:
                        correct_predictions += 1
                    total_predictions += 1
                    
                    prediction_details.append({
                        'date': rec['date'],
                        'recommendation': rec['recommendation'],
                        'initial_price': rec['price_at_recommendation'],
                        'future_price': future_price,
                        'price_change_percent': price_change_percent,
                        'correct': correct,
                        'confidence': rec['confidence']
                    })
            
            accuracy = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
            
            return {
                'symbol': symbol,
                'accuracy_percent': accuracy,
                'correct_predictions': correct_predictions,
                'total_predictions': total_predictions,
                'prediction_horizon_days': prediction_horizon,
                'analysis_period_days': days_back,
                'prediction_details': prediction_details
            }
            
        except Exception as e:
            print(f"Error calculating prediction accuracy: {e}")
            return {'error': str(e)}