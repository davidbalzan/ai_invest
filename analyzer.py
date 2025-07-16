# analyzer.py
from data_fetcher import get_stock_data, calculate_technical_indicators
from ai_analyzer import get_sentiment_analysis, get_ai_recommendation, _format_age, _format_age_from_timestamp
from data_storage import InvestmentDataStorage
from html_renderer import HTMLReportRenderer
from strategy_manager import StrategyManager
from report_generator import generate_pdf_report, create_individual_stock_chart, create_portfolio_overview_chart
from notifier import send_notification
from market_scheduler import MarketScheduler
from cache_manager import CacheManager
from datetime import datetime, timezone
import os

def _validate_data_age_for_trading(indicators, sentiment, market_scheduler=None):
    """Validate if data is fresh enough for reliable trading decisions"""
    warnings = []
    risk_level = "LOW"
    confidence_score = 100
    
    # Get current market timing
    timing_warnings = None
    if market_scheduler:
        timing_warnings = market_scheduler.get_market_timing_warnings()
    
    # Validate stock price data freshness
    try:
        data_timestamp = indicators.get('data_timestamp')
        retrieval_timestamp = indicators.get('retrieval_timestamp')
        
        if data_timestamp:
            now = datetime.now(timezone.utc)
            if hasattr(data_timestamp, 'tz_localize'):
                # Handle pandas timestamp
                if data_timestamp.tz is None:
                    data_timestamp = data_timestamp.tz_localize('UTC')
                else:
                    data_timestamp = data_timestamp.tz_convert('UTC')
                data_timestamp = data_timestamp.to_pydatetime()
            
            data_age_hours = (now - data_timestamp).total_seconds() / 3600
            
            # Critical: Data older than 3 days
            if data_age_hours > 72:
                warnings.append("🚨 CRITICAL: Stock price data is more than 3 days old")
                warnings.append(f"   Price data from: {_format_age_from_timestamp(data_timestamp)}")
                warnings.append("   Recommendation: DO NOT TRADE until you verify current prices")
                risk_level = "CRITICAL"
                confidence_score -= 50
                
            # High risk: Data older than 1 day during trading days
            elif data_age_hours > 24:
                if timing_warnings and timing_warnings.get('is_trading_day'):
                    warnings.append("⚠️ HIGH RISK: Stock price data is more than 1 day old")
                    warnings.append(f"   Price data from: {_format_age_from_timestamp(data_timestamp)}")
                    warnings.append("   Recommendation: Verify current prices before trading")
                    risk_level = "HIGH"
                    confidence_score -= 30
                else:
                    # Weekend/holiday - slightly less concerning
                    warnings.append("ℹ️ MODERATE: Price data is from previous trading session")
                    warnings.append(f"   Price data from: {_format_age_from_timestamp(data_timestamp)}")
                    if risk_level not in ["CRITICAL", "HIGH"]:
                        risk_level = "MEDIUM"
                        confidence_score -= 15
            
            # Medium risk: Data older than 4 hours during market hours
            elif data_age_hours > 4:
                if timing_warnings and timing_warnings.get('market_session') == 'market_open':
                    warnings.append("⚠️ MEDIUM RISK: Stock price data is several hours old during market hours")
                    warnings.append(f"   Price data from: {_format_age_from_timestamp(data_timestamp)}")
                    warnings.append("   Recommendation: Check for intraday price movements")
                    if risk_level not in ["CRITICAL", "HIGH"]:
                        risk_level = "MEDIUM"
                        confidence_score -= 20
    except Exception as e:
        warnings.append("❓ UNKNOWN: Unable to validate stock price data age")
        if risk_level == "LOW":
            risk_level = "MEDIUM"
            confidence_score -= 25
    
    # Validate sentiment data freshness
    try:
        news_age_minutes = sentiment.get('news_age_minutes')
        sentiment_retrieval = sentiment.get('retrieval_timestamp')
        
        if isinstance(news_age_minutes, int):
            # Critical: News older than 7 days
            if news_age_minutes > 10080:  # 7 days
                warnings.append("🚨 CRITICAL: News sentiment data is more than 1 week old")
                warnings.append(f"   Latest news: {_format_age(news_age_minutes)} old")
                warnings.append("   Recommendation: Check for recent news before trading")
                if risk_level not in ["CRITICAL"]:
                    risk_level = "HIGH"
                    confidence_score -= 25
                    
            # High risk: News older than 2 days
            elif news_age_minutes > 2880:  # 2 days
                warnings.append("⚠️ HIGH RISK: News sentiment is more than 2 days old")
                warnings.append(f"   Latest news: {_format_age(news_age_minutes)} old")
                warnings.append("   Recommendation: Search for recent news or earnings")
                if risk_level not in ["CRITICAL", "HIGH"]:
                    risk_level = "MEDIUM"
                    confidence_score -= 15
                    
            # Medium risk: News older than 12 hours during volatile periods
            elif news_age_minutes > 720:  # 12 hours
                if timing_warnings and timing_warnings.get('market_session') in ['market_open', 'pre_market', 'post_market']:
                    warnings.append("ℹ️ MODERATE: News sentiment is more than 12 hours old")
                    warnings.append(f"   Latest news: {_format_age(news_age_minutes)} old")
                    warnings.append("   Consider: Check for recent market-moving news")
                    confidence_score -= 10
        
        # Check articles analyzed count
        articles_count = sentiment.get('articles_analyzed', 0)
        if articles_count < 3:
            warnings.append("⚠️ LOW CONFIDENCE: Very few news articles analyzed for sentiment")
            warnings.append(f"   Only {articles_count} articles found")
            warnings.append("   Recommendation: Sentiment may not be representative")
            confidence_score -= 15
            
    except Exception as e:
        warnings.append("❓ UNKNOWN: Unable to validate news sentiment data age")
        confidence_score -= 10
    
    # Market timing validation
    if timing_warnings:
        market_session = timing_warnings.get('market_session', 'unknown')
        is_trading_day = timing_warnings.get('is_trading_day', False)
        
        # Critical: Weekend or holiday trading with stale data
        if not is_trading_day and risk_level in ["HIGH", "CRITICAL"]:
            warnings.append("🚨 CRITICAL COMBINATION: Stale data + Non-trading day")
            warnings.append("   Markets are closed and data is stale")
            warnings.append("   Recommendation: WAIT for fresh data on next trading day")
            risk_level = "CRITICAL"
            confidence_score -= 30
        
        # High risk: Pre-market trading with old sentiment
        elif market_session == 'pre_market' and news_age_minutes and isinstance(news_age_minutes, int) and news_age_minutes > 480:  # 8 hours
            warnings.append("⚠️ HIGH RISK: Pre-market trading with overnight news sentiment")
            warnings.append("   Overnight news may have changed sentiment significantly")
            warnings.append("   Recommendation: Check for overnight news and earnings")
            if risk_level not in ["CRITICAL"]:
                risk_level = "HIGH"
                confidence_score -= 20
    
    # Data retrieval validation
    try:
        retrieval_timestamp = indicators.get('retrieval_timestamp')
        if retrieval_timestamp:
            now = datetime.now(timezone.utc)
            retrieval_age_minutes = (now - retrieval_timestamp).total_seconds() / 60
            
            if retrieval_age_minutes > 60:  # More than 1 hour since data retrieval
                warnings.append("ℹ️ INFO: Data was retrieved more than 1 hour ago")
                warnings.append(f"   Retrieved: {_format_age_from_timestamp(retrieval_timestamp)}")
                warnings.append("   Consider: Refresh data for most current information")
                confidence_score -= 5
    except:
        pass
    
    # Calculate overall recommendation
    trading_recommendation = "PROCEED WITH CAUTION"
    
    if risk_level == "CRITICAL":
        trading_recommendation = "DO NOT TRADE - Data too stale"
    elif risk_level == "HIGH":
        trading_recommendation = "HIGH RISK - Verify data before trading"
    elif risk_level == "MEDIUM":
        trading_recommendation = "MODERATE RISK - Double-check key metrics"
    elif confidence_score >= 85:
        trading_recommendation = "DATA CONFIDENCE HIGH - Suitable for trading"
    elif confidence_score >= 70:
        trading_recommendation = "DATA CONFIDENCE GOOD - Monitor for changes"
    else:
        trading_recommendation = "LOW CONFIDENCE - Consider refreshing data"
    
    return {
        'warnings': warnings,
        'risk_level': risk_level,
        'confidence_score': max(0, min(100, confidence_score)),
        'trading_recommendation': trading_recommendation,
        'validation_timestamp': datetime.now(timezone.utc).isoformat()
    }

def _display_data_freshness_info(symbol, indicators, sentiment, market_scheduler=None):
    """Display data freshness information prominently with validation"""
    print(f"\n📊 DATA FRESHNESS FOR {symbol}:")
    print("=" * 50)
    
    # Market timing context with detailed warnings
    if market_scheduler:
        timing_warnings = market_scheduler.get_market_timing_warnings()
        
        print(f"📍 {timing_warnings['report_timing_context'].upper()}")
        print(f"🕐 Generated: {timing_warnings['market_time']}")
        print(f"📊 Session: {timing_warnings['market_session'].replace('_', ' ').title()}")
        print(f"🎯 Urgency: {timing_warnings['urgency_level']}")
        
        # Display next optimal trading time
        next_time = timing_warnings['next_optimal_trading_time']
        print(f"⏰ Next optimal: {next_time['description']}")
        print()
        
        # Display warnings
        for warning in timing_warnings['warnings']:
            print(f"   {warning}")
        print()
        
        # Display action recommendations
        if timing_warnings['action_recommendations']:
            print("💡 ACTION RECOMMENDATIONS:")
            for rec in timing_warnings['action_recommendations']:
                print(f"   {rec}")
            print()
    
    # Stock data freshness
    data_age = _format_age_from_timestamp(indicators.get('data_timestamp'))
    retrieval_age = _format_age_from_timestamp(indicators.get('retrieval_timestamp'))
    calculation_age = _format_age_from_timestamp(indicators.get('calculation_timestamp'))
    
    print(f"📈 Stock Price Data:")
    print(f"   • Data from: {data_age}")
    print(f"   • Retrieved: {retrieval_age}")
    print(f"   • Calculated: {calculation_age}")
    
    # Sentiment data freshness
    news_age = _format_age(sentiment.get('news_age_minutes', 'unknown'))
    sentiment_retrieval_age = _format_age_from_timestamp(sentiment.get('retrieval_timestamp'))
    
    print(f"\n📰 News Sentiment Data:")
    print(f"   • News age: {news_age}")
    print(f"   • Retrieved: {sentiment_retrieval_age}")
    print(f"   • Articles analyzed: {sentiment.get('articles_analyzed', 0)}")
    
    # COMPREHENSIVE DATA AGE VALIDATION
    validation_result = _validate_data_age_for_trading(indicators, sentiment, market_scheduler)
    
    print(f"\n🔍 DATA VALIDATION SUMMARY:")
    print(f"   Risk Level: {validation_result['risk_level']}")
    print(f"   Confidence Score: {validation_result['confidence_score']}/100")
    print(f"   Recommendation: {validation_result['trading_recommendation']}")
    
    # Display validation warnings
    if validation_result['warnings']:
        print(f"\n🚨 DATA AGE VALIDATION WARNINGS:")
        for warning in validation_result['warnings']:
            print(f"   {warning}")
    
    print("=" * 50)
    
    return validation_result

def _calculate_trading_window_with_urgency(market_scheduler=None, indicators=None, sentiment=None):
    """Calculate detailed trading window with urgency assessment"""
    if not market_scheduler:
        return {
            'status': "Market timing unavailable",
            'urgency': 'unknown',
            'action_window': 'unknown',
            'data_confidence': 'unknown'
        }
    
    timing_warnings = market_scheduler.get_market_timing_warnings()
    current_session = timing_warnings['market_session']
    urgency_level = timing_warnings['urgency_level']
    next_optimal = timing_warnings['next_optimal_trading_time']
    
    # Assess data confidence for trading decisions
    data_confidence = _assess_data_confidence(indicators, sentiment, timing_warnings)
    
    # Calculate specific action window
    action_window = _calculate_action_window(timing_warnings, data_confidence)
    
    if current_session == 'market_open':
        status = f"✅ IMMEDIATE TRADING WINDOW - {next_optimal['description']}"
        urgency = "IMMEDIATE"
    elif current_session == 'pre_market':
        status = f"🌅 PRE-MARKET ACTIVE - {next_optimal['description']}"
        urgency = "HIGH"
    elif current_session == 'post_market':
        status = f"🌆 POST-MARKET ACTIVE - {next_optimal['description']}"
        urgency = "MEDIUM"
    elif current_session == 'market_closed':
        status = f"⏳ MARKET CLOSED - {next_optimal['description']}"
        urgency = "LOW"
    elif current_session == 'weekend':
        status = f"🏖️ WEEKEND - {next_optimal['description']}"
        urgency = "PLANNING"
    else:
        status = f"❓ {current_session.replace('_', ' ').title()} - {next_optimal['description']}"
        urgency = "UNCERTAIN"
    
    return {
        'status': status,
        'urgency': urgency,
        'action_window': action_window,
        'data_confidence': data_confidence,
        'timing_context': timing_warnings['report_timing_context'],
        'recommendations': timing_warnings['action_recommendations']
    }

def _assess_data_confidence(indicators, sentiment, timing_warnings):
    """Assess confidence in data for trading decisions"""
    confidence_factors = []
    
    # Check market timing
    if timing_warnings['market_session'] == 'market_open':
        confidence_factors.append("HIGH - Live market data")
    elif timing_warnings['market_session'] in ['pre_market', 'post_market']:
        confidence_factors.append("MEDIUM - Extended hours data")
    else:
        confidence_factors.append("LOW - Stale market data")
    
    # Check news sentiment freshness
    try:
        if isinstance(sentiment.get('news_age_minutes'), int):
            news_age = sentiment['news_age_minutes']
            if news_age < 60:
                confidence_factors.append("HIGH - Recent news")
            elif news_age < 360:
                confidence_factors.append("MEDIUM - Moderately fresh news")
            else:
                confidence_factors.append("LOW - Stale news")
    except:
        confidence_factors.append("UNKNOWN - News age unavailable")
    
    # Overall confidence
    if "HIGH" in " ".join(confidence_factors):
        if "LOW" in " ".join(confidence_factors):
            return "MEDIUM - Mixed data quality"
        else:
            return "HIGH - Fresh data across sources"
    elif "MEDIUM" in " ".join(confidence_factors):
        return "MEDIUM - Adequate data freshness"
    else:
        return "LOW - Stale data, verify before trading"

def _calculate_action_window(timing_warnings, data_confidence):
    """Calculate specific action window timeframe"""
    urgency = timing_warnings['urgency_level']
    next_optimal = timing_warnings['next_optimal_trading_time']
    
    if urgency == "HIGH" and "HIGH" in data_confidence:
        return "IMMEDIATE (0-15 minutes) - Act now with high confidence"
    elif urgency == "HIGH":
        return "IMMEDIATE (0-30 minutes) - Act soon but verify prices"
    elif urgency == "MEDIUM" and "HIGH" in data_confidence:
        return "SHORT-TERM (30 minutes - 2 hours) - Good action window"
    elif urgency == "MEDIUM":
        return "SHORT-TERM (1-4 hours) - Monitor and prepare"
    elif urgency == "LOW":
        return f"PLANNING (Next session) - {next_optimal['description']}"
    else:
        return "UNCERTAIN - Assess market conditions"

def analyze_portfolio(portfolio_holdings, client, stop_loss_percent, take_profit_percent, generate_pdf_reports, notification_type, enable_notifications, report_output_dir, include_individual_charts, generate_html_reports=True, store_historical_data=True, analysis_context=None, **notification_kwargs):
    """Analyze entire portfolio"""
    if not portfolio_holdings:
        print("No portfolio holdings configured")
        return
    
    print("🔍 Analyzing portfolio...")
    analysis_results = {}
    notification_messages = []
    
    # Initialize components
    storage = InvestmentDataStorage() if store_historical_data else None
    html_renderer = HTMLReportRenderer() if generate_html_reports else None
    strategy_manager = StrategyManager()
    market_scheduler = MarketScheduler()  # For timing information
    
    # Initialize cache manager and show statistics
    cache_manager = CacheManager()
    enable_caching = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
    
    if enable_caching:
        # Clean up expired cache if requested
        if os.getenv('CACHE_CLEANUP_ON_START', 'false').lower() == 'true':
            removed_count = cache_manager.cleanup_expired_cache()
            if removed_count > 0:
                print(f"🧹 Cleaned up {removed_count} expired cache entries")
        
        # Show cache statistics if requested
        if os.getenv('CACHE_STATS_ON_START', 'true').lower() == 'true':
            stats = cache_manager.get_cache_stats()
            total_entries = stats['total_entries']
            expired_entries = stats['expired_entries']
            cache_size = stats['total_size_mb']
            market_session = stats['current_market_session']
            
            print(f"💾 Cache Status: {total_entries} entries ({cache_size:.2f} MB), {expired_entries} expired")
            print(f"📊 Market Session: {market_session.replace('_', ' ').title()}")
    else:
        print("⚠️ Caching is disabled - all data will be fetched fresh")
    
    # Get active strategy
    active_strategy = strategy_manager.get_active_strategy()
    if active_strategy:
        print(f"📋 Using strategy: {active_strategy.name} ({active_strategy.risk_profile.value.title()})")
        # Override stop_loss and take_profit with strategy values
        stop_loss_percent = active_strategy.stop_loss_percent
        take_profit_percent = active_strategy.take_profit_percent
    else:
        print("⚠️ No active strategy found, using default parameters")
    
    # Display comprehensive trading window information at the start
    trading_window_info = _calculate_trading_window_with_urgency(market_scheduler)
    print(f"\n🕐 TRADING WINDOW ANALYSIS:")
    print(f"   Status: {trading_window_info['status']}")
    print(f"   Urgency: {trading_window_info['urgency']}")
    print(f"   Action Window: {trading_window_info['action_window']}")
    print(f"   Context: {trading_window_info['timing_context']}")
    print()
    
    for symbol, holding in portfolio_holdings.items():
        print(f"\n📊 Analyzing {symbol}...")
        
        # Get stock data and indicators
        stock_data = get_stock_data(symbol)
        if stock_data is None:
            continue
        
        indicators = calculate_technical_indicators(stock_data)
        if indicators is None:
            continue
        
        sentiment = get_sentiment_analysis(symbol)
        
        # Display enhanced data freshness information with validation
        validation_result = _display_data_freshness_info(symbol, indicators, sentiment, market_scheduler)
        
        # Calculate trading window specific to this stock's data quality
        stock_trading_window = _calculate_trading_window_with_urgency(market_scheduler, indicators, sentiment)
        
        recommendation = get_ai_recommendation(symbol, stock_data, indicators, sentiment, client, portfolio_holdings, stop_loss_percent, take_profit_percent)
        
        # Calculate portfolio metrics
        current_price = indicators['current_price']
        cost_basis = holding['cost_basis']
        quantity = holding['quantity']
        current_value = current_price * quantity
        total_cost = cost_basis * quantity
        profit_loss = current_value - total_cost
        profit_loss_percent = (profit_loss / total_cost) * 100
        
        # Store results with enhanced timestamp and trading window information
        analysis_results[symbol] = {
            'current_price': current_price,
            'cost_basis': cost_basis,
            'quantity': quantity,
            'current_value': current_value,
            'total_cost': total_cost,
            'profit_loss': profit_loss,
            'profit_loss_percent': profit_loss_percent,
            'rsi': indicators['rsi'],
            'ma_20': indicators['ma_20'],
            'ma_50': indicators['ma_50'],
            'macd': indicators.get('macd', 0),
            'signal': indicators.get('signal', 0),
            'recommendation': recommendation,
            'sentiment': sentiment['sentiment'],
            'sentiment_score': sentiment.get('score', 0),
            'articles_analyzed': sentiment.get('articles_analyzed', 0),
            'news_age_minutes': sentiment.get('news_age_minutes', 'unknown'),
            # Enhanced timestamp tracking
            'data_timestamp': indicators.get('data_timestamp'),
            'retrieval_timestamp': indicators.get('retrieval_timestamp'),
            'calculation_timestamp': indicators.get('calculation_timestamp'),
            'sentiment_retrieval_timestamp': sentiment.get('retrieval_timestamp'),
            'latest_news_timestamp': sentiment.get('latest_news_timestamp'),
            # Trading window information
            'trading_window_urgency': stock_trading_window['urgency'],
            'action_window': stock_trading_window['action_window'],
            'data_confidence': stock_trading_window['data_confidence']
        }
        
        # Display results with enhanced timing context
        print(f"\n💰 INVESTMENT ANALYSIS:")
        print(f"Current Price: ${current_price:.2f}")
        print(f"Cost Basis: ${cost_basis:.2f}")
        print(f"Holdings: {quantity} shares")
        print(f"Current Value: ${current_value:.2f}")
        print(f"P&L: ${profit_loss:+.2f} ({profit_loss_percent:+.2f}%)")
        print(f"RSI: {indicators['rsi']:.2f}")
        print(f"Sentiment: {sentiment['sentiment'].title()} ({sentiment.get('score', 0):.3f})")
        print(f"📝 Recommendation: {recommendation}")
        
        # Display stock-specific trading window
        print(f"\n⚡ TRADING WINDOW FOR {symbol}:")
        print(f"   Urgency: {stock_trading_window['urgency']}")
        print(f"   Action Window: {stock_trading_window['action_window']}")
        print(f"   Data Confidence: {stock_trading_window['data_confidence']}")
        
        # Show final trading recommendation based on data validation
        if validation_result['risk_level'] == 'CRITICAL':
            print(f"\n🚨 FINAL RECOMMENDATION FOR {symbol}: {validation_result['trading_recommendation']}")
            print(f"   ⚠️ Data validation indicates high risk - avoid trading until data is refreshed")
        elif validation_result['risk_level'] == 'HIGH':
            print(f"\n⚠️ FINAL RECOMMENDATION FOR {symbol}: {validation_result['trading_recommendation']}")
            print(f"   📊 Double-check all metrics before making trading decisions")
        elif validation_result['confidence_score'] >= 85:
            print(f"\n✅ FINAL RECOMMENDATION FOR {symbol}: {validation_result['trading_recommendation']}")
            print(f"   🎯 Data quality is suitable for trading decisions")
        else:
            print(f"\n💡 FINAL RECOMMENDATION FOR {symbol}: {validation_result['trading_recommendation']}")
            print(f"   📋 Consider refreshing data for better confidence")
        
        # Add to notification message
        notification_messages.append(
            f"{symbol}: ${current_price:.2f} ({profit_loss_percent:+.2f}%) - {recommendation.split(' - ')[0].split(': ')[-1] if ' - ' in recommendation else recommendation.split(': ')[-1] if ': ' in recommendation else 'HOLD'}"
        )
    
    # Calculate portfolio totals
    total_value = sum(result['current_value'] for result in analysis_results.values())
    total_cost = sum(result['total_cost'] for result in analysis_results.values())
    total_profit_loss = total_value - total_cost
    total_profit_loss_percent = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0
    
    print(f"\n💼 PORTFOLIO SUMMARY:")
    print(f"Total Value: ${total_value:.2f}")
    print(f"Total Invested: ${total_cost:.2f}")
    print(f"Total P&L: ${total_profit_loss:+.2f} ({total_profit_loss_percent:+.2f}%)")
    
    # Display comprehensive final trading window summary
    print(f"\n🚨 PORTFOLIO TRADING WINDOW SUMMARY:")
    print(f"   Overall Status: {trading_window_info['status']}")
    print(f"   Urgency Level: {trading_window_info['urgency']}")
    print(f"   Action Window: {trading_window_info['action_window']}")
    print(f"   💡 Key Reminder: Always verify current prices before executing trades!")
    
    # Store historical data with enhanced metadata
    report_id = None
    if storage:
        metadata = {
            'version': '2.2',
            'analysis_type': 'portfolio',
            'total_symbols': len(analysis_results),
            'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
            'trading_window_status': trading_window_info['status'],
            'trading_urgency': trading_window_info['urgency'],
            'timing_context': trading_window_info['timing_context']
        }
        
        # Add strategic scheduling context if available
        if analysis_context:
            metadata.update({
                'scheduled_analysis_type': analysis_context.get('analysis_type'),
                'market_session': analysis_context.get('market_session'),
                'is_scheduled': analysis_context.get('scheduled', False)
            })
        
        # Get strategy information for storage
        strategy_info = {}
        if active_strategy:
            strategy_info = strategy_manager.get_strategy_summary(active_strategy.name)
        
        report_id = storage.store_daily_report(analysis_results, portfolio_holdings, metadata, strategy_info)
        print(f"📊 Historical data stored: {report_id}")
    
    # Generate HTML report from stored data
    html_path = None
    if html_renderer and report_id and storage:
        report_data = storage.load_report(report_id)
        if report_data:
            html_path = html_renderer.render_report(report_data)
            print(f"🌐 HTML report generated: {html_path}")
    
    # Generate PDF report (legacy format)
    pdf_path = None
    if generate_pdf_reports:
        pdf_path = generate_pdf_report(analysis_results, True, include_individual_charts, report_output_dir, get_stock_data, create_individual_stock_chart, create_portfolio_overview_chart, portfolio_holdings)
    
    # Send notification with comprehensive timing context
    if enable_notifications:
        # Add comprehensive timing context to notification
        context_prefix = ""
        if analysis_context and analysis_context.get('scheduled'):
            analysis_type = analysis_context.get('analysis_type', 'scheduled').replace('_', ' ').title()
            market_session = analysis_context.get('market_session', 'unknown').replace('_', ' ').title()
            context_prefix = f"🕐 {analysis_type} Analysis ({market_session})\n"
        
        # Add comprehensive trading window info
        context_prefix += f"📊 {trading_window_info['status']}\n"
        context_prefix += f"⚡ Urgency: {trading_window_info['urgency']}\n"
        context_prefix += f"🎯 Action Window: {trading_window_info['action_window']}\n\n"
        
        notification_message = context_prefix + f"Portfolio Value: ${total_value:.2f} (P&L: ${total_profit_loss:+.2f}, {total_profit_loss_percent:+.2f}%)\n\n" + "\n".join(notification_messages)
        send_notification(notification_type, notification_message, pdf_path, **notification_kwargs)
    
    return analysis_results

def _assess_action_urgency(indicators, sentiment, market_scheduler=None):
    """Assess urgency of action based on data freshness and market conditions"""
    urgency_factors = []
    
    if market_scheduler:
        market_status = market_scheduler.get_market_status_summary()
        current_session = market_status.get('current_session', 'unknown')
        
        if current_session == 'market_open':
            urgency_factors.append("HIGH - Market is open for immediate trading")
        elif current_session in ['pre_market', 'post_market']:
            urgency_factors.append("MEDIUM - Extended hours trading available")
        else:
            urgency_factors.append("LOW - Market closed, plan for next session")
    
    # Check news sentiment freshness
    try:
        if isinstance(sentiment.get('news_age_minutes'), int):
            news_age = sentiment['news_age_minutes']
            if news_age < 60:  # Less than 1 hour
                urgency_factors.append("Recent news may impact prices - verify before trading")
            elif news_age > 1440:  # More than 1 day
                urgency_factors.append("Sentiment data is stale - check for recent news")
    except:
        pass
    
    return " | ".join(urgency_factors) if urgency_factors else None

def analyze_single_stock(symbol, client, stop_loss_percent, take_profit_percent, generate_pdf_reports, notification_type, enable_notifications, report_output_dir, include_individual_charts, portfolio_holdings, analysis_context=None, **notification_kwargs):
    """Analyze a single stock with enhanced timing information"""
    print(f"📊 Analyzing {symbol}...")
    
    # Initialize market scheduler for timing information
    market_scheduler = MarketScheduler()
    
    # Display trading window information
    trading_window = _calculate_trading_window_with_urgency(market_scheduler)
    print(f"\n🕐 TRADING WINDOW STATUS:")
    print(f"   Status: {trading_window['status']}")
    print(f"   Urgency: {trading_window['urgency']}")
    print(f"   Action Window: {trading_window['action_window']}")
    print(f"   Context: {trading_window['timing_context']}")
    
    stock_data = get_stock_data(symbol)
    if stock_data is None:
        return
    
    indicators = calculate_technical_indicators(stock_data)
    if indicators is None:
        return
    
    sentiment = get_sentiment_analysis(symbol)
    
    # Display data freshness information prominently with validation
    validation_result = _display_data_freshness_info(symbol, indicators, sentiment, market_scheduler)
    
    # Calculate trading window specific to this stock's data quality
    stock_trading_window = _calculate_trading_window_with_urgency(market_scheduler, indicators, sentiment)
    
    recommendation = get_ai_recommendation(symbol, stock_data, indicators, sentiment, client, portfolio_holdings, stop_loss_percent, take_profit_percent)
    
    print(f"\n💰 ANALYSIS RESULTS:")
    print(f"Current Price: ${indicators['current_price']:.2f}")
    print(f"RSI: {indicators['rsi']:.2f}")
    print(f"20-day MA: ${indicators['ma_20']:.2f}")
    print(f"50-day MA: ${indicators['ma_50']:.2f}")
    print(f"Sentiment: {sentiment['sentiment'].title()} ({sentiment.get('score', 0):.3f})")
    print(f"📝 Recommendation: {recommendation}")
    
    # Display stock-specific trading window
    print(f"\n⚡ TRADING WINDOW FOR {symbol}:")
    print(f"   Urgency: {stock_trading_window['urgency']}")
    print(f"   Action Window: {stock_trading_window['action_window']}")
    print(f"   Data Confidence: {stock_trading_window['data_confidence']}")
    
    # Show final trading recommendation based on data validation
    if validation_result['risk_level'] == 'CRITICAL':
        print(f"\n🚨 FINAL RECOMMENDATION FOR {symbol}: {validation_result['trading_recommendation']}")
        print(f"   ⚠️ Data validation indicates high risk - avoid trading until data is refreshed")
    elif validation_result['risk_level'] == 'HIGH':
        print(f"\n⚠️ FINAL RECOMMENDATION FOR {symbol}: {validation_result['trading_recommendation']}")
        print(f"   📊 Double-check all metrics before making trading decisions")
    elif validation_result['confidence_score'] >= 85:
        print(f"\n✅ FINAL RECOMMENDATION FOR {symbol}: {validation_result['trading_recommendation']}")
        print(f"   🎯 Data quality is suitable for trading decisions")
    else:
        print(f"\n💡 FINAL RECOMMENDATION FOR {symbol}: {validation_result['trading_recommendation']}")
        print(f"   📋 Consider refreshing data for better confidence")
    
    # Display final trading window reminder
    print(f"\n🚨 IMPORTANT TRADING REMINDER:")
    print(f"   Status: {trading_window['status']}")
    print(f"   💡 Always verify current prices before executing trades!")
    
    # Generate individual chart and PDF if requested
    if generate_pdf_reports:
        analysis_results = {symbol: {
            'current_price': indicators['current_price'],
            'rsi': indicators['rsi'],
            'ma_20': indicators['ma_20'],
            'ma_50': indicators['ma_50'],
            'recommendation': recommendation,
            'sentiment': sentiment['sentiment'],
            'sentiment_score': sentiment.get('score', 0),
            'articles_analyzed': sentiment.get('articles_analyzed', 0),
            'news_age_minutes': sentiment.get('news_age_minutes', 'unknown'),
            # Enhanced timestamp tracking
            'data_timestamp': indicators.get('data_timestamp'),
            'retrieval_timestamp': indicators.get('retrieval_timestamp'),
            'calculation_timestamp': indicators.get('calculation_timestamp'),
            'sentiment_retrieval_timestamp': sentiment.get('retrieval_timestamp'),
            'latest_news_timestamp': sentiment.get('latest_news_timestamp'),
            # Trading window information
            'trading_window_urgency': stock_trading_window['urgency'],
            'action_window': stock_trading_window['action_window'],
            'data_confidence': stock_trading_window['data_confidence']
        }}
        pdf_path = generate_pdf_report(analysis_results, False, include_individual_charts, report_output_dir, get_stock_data, create_individual_stock_chart, create_portfolio_overview_chart, portfolio_holdings)
        
        if enable_notifications:
            # Add timing context to notification
            notification_message = f"🕐 {trading_window['status']}\n"
            notification_message += f"⚡ Urgency: {trading_window['urgency']}\n"
            notification_message += f"🎯 Action Window: {trading_window['action_window']}\n\n{symbol}: ${indicators['current_price']:.2f} - {recommendation.split(' - ')[0].split(': ')[-1] if ' - ' in recommendation else recommendation.split(': ')[-1] if ': ' in recommendation else 'HOLD'}"
            send_notification(notification_type, notification_message, pdf_path, **notification_kwargs)
