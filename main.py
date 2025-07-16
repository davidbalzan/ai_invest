import schedule
import time
import os
from dotenv import load_dotenv
from openai import OpenAI
from data_fetcher import get_stock_data, calculate_technical_indicators
from ai_analyzer import get_sentiment_analysis, get_ai_recommendation
from report_generator import create_individual_stock_chart, create_portfolio_overview_chart, generate_pdf_report
from notifier import send_notification
from analyzer import analyze_portfolio, analyze_single_stock
from strategy_manager import StrategyManager
from market_scheduler import MarketScheduler, AnalysisType, MarketSession
from backtest_engine import BacktestEngine
from data_storage import InvestmentDataStorage

# Load environment variables
load_dotenv()

class AIInvestmentTool:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.portfolio_mode = os.getenv('PORTFOLIO_MODE', 'false').lower() == 'true'
        self.run_once_mode = os.getenv('RUN_ONCE_MODE', 'true').lower() == 'true'
        self.schedule_time = os.getenv('SCHEDULE_TIME', '09:00')
        
        # Strategic scheduling configuration
        self.enable_strategic_scheduling = os.getenv('ENABLE_STRATEGIC_SCHEDULING', 'false').lower() == 'true'
        self.scheduling_strategy = os.getenv('SCHEDULING_STRATEGY', 'balanced').lower()
        self.market_timezone = os.getenv('MARKET_TIMEZONE', 'America/New_York')
        self.run_immediate_analysis = os.getenv('RUN_IMMEDIATE_ANALYSIS', 'false').lower() == 'true'
        self.auto_detect_analysis_type = os.getenv('AUTO_DETECT_ANALYSIS_TYPE', 'true').lower() == 'true'
        
        # Backtesting Settings
        self.run_backtest = os.getenv('RUN_BACKTEST', 'false').lower() == 'true'
        self.backtest_period = os.getenv('BACKTEST_PERIOD', '90')  # days
        self.run_whatif_analysis = os.getenv('RUN_WHATIF_ANALYSIS', 'false').lower() == 'true'
        self.validate_predictions = os.getenv('VALIDATE_PREDICTIONS', 'false').lower() == 'true'
        self.historical_sentiment_symbol = os.getenv('HISTORICAL_SENTIMENT_SYMBOL', '')
        self.show_historical_sentiment = os.getenv('SHOW_HISTORICAL_SENTIMENT', 'false').lower() == 'true'
        
        # Initialize market scheduler
        self.market_scheduler = MarketScheduler()
        self.market_scheduler.market_hours.timezone = self.market_timezone
        
        # Override market hours if provided
        if os.getenv('PRE_MARKET_START'):
            self.market_scheduler.market_hours.pre_market_start = os.getenv('PRE_MARKET_START')
        if os.getenv('MARKET_OPEN'):
            self.market_scheduler.market_hours.market_open = os.getenv('MARKET_OPEN')
        if os.getenv('MARKET_CLOSE'):
            self.market_scheduler.market_hours.market_close = os.getenv('MARKET_CLOSE')
        if os.getenv('POST_MARKET_END'):
            self.market_scheduler.market_hours.post_market_end = os.getenv('POST_MARKET_END')
        
        # Parse portfolio holdings
        self.portfolio_holdings = self.parse_portfolio_holdings()
        
        # Risk management settings
        self.stop_loss_percent = float(os.getenv('STOP_LOSS_PERCENT', '-10.0'))
        self.take_profit_percent = float(os.getenv('TAKE_PROFIT_PERCENT', '20.0'))
        
        # Notification settings
        self.enable_notifications = os.getenv('ENABLE_NOTIFICATIONS', 'true').lower() == 'true'
        self.notification_type = os.getenv('NOTIFICATION_TYPE', 'none').lower()
        self.notification_kwargs = {
            'discord_webhook_url': os.getenv('DISCORD_WEBHOOK_URL'),
            'slack_bot_token': os.getenv('SLACK_BOT_TOKEN'),
            'slack_channel': os.getenv('SLACK_CHANNEL'),
            'email_smtp_server': os.getenv('EMAIL_SMTP_SERVER'),
            'email_smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
            'email_from': os.getenv('EMAIL_FROM'),
            'email_password': os.getenv('EMAIL_PASSWORD'),
            'email_to': os.getenv('EMAIL_TO')
        }
        
        # Report settings
        self.generate_pdf_reports = os.getenv('GENERATE_PDF_REPORTS', 'true').lower() == 'true'
        self.include_individual_charts = os.getenv('INCLUDE_INDIVIDUAL_CHARTS', 'true').lower() == 'true'
        self.report_output_dir = os.getenv('REPORT_OUTPUT_DIR', 'reports')
        
        # Ensure reports directory exists
        if not os.path.exists(self.report_output_dir):
            os.makedirs(self.report_output_dir)

    def parse_portfolio_holdings(self):
        """Parse portfolio holdings from environment variable"""
        holdings_str = os.getenv('PORTFOLIO_HOLDINGS', '')
        holdings = {}
        
        if holdings_str:
            for holding in holdings_str.split(','):
                parts = holding.strip().split(':')
                if len(parts) == 3:
                    symbol, quantity, cost_basis = parts
                    holdings[symbol] = {
                        'quantity': float(quantity),
                        'cost_basis': float(cost_basis)
                    }
        
        return holdings

    def show_strategy_info(self):
        """Display current strategy information"""
        strategy_manager = StrategyManager()
        active_strategy = strategy_manager.get_active_strategy()
        
        if not active_strategy:
            print("❌ No active strategy found")
            return
            
        print(f"\n🎯 Current Investment Strategy: {active_strategy.name}")
        print(f"📝 Description: {active_strategy.description}")
        print(f"🎲 Risk Profile: {active_strategy.risk_profile.value.title()}")
        print(f"📅 Created: {active_strategy.created_date[:10]}")
        print(f"🔄 Last Modified: {active_strategy.last_modified[:10]}")
        
        print(f"\n🛡️ Risk Management:")
        print(f"   Stop Loss: {active_strategy.stop_loss_percent:+.1f}%")
        print(f"   Take Profit: {active_strategy.take_profit_percent:+.1f}%")
        print(f"   Max Position Size: {active_strategy.max_position_size_percent:.1f}%")
        print(f"   Cash Reserve: {active_strategy.cash_reserve_percent:.1f}%")
        
        print(f"\n📊 Technical Analysis:")
        print(f"   RSI Thresholds: {active_strategy.rsi_oversold_threshold}-{active_strategy.rsi_overbought_threshold}")
        print(f"   Moving Averages: {active_strategy.moving_average_periods}")
        print(f"   Use MACD: {'Yes' if active_strategy.use_macd_signals else 'No'}")
        
        print(f"\n📰 Sentiment Analysis:")
        print(f"   Decision Weight: {active_strategy.sentiment_weight:.1%}")
        print(f"   Min Buy Score: {active_strategy.min_sentiment_score_buy}")
        print(f"   Min Articles: {active_strategy.news_articles_threshold}")
        
        print(f"\n⚖️ Portfolio Management:")
        print(f"   Rebalancing: {active_strategy.rebalancing_frequency.title()}")
        print(f"   Auto Rebalancing: {'Enabled' if active_strategy.auto_rebalancing else 'Disabled'}")
        print(f"   Target Positions: {active_strategy.diversification_target}")
        
        print(f"\n🎯 Performance Targets:")
        print(f"   Annual Return: {active_strategy.annual_return_target:.1f}%")
        print(f"   Max Drawdown: {active_strategy.max_drawdown_tolerance:.1f}%")
        print(f"   Sharpe Ratio: {active_strategy.sharpe_ratio_target:.1f}")
        
        # Show all available strategies
        all_strategies = strategy_manager.list_strategies()
        print(f"\n📋 Available Strategies:")
        for name in all_strategies:
            strategy = strategy_manager.get_strategy(name)
            status = "🟢 ACTIVE" if strategy.active else "⚪ Available"
            print(f"   {status} {name} ({strategy.risk_profile.value.title()})")
        
        print(f"\n💡 Tip: Set STRATEGY_NAME environment variable to switch strategies")
    
    def run_historical_analysis(self):
        """Run historical analysis including sentiment history and prediction validation"""
        print("\n🕰️ Running Historical Analysis...")
        
        storage = InvestmentDataStorage()
        
        # Show historical sentiment if requested
        if self.show_historical_sentiment and self.historical_sentiment_symbol:
            print(f"\n📊 Historical Sentiment Analysis: {self.historical_sentiment_symbol}")
            sentiment_history = storage.get_sentiment_history(self.historical_sentiment_symbol, int(self.backtest_period))
            
            if sentiment_history:
                print(f"📈 Found {len(sentiment_history)} historical sentiment records")
                
                # Show recent sentiment trends
                for record in sentiment_history[:5]:  # Show last 5 records
                    print(f"   {record['date']}: {record['sentiment'].title()} "
                          f"(Score: {record['sentiment_score']:.3f}, "
                          f"Articles: {record['news_articles_count']}, "
                          f"Price: ${record['price']:.2f})")
                
                # Create BacktestEngine for sentiment analysis
                backtest_engine = BacktestEngine()
                sentiment_analysis = backtest_engine.analyze_sentiment_predictive_power(
                    self.historical_sentiment_symbol, int(self.backtest_period)
                )
                
                if 'error' not in sentiment_analysis:
                    print(f"\n🧠 Sentiment Predictive Power Analysis:")
                    print(f"   Overall Accuracy: {sentiment_analysis['overall_sentiment_accuracy']:.1f}%")
                    for sentiment_type, data in sentiment_analysis['sentiment_breakdown'].items():
                        print(f"   {sentiment_type.title()}: {data['count']} predictions, "
                              f"{data['accuracy']:.1f}% accuracy, "
                              f"{data['avg_future_return']:.2f}% avg return")
            else:
                print(f"⚠️ No historical sentiment data found for {self.historical_sentiment_symbol}")
        
        # Validate predictions if requested
        if self.validate_predictions:
            print(f"\n🔍 Validating AI Predictions (Last {self.backtest_period} days)")
            backtest_engine = BacktestEngine()
            validation_results = backtest_engine.validate_historical_predictions(int(self.backtest_period))
            
            if 'error' not in validation_results and validation_results:
                overall_stats = validation_results.get('overall', {})
                if overall_stats:
                    print(f"🎯 Overall Prediction Accuracy: {overall_stats['accuracy_percent']:.1f}%")
                    print(f"   Correct: {overall_stats['total_correct']}/{overall_stats['total_predictions']} predictions")
                
                print(f"\n📊 Individual Stock Accuracy:")
                for symbol, stats in validation_results.items():
                    if symbol != 'overall' and 'error' not in stats:
                        print(f"   {symbol}: {stats['accuracy_percent']:.1f}% "
                              f"({stats['correct_predictions']}/{stats['total_predictions']})")
            else:
                print("⚠️ Insufficient historical data for prediction validation")
    
    def run_backtesting_analysis(self):
        """Run comprehensive backtesting and what-if analysis"""
        print(f"\n🔬 Running Backtesting Analysis...")
        
        # Get current strategy
        strategy_manager = StrategyManager()
        active_strategy = strategy_manager.get_active_strategy()
        
        if not active_strategy:
            print("❌ No active strategy found for backtesting")
            return
        
        # Calculate date range
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=int(self.backtest_period))).strftime('%Y-%m-%d')
        
        print(f"📅 Backtesting Period: {start_date} to {end_date}")
        print(f"🎯 Strategy: {active_strategy.name}")
        
        # Get portfolio symbols
        portfolio_symbols = list(self.portfolio_holdings.keys()) if self.portfolio_holdings else ['AAPL', 'MSFT', 'GOOGL']
        print(f"📊 Symbols: {', '.join(portfolio_symbols)}")
        
        try:
            backtest_engine = BacktestEngine()
            
            if self.run_whatif_analysis:
                # Run comprehensive what-if analysis
                print(f"\n🧪 Running What-If Scenarios...")
                whatif_results = backtest_engine.run_what_if_scenarios(
                    portfolio_symbols, start_date, end_date, active_strategy
                )
                
                # Generate and display report
                if whatif_results:
                    report_filename = f"reports/backtest_whatif_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    report = backtest_engine.generate_backtest_report(whatif_results, report_filename)
                    
                    print(f"\n📄 What-If Analysis Report:")
                    print("-" * 50)
                    # Show summary of top results
                    sorted_results = sorted(whatif_results.items(), key=lambda x: x[1].total_return, reverse=True)
                    for i, (name, result) in enumerate(sorted_results[:3]):
                        rank = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
                        print(f"{rank} {name}: {result.total_return:.2f}% return, {result.max_drawdown:.2f}% drawdown")
                    
                    print(f"\n📊 Full report saved to: {report_filename}")
            
            else:
                # Run simple backtest with current strategy
                print(f"\n📈 Running Simple Backtest...")
                result = backtest_engine.simulate_strategy(
                    portfolio_symbols, start_date, end_date, active_strategy
                )
                
                print(f"\n📊 Backtest Results:")
                print(f"   Total Return: {result.total_return:.2f}%")
                print(f"   Annualized Return: {result.annualized_return:.2f}%")
                print(f"   Max Drawdown: {result.max_drawdown:.2f}%")
                print(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
                print(f"   Win Rate: {result.win_rate:.1f}%")
                print(f"   Total Trades: {result.total_trades}")
                print(f"   Final Portfolio Value: ${result.final_portfolio_value:,.2f}")
        
        except Exception as e:
            print(f"❌ Error running backtesting: {e}")
            print("💡 Note: Backtesting requires sufficient historical data")

    def strategic_analysis_callback(self, analysis_type: AnalysisType, market_session: MarketSession):
        """Strategic analysis callback for market scheduler"""
        print(f"\n🎯 Running {analysis_type.value} analysis at {market_session.value}")
        
        # Add analysis context to notification
        analysis_context = {
            'analysis_type': analysis_type.value,
            'market_session': market_session.value,
            'scheduled': True
        }
        
        # Run the appropriate analysis
        self.run_analysis(analysis_context)
    
    def run_analysis(self, context: dict = None):
        """Run the appropriate analysis based on configuration"""
        if context is None:
            context = {'analysis_type': 'manual', 'market_session': 'unknown', 'scheduled': False}
            
        if self.portfolio_mode:
            analyze_portfolio(
                self.portfolio_holdings,
                self.client,
                self.stop_loss_percent,
                self.take_profit_percent,
                self.generate_pdf_reports,
                self.notification_type,
                self.enable_notifications,
                self.report_output_dir,
                self.include_individual_charts,
                generate_html_reports=True,
                store_historical_data=True,
                analysis_context=context,
                **self.notification_kwargs
            )
        else:
            # For single stock mode, you might want to specify a default stock
            # or get it from environment variable
            default_symbol = os.getenv('DEFAULT_SYMBOL', 'AAPL')
            analyze_single_stock(
                default_symbol,
                self.client,
                self.stop_loss_percent,
                self.take_profit_percent,
                self.generate_pdf_reports,
                self.notification_type,
                self.enable_notifications,
                self.report_output_dir,
                self.include_individual_charts,
                self.portfolio_holdings,
                analysis_context=context,
                **self.notification_kwargs
            )

    def main(self):
        """Main execution function"""
        print("🚀 AI Investment Tool Starting...")
        print(f"Mode: {'Portfolio' if self.portfolio_mode else 'Single Stock'}")
        print(f"Run Mode: {'Run Once' if self.run_once_mode else 'Scheduled'}")
        
        # Show market status
        if self.enable_strategic_scheduling or self.run_immediate_analysis:
            market_status = self.market_scheduler.get_market_status_summary()
            print(f"\n📊 Market Status:")
            print(f"   Session: {market_status['current_session'].title()}")
            print(f"   Trading Day: {'Yes' if market_status['is_trading_day'] else 'No'}")
            print(f"   Timezone: {market_status['market_timezone']}")
            if market_status.get('next_event'):
                print(f"   Next: {market_status['next_event']} in {market_status['time_to_next_event']}")
        
        if self.run_immediate_analysis:
            print("\n🚀 Running immediate market-aware analysis...")
            analysis_type = None if self.auto_detect_analysis_type else AnalysisType.EVENING_SUMMARY
            self.market_scheduler.set_analysis_callback(self.strategic_analysis_callback)
            self.market_scheduler.run_immediate_analysis(analysis_type)
            return
        
        # Run backtesting analysis if requested
        if self.run_backtest:
            self.run_backtesting_analysis()
            if not self.validate_predictions and not self.show_historical_sentiment:
                return
        
        # Run historical analysis if requested
        if self.validate_predictions or self.show_historical_sentiment:
            self.run_historical_analysis()
            return
        
        if self.run_once_mode:
            print("📈 Running analysis once...")
            self.run_analysis()
            print("✅ Analysis complete!")
        elif self.enable_strategic_scheduling:
            print(f"\n📅 Setting up strategic scheduling ({self.scheduling_strategy} strategy)...")
            
            # Set up strategic scheduling
            self.market_scheduler.set_analysis_callback(self.strategic_analysis_callback)
            strategic_tasks = self.market_scheduler.create_strategic_schedule(self.scheduling_strategy)
            self.market_scheduler.scheduled_tasks = strategic_tasks
            self.market_scheduler.setup_schedule()
            
            # Run the strategic scheduler
            self.market_scheduler.run_scheduler()
        else:
            print(f"⏰ Scheduling analysis for {self.schedule_time} daily...")
            schedule.every().day.at(self.schedule_time).do(self.run_analysis)
            
            print("🔄 Scheduler running... Press Ctrl+C to stop")
            try:
                while True:
                    schedule.run_pending()
                    time.sleep(60)
            except KeyboardInterrupt:
                print("\n👋 Scheduler stopped")

if __name__ == "__main__":
    # Check for strategy management commands
    strategy_name = os.getenv('STRATEGY_NAME', '').strip()
    show_strategy = os.getenv('SHOW_STRATEGY', '').lower() in ['true', '1', 'yes']
    
    tool = AIInvestmentTool()
    
    if show_strategy:
        tool.show_strategy_info()
    elif strategy_name:
        strategy_manager = StrategyManager()
        if strategy_manager.set_active_strategy(strategy_name):
            print(f"✅ Switched to strategy: {strategy_name}")
            tool.main()
        else:
            print(f"❌ Strategy '{strategy_name}' not found")
            print("Available strategies:")
            for name in strategy_manager.list_strategies():
                print(f"  - {name}")
    else:
        tool.main()