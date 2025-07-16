import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import os
from data_storage import InvestmentDataStorage
from data_fetcher import get_stock_data, calculate_technical_indicators
from ai_analyzer import get_sentiment_analysis, get_ai_recommendation
from strategy_manager import StrategyManager, InvestmentStrategy

@dataclass
class BacktestResult:
    """Results from a backtest scenario"""
    strategy_name: str
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_gain: float
    avg_loss: float
    start_date: str
    end_date: str
    final_portfolio_value: float
    benchmark_return: float

@dataclass
class WhatIfScenario:
    """Configuration for what-if scenario testing"""
    name: str
    description: str
    parameters: Dict
    
class BacktestEngine:
    """Advanced backtesting engine for strategy validation and what-if analysis"""
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.storage = InvestmentDataStorage()
        self.strategy_manager = StrategyManager()
        
    def get_historical_data(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Fetch historical data for backtesting"""
        historical_data = {}
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date)
                
                if not data.empty:
                    # Add technical indicators
                    data['RSI'] = self._calculate_rsi(data['Close'])
                    data['MA_20'] = data['Close'].rolling(window=20).mean()
                    data['MA_50'] = data['Close'].rolling(window=50).mean()
                    
                    historical_data[symbol] = data
                else:
                    print(f"⚠️ No data found for {symbol}")
                    
            except Exception as e:
                print(f"❌ Error fetching data for {symbol}: {e}")
                
        return historical_data
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def simulate_strategy(self, 
                         symbols: List[str], 
                         start_date: str, 
                         end_date: str,
                         strategy: InvestmentStrategy,
                         portfolio_holdings: Dict = None) -> BacktestResult:
        """Simulate a strategy over historical data"""
        
        print(f"📊 Running backtest: {strategy.name}")
        print(f"📅 Period: {start_date} to {end_date}")
        print(f"🎯 Strategy: {strategy.risk_profile.value.title()}")
        
        # Get historical data
        historical_data = self.get_historical_data(symbols, start_date, end_date)
        
        if not historical_data:
            raise ValueError("No historical data available for backtesting")
        
        # Initialize portfolio
        portfolio_value = self.initial_capital
        positions = {}
        cash = self.initial_capital
        trades = []
        daily_values = []
        
        # Get all trading dates
        all_dates = sorted(set().union(*[data.index for data in historical_data.values()]))
        
        for date in all_dates:
            daily_portfolio_value = cash
            
            # Update position values
            for symbol, shares in positions.items():
                if symbol in historical_data and date in historical_data[symbol].index:
                    current_price = historical_data[symbol].loc[date, 'Close']
                    daily_portfolio_value += shares * current_price
            
            daily_values.append({
                'date': date,
                'portfolio_value': daily_portfolio_value,
                'cash': cash,
                'positions': positions.copy()
            })
            
            # Generate trading signals for each symbol
            for symbol in symbols:
                if symbol not in historical_data or date not in historical_data[symbol].index:
                    continue
                    
                current_data = historical_data[symbol].loc[date]
                current_price = current_data['Close']
                rsi = current_data.get('RSI', 50)
                ma_20 = current_data.get('MA_20', current_price)
                ma_50 = current_data.get('MA_50', current_price)
                
                # Apply strategy rules
                signal = self._generate_signal(symbol, current_price, rsi, ma_20, ma_50, strategy)
                
                if signal == 'BUY' and cash >= current_price * 100:  # Buy 100 shares minimum
                    # Calculate position size based on strategy
                    max_position_value = daily_portfolio_value * (strategy.max_position_size_percent / 100)
                    shares_to_buy = min(int(max_position_value / current_price), int(cash / current_price))
                    
                    if shares_to_buy > 0:
                        cost = shares_to_buy * current_price
                        cash -= cost
                        
                        if symbol in positions:
                            positions[symbol] += shares_to_buy
                        else:
                            positions[symbol] = shares_to_buy
                        
                        trades.append({
                            'date': date,
                            'symbol': symbol,
                            'action': 'BUY',
                            'shares': shares_to_buy,
                            'price': current_price,
                            'cost': cost
                        })
                
                elif signal == 'SELL' and symbol in positions and positions[symbol] > 0:
                    shares_to_sell = positions[symbol]
                    revenue = shares_to_sell * current_price
                    cash += revenue
                    
                    trades.append({
                        'date': date,
                        'symbol': symbol,
                        'action': 'SELL',
                        'shares': shares_to_sell,
                        'price': current_price,
                        'revenue': revenue
                    })
                    
                    del positions[symbol]
        
        # Calculate final portfolio value
        final_value = cash
        for symbol, shares in positions.items():
            if symbol in historical_data:
                final_price = historical_data[symbol].iloc[-1]['Close']
                final_value += shares * final_price
        
        # Calculate performance metrics
        return self._calculate_backtest_metrics(
            daily_values, trades, final_value, start_date, end_date, strategy.name
        )
    
    def _generate_signal(self, symbol: str, price: float, rsi: float, ma_20: float, 
                        ma_50: float, strategy: InvestmentStrategy) -> str:
        """Generate buy/sell/hold signal based on strategy parameters"""
        
        # RSI-based signals
        if rsi < strategy.rsi_oversold_threshold and price > ma_20:
            return 'BUY'
        elif rsi > strategy.rsi_overbought_threshold:
            return 'SELL'
        
        # Moving average crossover
        if ma_20 > ma_50 and price > ma_20:
            return 'BUY'
        elif ma_20 < ma_50 and price < ma_20:
            return 'SELL'
        
        return 'HOLD'
    
    def _calculate_backtest_metrics(self, daily_values: List[Dict], trades: List[Dict], 
                                  final_value: float, start_date: str, end_date: str,
                                  strategy_name: str) -> BacktestResult:
        """Calculate comprehensive backtest performance metrics"""
        
        # Calculate returns
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        
        # Calculate annualized return
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        years = (end - start).days / 365.25
        annualized_return = (pow(final_value / self.initial_capital, 1/years) - 1) * 100 if years > 0 else 0
        
        # Calculate max drawdown
        portfolio_values = [d['portfolio_value'] for d in daily_values]
        peak = portfolio_values[0]
        max_drawdown = 0
        
        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        # Calculate Sharpe ratio (simplified, assuming 2% risk-free rate)
        if len(portfolio_values) > 1:
            returns = [(portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1] 
                      for i in range(1, len(portfolio_values))]
            if returns:
                avg_return = np.mean(returns) * 252  # Annualized
                std_return = np.std(returns) * np.sqrt(252)  # Annualized
                sharpe_ratio = (avg_return - 0.02) / std_return if std_return > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        # Analyze trades
        winning_trades = sum(1 for trade in trades if trade['action'] == 'SELL' and 
                           any(t['action'] == 'BUY' and t['symbol'] == trade['symbol'] 
                               and t['price'] < trade['price'] for t in trades))
        
        total_trades = len([t for t in trades if t['action'] == 'SELL'])
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate average gains/losses
        gains = []
        losses = []
        for trade in trades:
            if trade['action'] == 'SELL':
                # Find corresponding buy trade
                buy_trades = [t for t in trades if t['action'] == 'BUY' and 
                             t['symbol'] == trade['symbol'] and t['date'] < trade['date']]
                if buy_trades:
                    buy_price = buy_trades[-1]['price']  # Most recent buy
                    pnl_percent = (trade['price'] - buy_price) / buy_price * 100
                    if pnl_percent > 0:
                        gains.append(pnl_percent)
                    else:
                        losses.append(abs(pnl_percent))
        
        avg_gain = np.mean(gains) if gains else 0
        avg_loss = np.mean(losses) if losses else 0
        
        # Calculate benchmark (simple buy and hold)
        benchmark_return = 0  # Would need market index data for proper benchmark
        
        return BacktestResult(
            strategy_name=strategy_name,
            total_return=total_return,
            annualized_return=annualized_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_gain=avg_gain,
            avg_loss=avg_loss,
            start_date=start_date,
            end_date=end_date,
            final_portfolio_value=final_value,
            benchmark_return=benchmark_return
        )
    
    def run_what_if_scenarios(self, symbols: List[str], start_date: str, end_date: str,
                             base_strategy: InvestmentStrategy) -> Dict[str, BacktestResult]:
        """Run multiple what-if scenarios to test parameter sensitivity"""
        
        scenarios = [
            WhatIfScenario(
                "Conservative RSI",
                "More conservative RSI thresholds (25/75 vs 30/70)",
                {"rsi_oversold_threshold": 25, "rsi_overbought_threshold": 75}
            ),
            WhatIfScenario(
                "Aggressive RSI", 
                "More aggressive RSI thresholds (35/65 vs 30/70)",
                {"rsi_oversold_threshold": 35, "rsi_overbought_threshold": 65}
            ),
            WhatIfScenario(
                "Tighter Stop Loss",
                "Reduce stop loss from -10% to -5%",
                {"stop_loss_percent": -5.0}
            ),
            WhatIfScenario(
                "Wider Stop Loss",
                "Increase stop loss from -10% to -15%", 
                {"stop_loss_percent": -15.0}
            ),
            WhatIfScenario(
                "Higher Take Profit",
                "Increase take profit from 20% to 30%",
                {"take_profit_percent": 30.0}
            ),
            WhatIfScenario(
                "Smaller Positions",
                "Reduce max position size from 15% to 10%",
                {"max_position_size_percent": 10.0}
            ),
            WhatIfScenario(
                "Larger Positions",
                "Increase max position size from 15% to 20%",
                {"max_position_size_percent": 20.0}
            )
        ]
        
        results = {}
        
        # Run base strategy first
        print(f"\n🔬 Running What-If Analysis")
        print(f"📊 Base Strategy: {base_strategy.name}")
        
        base_result = self.simulate_strategy(symbols, start_date, end_date, base_strategy)
        results["Base Strategy"] = base_result
        
        # Run scenario variations
        for scenario in scenarios:
            print(f"\n🧪 Testing: {scenario.name}")
            
            # Create modified strategy
            modified_strategy = base_strategy
            for param, value in scenario.parameters.items():
                setattr(modified_strategy, param, value)
            
            modified_strategy.name = f"{base_strategy.name} - {scenario.name}"
            
            try:
                result = self.simulate_strategy(symbols, start_date, end_date, modified_strategy)
                results[scenario.name] = result
                
                # Show comparison
                improvement = result.total_return - base_result.total_return
                print(f"   📈 Total Return: {result.total_return:.2f}% ({improvement:+.2f}% vs base)")
                print(f"   📉 Max Drawdown: {result.max_drawdown:.2f}%")
                print(f"   🎯 Win Rate: {result.win_rate:.1f}%")
                
            except Exception as e:
                print(f"   ❌ Error testing {scenario.name}: {e}")
        
        return results
    
    def validate_historical_predictions(self, days_back: int = 30) -> Dict:
        """Validate our historical AI predictions against actual outcomes"""
        print(f"\n🔍 Validating AI Predictions (Last {days_back} days)")
        
        validation_results = {}
        
        # Get all symbols from historical data
        historical_reports = self.storage.get_historical_reports(days_back)
        
        if not historical_reports:
            return {"error": "No historical data available for validation"}
        
        # Extract unique symbols
        all_symbols = set()
        for report in historical_reports:
            all_symbols.update(report.get('stocks', {}).keys())
        
        # Validate predictions for each symbol
        for symbol in all_symbols:
            accuracy_result = self.storage.calculate_prediction_accuracy(symbol, days_back, 5)
            if 'error' not in accuracy_result:
                validation_results[symbol] = accuracy_result
                
                print(f"📊 {symbol}: {accuracy_result['accuracy_percent']:.1f}% accuracy "
                      f"({accuracy_result['correct_predictions']}/{accuracy_result['total_predictions']} predictions)")
        
        # Calculate overall accuracy
        if validation_results:
            total_correct = sum(r['correct_predictions'] for r in validation_results.values())
            total_predictions = sum(r['total_predictions'] for r in validation_results.values())
            overall_accuracy = (total_correct / total_predictions * 100) if total_predictions > 0 else 0
            
            validation_results['overall'] = {
                'accuracy_percent': overall_accuracy,
                'total_correct': total_correct,
                'total_predictions': total_predictions
            }
            
            print(f"\n🎯 Overall Accuracy: {overall_accuracy:.1f}% ({total_correct}/{total_predictions})")
        
        return validation_results
    
    def generate_backtest_report(self, results: Dict[str, BacktestResult], 
                               output_file: str = None) -> str:
        """Generate a comprehensive backtesting report"""
        
        if not results:
            return "No backtest results to report"
        
        report_lines = []
        report_lines.append("📊 BACKTESTING & WHAT-IF ANALYSIS REPORT")
        report_lines.append("=" * 60)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Sort results by total return
        sorted_results = sorted(results.items(), key=lambda x: x[1].total_return, reverse=True)
        
        report_lines.append("🏆 PERFORMANCE RANKING")
        report_lines.append("-" * 30)
        
        for i, (name, result) in enumerate(sorted_results):
            rank_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
            report_lines.append(f"{rank_emoji} {name}")
            report_lines.append(f"   Return: {result.total_return:.2f}% (Ann: {result.annualized_return:.2f}%)")
            report_lines.append(f"   Drawdown: {result.max_drawdown:.2f}% | Sharpe: {result.sharpe_ratio:.2f}")
            report_lines.append(f"   Win Rate: {result.win_rate:.1f}% | Trades: {result.total_trades}")
            report_lines.append("")
        
        # Detailed analysis
        report_lines.append("📈 DETAILED ANALYSIS")
        report_lines.append("-" * 30)
        
        for name, result in results.items():
            report_lines.append(f"\n🔍 {name}")
            report_lines.append(f"   Period: {result.start_date} to {result.end_date}")
            report_lines.append(f"   Total Return: {result.total_return:.2f}%")
            report_lines.append(f"   Annualized Return: {result.annualized_return:.2f}%")
            report_lines.append(f"   Max Drawdown: {result.max_drawdown:.2f}%")
            report_lines.append(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
            report_lines.append(f"   Total Trades: {result.total_trades}")
            report_lines.append(f"   Winning Trades: {result.winning_trades}")
            report_lines.append(f"   Losing Trades: {result.losing_trades}")
            report_lines.append(f"   Win Rate: {result.win_rate:.1f}%")
            report_lines.append(f"   Avg Gain: {result.avg_gain:.2f}%")
            report_lines.append(f"   Avg Loss: {result.avg_loss:.2f}%")
            report_lines.append(f"   Final Portfolio Value: ${result.final_portfolio_value:,.2f}")
        
        # Key insights
        if len(results) > 1:
            base_result = results.get("Base Strategy")
            if base_result:
                report_lines.append("\n💡 KEY INSIGHTS")
                report_lines.append("-" * 30)
                
                best_scenario = max(results.items(), key=lambda x: x[1].total_return)
                worst_scenario = min(results.items(), key=lambda x: x[1].total_return)
                
                report_lines.append(f"🎯 Best Scenario: {best_scenario[0]}")
                report_lines.append(f"   Improvement: +{best_scenario[1].total_return - base_result.total_return:.2f}% vs base")
                
                report_lines.append(f"⚠️ Worst Scenario: {worst_scenario[0]}")
                report_lines.append(f"   Decline: {worst_scenario[1].total_return - base_result.total_return:.2f}% vs base")
                
                # Risk-adjusted analysis
                best_sharpe = max(results.items(), key=lambda x: x[1].sharpe_ratio)
                report_lines.append(f"📊 Best Risk-Adjusted: {best_sharpe[0]} (Sharpe: {best_sharpe[1].sharpe_ratio:.2f})")
        
        report_text = "\n".join(report_lines)
        
        # Save to file if specified
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(report_text)
                print(f"📄 Report saved to: {output_file}")
            except Exception as e:
                print(f"❌ Error saving report: {e}")
        
        return report_text
    
    def analyze_sentiment_predictive_power(self, symbol: str, days_back: int = 30) -> Dict:
        """Analyze how well sentiment predicts future price movements"""
        print(f"\n🧠 Analyzing Sentiment Predictive Power: {symbol}")
        
        sentiment_history = self.storage.get_sentiment_history(symbol, days_back)
        
        if len(sentiment_history) < 5:
            return {"error": "Insufficient sentiment history"}
        
        # Analyze sentiment vs future returns
        predictive_analysis = []
        
        for i, record in enumerate(sentiment_history[:-3]):  # Leave 3 days for future analysis
            current_sentiment = record['sentiment']
            current_price = record['price']
            
            # Look at price 3 days later
            future_record = sentiment_history[i + 3] if i + 3 < len(sentiment_history) else None
            
            if future_record and current_price and future_record['price']:
                future_return = (future_record['price'] - current_price) / current_price * 100
                
                predictive_analysis.append({
                    'date': record['date'],
                    'sentiment': current_sentiment,
                    'sentiment_score': record['sentiment_score'],
                    'future_return_3d': future_return,
                    'articles_count': record['news_articles_count']
                })
        
        if not predictive_analysis:
            return {"error": "Insufficient data for sentiment analysis"}
        
        # Calculate sentiment accuracy
        positive_sentiment_returns = [r['future_return_3d'] for r in predictive_analysis if r['sentiment'] == 'positive']
        negative_sentiment_returns = [r['future_return_3d'] for r in predictive_analysis if r['sentiment'] == 'negative']
        neutral_sentiment_returns = [r['future_return_3d'] for r in predictive_analysis if r['sentiment'] == 'neutral']
        
        results = {
            'symbol': symbol,
            'analysis_period_days': days_back,
            'total_predictions': len(predictive_analysis),
            'sentiment_breakdown': {
                'positive': {
                    'count': len(positive_sentiment_returns),
                    'avg_future_return': np.mean(positive_sentiment_returns) if positive_sentiment_returns else 0,
                    'accuracy': sum(1 for r in positive_sentiment_returns if r > 1) / len(positive_sentiment_returns) * 100 if positive_sentiment_returns else 0
                },
                'negative': {
                    'count': len(negative_sentiment_returns),
                    'avg_future_return': np.mean(negative_sentiment_returns) if negative_sentiment_returns else 0,
                    'accuracy': sum(1 for r in negative_sentiment_returns if r < -1) / len(negative_sentiment_returns) * 100 if negative_sentiment_returns else 0
                },
                'neutral': {
                    'count': len(neutral_sentiment_returns),
                    'avg_future_return': np.mean(neutral_sentiment_returns) if neutral_sentiment_returns else 0,
                    'accuracy': sum(1 for r in neutral_sentiment_returns if abs(r) <= 2) / len(neutral_sentiment_returns) * 100 if neutral_sentiment_returns else 0
                }
            },
            'overall_sentiment_accuracy': 0  # Will calculate below
        }
        
        # Calculate overall accuracy
        correct_predictions = 0
        for analysis in predictive_analysis:
            if (analysis['sentiment'] == 'positive' and analysis['future_return_3d'] > 1) or \
               (analysis['sentiment'] == 'negative' and analysis['future_return_3d'] < -1) or \
               (analysis['sentiment'] == 'neutral' and abs(analysis['future_return_3d']) <= 2):
                correct_predictions += 1
        
        results['overall_sentiment_accuracy'] = (correct_predictions / len(predictive_analysis) * 100) if predictive_analysis else 0
        
        print(f"📊 Sentiment Accuracy: {results['overall_sentiment_accuracy']:.1f}%")
        print(f"📈 Positive sentiment → Avg return: {results['sentiment_breakdown']['positive']['avg_future_return']:.2f}%")
        print(f"📉 Negative sentiment → Avg return: {results['sentiment_breakdown']['negative']['avg_future_return']:.2f}%")
        
        return results 