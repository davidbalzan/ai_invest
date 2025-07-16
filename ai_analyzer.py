from openai import OpenAI
import os
from dotenv import load_dotenv
import requests
import time
from datetime import datetime, timezone
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from cache_manager import CacheManager
import pytz

load_dotenv()

# Initialize cache manager
cache_manager = CacheManager()

def get_news_sentiment(symbol):
    """Get real news sentiment using the new FinnhubProvider and VADER sentiment analysis"""
    try:
        sentiment_retrieval_timestamp = datetime.now(timezone.utc)
        
        # Import the new FinnhubProvider
        from app.services.news_providers.finnhub_provider import FinnhubProvider
        from app.services.news_providers.base import NewsProviderError
        
        finnhub_api_key = os.getenv('FINNHUB_API_KEY')
        if not finnhub_api_key:
            print(f"Warning: FINNHUB_API_KEY not found in .env file for {symbol}")
            return {
                "sentiment": "neutral", 
                "score": 0.0, 
                "articles_analyzed": 0,
                "retrieval_timestamp": sentiment_retrieval_timestamp,
                "news_age_minutes": "unknown",
                "symbol": symbol
            }
        
        # Use the new FinnhubProvider
        provider = FinnhubProvider(finnhub_api_key)
        
        try:
            articles = provider.fetch_news_for_symbol(symbol, limit=10)
        except NewsProviderError as e:
            print(f"Warning: Finnhub provider error for {symbol}: {e}")
            return {
                "sentiment": "neutral", 
                "score": 0.0, 
                "articles_analyzed": 0,
                "retrieval_timestamp": sentiment_retrieval_timestamp,
                "news_age_minutes": "error",
                "symbol": symbol
            }
        
        if not articles:
            print(f"No news found for {symbol}")
            return {
                "sentiment": "neutral", 
                "score": 0.0, 
                "articles_analyzed": 0,
                "retrieval_timestamp": sentiment_retrieval_timestamp,
                "news_age_minutes": "no_news",
                "symbol": symbol
            }
        
        # Initialize VADER sentiment analyzer
        analyzer = SentimentIntensityAnalyzer()
        
        # Analyze sentiment of articles
        sentiment_scores = []
        latest_news_timestamp = None
        
        for article in articles:
            # Track the most recent news timestamp
            if latest_news_timestamp is None or article.published_at > latest_news_timestamp:
                latest_news_timestamp = article.published_at
            
            # Combine title and description for analysis
            text_to_analyze = f"{article.title} {article.description or ''}"
            
            if text_to_analyze.strip():
                scores = analyzer.polarity_scores(text_to_analyze)
                sentiment_scores.append(scores['compound'])
        
        if not sentiment_scores:
            overall_score = 0.0
            news_age_minutes = "unknown"
        else:
            overall_score = sum(sentiment_scores) / len(sentiment_scores)
            
            # Calculate how old the latest news is
            if latest_news_timestamp:
                age_delta = sentiment_retrieval_timestamp - latest_news_timestamp
                news_age_minutes = int(age_delta.total_seconds() / 60)
            else:
                news_age_minutes = "unknown"
        
        # Determine sentiment category
        if overall_score > 0.1:
            sentiment = "positive"
        elif overall_score < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "score": overall_score,
            "articles_analyzed": len(sentiment_scores),
            "retrieval_timestamp": sentiment_retrieval_timestamp,
            "latest_news_timestamp": latest_news_timestamp,
            "news_age_minutes": news_age_minutes,
            "symbol": symbol
        }
        
    except Exception as e:
        print(f"Error fetching sentiment for {symbol}: {e}")
        sentiment_retrieval_timestamp = datetime.now(timezone.utc)
        return {
            "sentiment": "neutral", 
            "score": 0.0, 
            "articles_analyzed": 0,
            "retrieval_timestamp": sentiment_retrieval_timestamp,
            "news_age_minutes": "error",
            "symbol": symbol
        }

def get_sentiment_analysis(symbol, force_refresh=False):
    """Enhanced sentiment analysis with intelligent caching"""
    # Check if caching is enabled
    enable_caching = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
    
    if not enable_caching or force_refresh:
        return _get_sentiment_analysis_direct(symbol)
    
    # Check for force refresh marker
    if cache_manager.should_force_refresh('sentiment_data', symbol):
        print(f"🔄 Force refreshing sentiment data for {symbol}")
        return _get_sentiment_analysis_direct(symbol)
    
    # Try to get cached sentiment first
    cached_sentiment = cache_manager.get_cached_data('sentiment_data', symbol)
    if cached_sentiment is not None:
        print(f"📰 Using cached sentiment data for {symbol}")
        
        # Convert timestamp strings back to datetime objects
        for timestamp_field in ['retrieval_timestamp', 'latest_news_timestamp']:
            if timestamp_field in cached_sentiment and isinstance(cached_sentiment[timestamp_field], str):
                try:
                    cached_sentiment[timestamp_field] = datetime.fromisoformat(cached_sentiment[timestamp_field])
                except:
                    pass  # Keep as string if conversion fails
        
        cached_sentiment['cached'] = True
        return cached_sentiment
    
    # Fetch new sentiment if not cached or expired
    print(f"📰 Fetching fresh sentiment data for {symbol}")
    return _get_sentiment_analysis_direct(symbol)

def _get_sentiment_analysis_direct(symbol):
    """Direct sentiment analysis without caching"""
    # Add a small delay to respect rate limits (60 calls/minute = 1 per second)
    time.sleep(1)
    
    # Get news sentiment with timestamp information
    news_sentiment = get_news_sentiment(symbol)
    
    # Cache the sentiment data for future use
    enable_caching = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
    if enable_caching and news_sentiment:
        # Prepare cache data (convert datetime objects to strings for JSON serialization)
        cache_data = news_sentiment.copy()
        for timestamp_field in ['retrieval_timestamp', 'latest_news_timestamp']:
            if timestamp_field in cache_data and isinstance(cache_data[timestamp_field], datetime):
                cache_data[timestamp_field] = cache_data[timestamp_field].isoformat()
        
        cache_data['cached'] = False  # Mark as fresh data
        
        success = cache_manager.cache_data('sentiment_data', symbol, cache_data)
        if success:
            print(f"💾 Cached sentiment data for {symbol}")
        else:
            print(f"⚠️ Failed to cache sentiment data for {symbol}")
    
    # You can also add social media sentiment here in the future
    # For now, we'll use the news sentiment as the primary indicator
    news_sentiment['cached'] = False
    return news_sentiment

def get_ai_recommendation(symbol, stock_data, indicators, sentiment, client, portfolio_holdings, stop_loss_percent, take_profit_percent, force_refresh=False):
    """Get AI recommendation using OpenAI with intelligent caching"""
    if not client:
        return "HOLD - AI analysis unavailable (no API key)"
    
    # Check if caching is enabled
    enable_caching = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
    
    # Generate cache key based on analysis context
    cache_context = {
        'current_price': float(indicators['current_price']),
        'rsi': float(indicators['rsi']),
        'sentiment': sentiment['sentiment'],
        'sentiment_score': float(sentiment.get('score', 0)),
        'stop_loss_percent': stop_loss_percent,
        'take_profit_percent': take_profit_percent,
        'data_timestamp': indicators['data_timestamp'].strftime('%Y-%m-%d') if hasattr(indicators['data_timestamp'], 'strftime') else str(indicators['data_timestamp'])
    }
    
    # Add portfolio context if available
    if symbol in portfolio_holdings:
        holding = portfolio_holdings[symbol]
        cache_context.update({
            'cost_basis': float(holding['cost_basis']),
            'quantity': float(holding['quantity'])
        })
    
    if not enable_caching or force_refresh:
        return _get_ai_recommendation_direct(symbol, stock_data, indicators, sentiment, client, portfolio_holdings, stop_loss_percent, take_profit_percent)
    
    # Check for force refresh marker
    if cache_manager.should_force_refresh('ai_recommendations', symbol, **cache_context):
        print(f"🔄 Force refreshing AI recommendation for {symbol}")
        return _get_ai_recommendation_direct(symbol, stock_data, indicators, sentiment, client, portfolio_holdings, stop_loss_percent, take_profit_percent)
    
    # Try to get cached recommendation first
    cached_recommendation = cache_manager.get_cached_data('ai_recommendations', symbol, **cache_context)
    if cached_recommendation is not None:
        print(f"🤖 Using cached AI recommendation for {symbol}")
        return cached_recommendation
    
    # Generate new recommendation if not cached or expired
    print(f"🤖 Generating fresh AI recommendation for {symbol}")
    return _get_ai_recommendation_direct(symbol, stock_data, indicators, sentiment, client, portfolio_holdings, stop_loss_percent, take_profit_percent, cache_context)

def _get_ai_recommendation_direct(symbol, stock_data, indicators, sentiment, client, portfolio_holdings, stop_loss_percent, take_profit_percent, cache_context=None):
    """Direct AI recommendation without caching"""
    try:
        ai_analysis_timestamp = datetime.now(timezone.utc)
        current_price = indicators['current_price']
        
        # Get portfolio context if available
        portfolio_context = ""
        if symbol in portfolio_holdings:
            holding = portfolio_holdings[symbol]
            cost_basis = holding['cost_basis']
            quantity = holding['quantity']
            current_value = current_price * quantity
            total_cost = cost_basis * quantity
            profit_loss = current_value - total_cost
            profit_loss_percent = (profit_loss / total_cost) * 100
            
            portfolio_context = f"""
PORTFOLIO CONTEXT:
- Current holdings: {quantity} shares
- Cost basis: ${cost_basis:.2f}
- Current value: ${current_value:.2f}
- Total cost: ${total_cost:.2f}
- P&L: ${profit_loss:.2f} ({profit_loss_percent:+.2f}%)
"""
        
        # Build data freshness context
        data_freshness_context = _build_data_freshness_context(indicators, sentiment)
        
        # Enhanced prompt with sentiment details and data freshness
        sentiment_context = f"""
NEWS SENTIMENT ANALYSIS:
- Overall sentiment: {sentiment['sentiment']}
- Sentiment score: {sentiment['score']:.3f} (range: -1 to +1)
- Articles analyzed: {sentiment.get('articles_analyzed', 0)}
- News age: {_format_age(sentiment.get('news_age_minutes', 'unknown'))}
"""
        
        prompt = f"""
As an AI investment advisor, provide a recommendation for {symbol} based on:

TECHNICAL ANALYSIS:
- Current Price: ${current_price:.2f}
- RSI: {indicators['rsi']:.2f} (Dynamic thresholds: Oversold<{indicators.get('rsi_oversold', 30)}, Overbought>{indicators.get('rsi_overbought', 70)})
- 20-day MA: ${indicators['ma_20']:.2f}
- 50-day MA: ${indicators['ma_50']:.2f}
- MACD: {indicators['macd']:.4f}
- Signal: {indicators['signal']:.4f}

MARKET REGIME & VOLATILITY:
- Volatility: {indicators.get('volatility', 0):.2f}% (annualized)
- Volume Ratio: {indicators.get('volume_ratio', 1):.2f}x average
- Price Momentum: {indicators.get('price_momentum', 0):+.2f}%
- Trend Strength: {indicators.get('trend_strength', 0):.2f}

{sentiment_context}

{data_freshness_context}

{portfolio_context}

RISK MANAGEMENT:
- Stop loss threshold: {stop_loss_percent}%
- Take profit threshold: {take_profit_percent}%

ANALYSIS REQUIREMENTS:
- Consider the dynamic RSI thresholds adjusted for current volatility
- Factor in market regime (trending vs. ranging)
- Evaluate volume confirmation for price moves
- Assess risk/reward based on current volatility levels

Provide one of: BUY, SELL, HOLD with a 3-4 sentence explanation focusing on:
1. Key technical signals with volatility context
2. Market regime and trend analysis
3. Risk/reward assessment with current volatility
4. Specific action recommendations

Format: "RECOMMENDATION: [BUY/SELL/HOLD] - [explanation]"
"""

        response = client.chat.completions.create(
            model="gpt-4",  # UPGRADED: from gpt-3.5-turbo to gpt-4 for more reliable analysis
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300  # INCREASED: from 200 to 300 for more detailed analysis
        )
        
        recommendation = response.choices[0].message.content.strip()
        
        # ENHANCED: Calculate dynamic confidence score based on data quality
        confidence_score = _calculate_recommendation_confidence(indicators, sentiment)
        
        # ENHANCED: Validate data quality and get reliability assessment
        validation_result = validate_analysis_data_quality(indicators, sentiment, symbol)
        
        # Add validation warnings to the recommendation if there are issues
        validation_context = ""
        if not validation_result["is_valid"] or validation_result["warnings"]:
            validation_context = f"\n\n🔍 DATA QUALITY ASSESSMENT:\n"
            validation_context += f"Status: {validation_result['data_status']} (Reliability: {validation_result['reliability_score']:.1f}%)\n"
            
            if validation_result["errors"]:
                validation_context += "CRITICAL ISSUES:\n" + "\n".join(validation_result["errors"]) + "\n"
            
            if validation_result["warnings"]:
                validation_context += "WARNINGS:\n" + "\n".join(validation_result["warnings"]) + "\n"
            
            if validation_result["recommendations"]:
                validation_context += "RECOMMENDATIONS:\n" + "\n".join(validation_result["recommendations"])
        
        # Add timestamp and confidence to recommendation
        recommendation_with_metadata = f"{recommendation}{validation_context}\n[AI Analysis: {ai_analysis_timestamp.strftime('%H:%M:%S UTC')} | Confidence: {confidence_score:.1f}% | Data Quality: {validation_result['data_status']}]"
        
        # Cache the AI recommendation for future use
        enable_caching = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
        if enable_caching and cache_context:
            success = cache_manager.cache_data('ai_recommendations', symbol, recommendation_with_metadata, **cache_context)
            if success:
                print(f"💾 Cached AI recommendation for {symbol}")
            else:
                print(f"⚠️ Failed to cache AI recommendation for {symbol}")
        
        return recommendation_with_metadata
        
    except Exception as e:
        print(f"Error getting AI recommendation: {e}")
        error_response = f"HOLD - Error in AI analysis: {str(e)}"
        
        # Cache error responses too (with shorter expiration)
        if cache_context:
            enable_caching = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
            if enable_caching:
                cache_manager.cache_data('ai_recommendations', symbol, error_response, **cache_context)
        
        return error_response

def _build_data_freshness_context(indicators, sentiment):
    """Build data freshness context for AI recommendation"""
    try:
        data_age = _format_age_from_timestamp(indicators.get('data_timestamp'))
        retrieval_age = _format_age_from_timestamp(indicators.get('retrieval_timestamp'))
        
        return f"""
DATA FRESHNESS:
- Stock data from: {data_age}
- Data retrieved: {retrieval_age}
- Sentiment data: {_format_age(sentiment.get('news_age_minutes', 'unknown'))} old
- Technical indicators calculated: {_format_age_from_timestamp(indicators.get('calculation_timestamp'))}
"""
    except:
        return "\nDATA FRESHNESS: Timestamp information unavailable"

def _format_age_from_timestamp(timestamp):
    """Format age from timestamp"""
    if not timestamp:
        return "unknown"
    
    try:
        if hasattr(timestamp, 'tz_localize'):
            # Handle pandas timestamp
            if timestamp.tz is None:
                timestamp = timestamp.tz_localize('UTC')
            else:
                timestamp = timestamp.tz_convert('UTC')
            timestamp = timestamp.to_pydatetime()
        
        now = datetime.now(timezone.utc)
        age_delta = now - timestamp
        return _format_age(int(age_delta.total_seconds() / 60))
    except:
        return "unknown"

def _format_age(age_minutes):
    """Format age in minutes to human readable format"""
    if age_minutes == "unknown" or age_minutes == "error" or age_minutes == "no_news":
        return str(age_minutes)
    
    try:
        age_minutes = int(age_minutes)
        if age_minutes < 1:
            return "just now"
        elif age_minutes < 60:
            return f"{age_minutes} minute{'s' if age_minutes != 1 else ''} ago"
        elif age_minutes < 1440:  # Less than 24 hours
            hours = age_minutes // 60
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = age_minutes // 1440
            return f"{days} day{'s' if days != 1 else ''} ago"
    except:
        return str(age_minutes) 

def _calculate_recommendation_confidence(indicators, sentiment):
    """Calculate dynamic confidence score based on data quality and freshness"""
    confidence = 100.0  # Start with maximum confidence
    
    try:
        # 1. Data Freshness Penalty (most critical factor)
        data_timestamp = indicators.get('data_timestamp')
        if data_timestamp:
            now = datetime.now(timezone.utc)
            
            # FIXED: Handle string timestamps from API responses
            if isinstance(data_timestamp, str):
                try:
                    # Parse ISO format timestamp
                    data_timestamp = datetime.fromisoformat(data_timestamp.replace('Z', '+00:00'))
                except ValueError:
                    try:
                        # Try parsing as pandas timestamp string
                        from dateutil import parser
                        data_timestamp = parser.parse(data_timestamp)
                        if data_timestamp.tzinfo is None:
                            data_timestamp = data_timestamp.replace(tzinfo=timezone.utc)
                    except:
                        print(f"Could not parse timestamp: {data_timestamp}")
                        data_timestamp = now  # Assume fresh data if can't parse
            
            # Handle pandas timestamp
            elif hasattr(data_timestamp, 'tz_localize'):
                if data_timestamp.tz is None:
                    data_timestamp = data_timestamp.tz_localize('UTC')
                else:
                    data_timestamp = data_timestamp.tz_convert('UTC')
                # Convert to datetime
                data_timestamp = data_timestamp.to_pydatetime()
            
            # Ensure timezone awareness
            if data_timestamp.tzinfo is None:
                data_timestamp = data_timestamp.replace(tzinfo=timezone.utc)
            else:
                data_timestamp = data_timestamp.astimezone(timezone.utc)
            
            data_age_hours = (now - data_timestamp).total_seconds() / 3600
            
            # Severe penalties for old data
            if data_age_hours > 72:  # More than 3 days
                confidence -= 60  # Critical penalty
            elif data_age_hours > 24:  # More than 1 day
                confidence -= 30
            elif data_age_hours > 8:  # More than 8 hours
                confidence -= 15
            elif data_age_hours > 4:  # More than 4 hours
                confidence -= 5
        else:
            confidence -= 40  # No timestamp data
        
        # 2. Sentiment Data Quality
        sentiment_score = sentiment.get('score', 0)
        articles_analyzed = sentiment.get('articles_analyzed', 0)
        news_age_minutes = sentiment.get('news_age_minutes', 'unknown')
        
        # Penalty for insufficient sentiment data
        if articles_analyzed < 3:
            confidence -= 15
        elif articles_analyzed < 5:
            confidence -= 8
        
        # Penalty for old news
        if isinstance(news_age_minutes, (int, float)):
            if news_age_minutes > 1440:  # More than 24 hours
                confidence -= 20
            elif news_age_minutes > 720:  # More than 12 hours
                confidence -= 10
            elif news_age_minutes > 360:  # More than 6 hours
                confidence -= 5
        
        # 3. Technical Indicator Quality
        current_price = indicators.get('current_price', 0)
        rsi = indicators.get('rsi', 50)
        ma_20 = indicators.get('ma_20', 0)
        ma_50 = indicators.get('ma_50', 0)
        
        # Penalty for missing or invalid technical data
        if not current_price or current_price <= 0:
            confidence -= 25
        if not rsi or rsi <= 0 or rsi >= 100:
            confidence -= 15
        if not ma_20 or ma_20 <= 0:
            confidence -= 10
        if not ma_50 or ma_50 <= 0:
            confidence -= 10
        
        # 4. Market Conditions Adjustment
        retrieval_timestamp = indicators.get('retrieval_timestamp')
        if retrieval_timestamp:
            # Check if analysis was done during market hours
            market_tz = pytz.timezone('America/New_York')
            if hasattr(retrieval_timestamp, 'astimezone'):
                market_time = retrieval_timestamp.astimezone(market_tz)
                hour = market_time.hour
                
                # Higher confidence during market hours (9:30 AM - 4:00 PM ET)
                if 9 <= hour < 16:
                    confidence += 5  # Bonus for market hours
                elif hour < 6 or hour > 20:
                    confidence -= 5  # Penalty for very off-hours
        
        # 5. Data Consistency Check
        # Penalize if current price seems inconsistent with moving averages
        if current_price > 0 and ma_20 > 0 and ma_50 > 0:
            price_ma_deviation = abs(current_price - ma_20) / ma_20
            if price_ma_deviation > 0.1:  # More than 10% deviation
                confidence -= 5
        
        # Ensure confidence stays within reasonable bounds
        confidence = max(10.0, min(95.0, confidence))
        
        return confidence
        
    except Exception as e:
        print(f"Error calculating confidence score: {e}")
        return 50.0  # Default moderate confidence on error

def validate_analysis_data_quality(indicators, sentiment, symbol):
    """Comprehensive data validation with detailed warnings and recommendations"""
    validation_result = {
        "is_valid": True,
        "warnings": [],
        "errors": [],
        "reliability_score": 100.0,
        "recommendations": [],
        "data_status": "GOOD"
    }
    
    try:
        # 1. CRITICAL: Timestamp Validation
        data_timestamp = indicators.get('data_timestamp')
        if not data_timestamp:
            validation_result["errors"].append("🚨 CRITICAL: No data timestamp available")
            validation_result["reliability_score"] -= 50
            validation_result["is_valid"] = False
        else:
            now = datetime.now(timezone.utc)
            
            # FIXED: Handle string timestamps from API responses
            if isinstance(data_timestamp, str):
                try:
                    # Parse ISO format timestamp
                    data_timestamp = datetime.fromisoformat(data_timestamp.replace('Z', '+00:00'))
                except ValueError:
                    try:
                        # Try parsing as pandas timestamp string
                        from dateutil import parser
                        data_timestamp = parser.parse(data_timestamp)
                        if data_timestamp.tzinfo is None:
                            data_timestamp = data_timestamp.replace(tzinfo=timezone.utc)
                    except:
                        print(f"Could not parse timestamp: {data_timestamp}")
                        data_timestamp = now  # Assume fresh data if can't parse
            
            # Handle pandas timestamp
            elif hasattr(data_timestamp, 'tz_localize'):
                if data_timestamp.tz is None:
                    data_timestamp = data_timestamp.tz_localize('UTC')
                else:
                    data_timestamp = data_timestamp.tz_convert('UTC')
                data_timestamp = data_timestamp.to_pydatetime()
            
            # Ensure timezone awareness
            if data_timestamp.tzinfo is None:
                data_timestamp = data_timestamp.replace(tzinfo=timezone.utc)
            else:
                data_timestamp = data_timestamp.astimezone(timezone.utc)
            
            data_age_hours = (now - data_timestamp).total_seconds() / 3600
            
            if data_age_hours > 168:  # More than 1 week
                validation_result["errors"].append(f"🚨 CRITICAL: Data is {data_age_hours/24:.1f} days old - DO NOT TRADE")
                validation_result["recommendations"].append("Refresh data immediately before making any decisions")
                validation_result["is_valid"] = False
                validation_result["reliability_score"] -= 60
            elif data_age_hours > 72:  # More than 3 days
                validation_result["warnings"].append(f"⚠️ WARNING: Data is {data_age_hours/24:.1f} days old")
                validation_result["recommendations"].append("Consider refreshing data for current market conditions")
                validation_result["reliability_score"] -= 30
            elif data_age_hours > 24:  # More than 1 day
                validation_result["warnings"].append(f"⚠️ Data is {data_age_hours:.1f} hours old")
                validation_result["reliability_score"] -= 15
        
        # 2. Technical Indicator Validation
        current_price = indicators.get('current_price', 0)
        rsi = indicators.get('rsi', 0)
        ma_20 = indicators.get('ma_20', 0)
        ma_50 = indicators.get('ma_50', 0)
        
        if not current_price or current_price <= 0:
            validation_result["errors"].append("🚨 CRITICAL: Invalid or missing current price")
            validation_result["is_valid"] = False
            validation_result["reliability_score"] -= 40
        
        if not rsi or rsi <= 0 or rsi >= 100:
            validation_result["warnings"].append("⚠️ Invalid RSI value - technical analysis may be unreliable")
            validation_result["reliability_score"] -= 20
        
        if not ma_20 or ma_20 <= 0:
            validation_result["warnings"].append("⚠️ Missing 20-day moving average")
            validation_result["reliability_score"] -= 15
        
        if not ma_50 or ma_50 <= 0:
            validation_result["warnings"].append("⚠️ Missing 50-day moving average")
            validation_result["reliability_score"] -= 15
        
        # 3. Sentiment Data Validation
        articles_analyzed = sentiment.get('articles_analyzed', 0)
        news_age_minutes = sentiment.get('news_age_minutes', 'unknown')
        
        if articles_analyzed < 2:
            validation_result["warnings"].append(f"⚠️ Limited news coverage: Only {articles_analyzed} articles analyzed")
            validation_result["recommendations"].append("Sentiment analysis may be unreliable due to limited news data")
            validation_result["reliability_score"] -= 20
        
        if isinstance(news_age_minutes, (int, float)) and news_age_minutes > 1440:
            validation_result["warnings"].append(f"⚠️ News data is {news_age_minutes/60:.1f} hours old")
            validation_result["reliability_score"] -= 15
        
        # 4. Market Timing Validation
        retrieval_timestamp = indicators.get('retrieval_timestamp')
        if retrieval_timestamp:
            market_tz = pytz.timezone('America/New_York')
            if hasattr(retrieval_timestamp, 'astimezone'):
                market_time = retrieval_timestamp.astimezone(market_tz)
                hour = market_time.hour
                weekday = market_time.weekday()
                
                # Check if analysis was done during market hours
                if weekday >= 5:  # Weekend
                    validation_result["warnings"].append("⚠️ Analysis performed during weekend - markets closed")
                elif hour < 9 or hour >= 16:
                    validation_result["warnings"].append("⚠️ Analysis performed outside market hours")
                    validation_result["recommendations"].append("Consider waiting for market open for more reliable price action")
        
        # 5. Data Consistency Checks
        if current_price > 0 and ma_20 > 0:
            price_deviation = abs(current_price - ma_20) / ma_20
            if price_deviation > 0.2:  # More than 20% deviation
                validation_result["warnings"].append(f"⚠️ Current price deviates {price_deviation*100:.1f}% from 20-day MA")
                validation_result["recommendations"].append("Verify price data accuracy due to unusual deviation")
        
        # 6. Set overall data status
        if validation_result["reliability_score"] >= 85:
            validation_result["data_status"] = "EXCELLENT"
        elif validation_result["reliability_score"] >= 70:
            validation_result["data_status"] = "GOOD"
        elif validation_result["reliability_score"] >= 50:
            validation_result["data_status"] = "FAIR"
            validation_result["warnings"].append("⚠️ Data quality is fair - use recommendations with caution")
        else:
            validation_result["data_status"] = "POOR"
            validation_result["errors"].append("🚨 Data quality is poor - recommendations not reliable")
            validation_result["is_valid"] = False
        
        return validation_result
        
    except Exception as e:
        validation_result["errors"].append(f"🚨 Validation error: {str(e)}")
        validation_result["is_valid"] = False
        validation_result["reliability_score"] = 0
        validation_result["data_status"] = "ERROR"
        return validation_result

def generate_reliability_report(analysis_results):
    """Generate a comprehensive reliability report for all recommendations"""
    report = {
        "overall_reliability": 0.0,
        "total_symbols": len(analysis_results),
        "reliable_count": 0,
        "warning_count": 0,
        "critical_count": 0,
        "summary": "",
        "recommendations": [],
        "data_quality_distribution": {
            "EXCELLENT": 0,
            "GOOD": 0,
            "FAIR": 0,
            "POOR": 0,
            "ERROR": 0
        }
    }
    
    if not analysis_results:
        report["summary"] = "No analysis data available"
        return report
    
    try:
        total_reliability = 0.0
        reliable_symbols = []
        warning_symbols = []
        critical_symbols = []
        
        for symbol, data in analysis_results.items():
            # Extract validation data if available
            validation_data = data.get('validation_result', {})
            reliability_score = validation_data.get('reliability_score', 50.0)
            data_status = validation_data.get('data_status', 'UNKNOWN')
            is_valid = validation_data.get('is_valid', True)
            warnings = validation_data.get('warnings', [])
            errors = validation_data.get('errors', [])
            
            total_reliability += reliability_score
            
            # Categorize symbols
            if reliability_score >= 80 and is_valid:
                reliable_symbols.append(symbol)
                report["reliable_count"] += 1
            elif reliability_score >= 50 and len(errors) == 0:
                warning_symbols.append(symbol)
                report["warning_count"] += 1
            else:
                critical_symbols.append(symbol)
                report["critical_count"] += 1
            
            # Count data quality distribution
            if data_status in report["data_quality_distribution"]:
                report["data_quality_distribution"][data_status] += 1
            else:
                report["data_quality_distribution"]["UNKNOWN"] = report["data_quality_distribution"].get("UNKNOWN", 0) + 1
        
        # Calculate overall reliability
        report["overall_reliability"] = total_reliability / len(analysis_results)
        
        # Generate summary
        if report["overall_reliability"] >= 85:
            report["summary"] = f"🟢 EXCELLENT: High confidence in all {report['total_symbols']} recommendations"
        elif report["overall_reliability"] >= 70:
            report["summary"] = f"🟡 GOOD: Recommendations are generally reliable with minor data quality issues"
        elif report["overall_reliability"] >= 50:
            report["summary"] = f"🟠 FAIR: Use recommendations with caution due to data quality concerns"
        else:
            report["summary"] = f"🔴 POOR: Recommendations not reliable due to significant data issues"
        
        # Add specific recommendations
        if critical_symbols:
            report["recommendations"].append(f"🚨 CRITICAL: Do not trade {', '.join(critical_symbols)} without fresh data")
        
        if warning_symbols:
            report["recommendations"].append(f"⚠️ CAUTION: Use extra care with {', '.join(warning_symbols)} due to data quality issues")
        
        if reliable_symbols:
            report["recommendations"].append(f"✅ RELIABLE: {', '.join(reliable_symbols)} have good data quality")
        
        # Add general recommendations
        if report["critical_count"] > 0:
            report["recommendations"].append("Refresh all data sources before making trading decisions")
        
        if report["warning_count"] > report["reliable_count"]:
            report["recommendations"].append("Consider waiting for market hours or fresh data")
        
        return report
        
    except Exception as e:
        report["summary"] = f"Error generating reliability report: {str(e)}"
        return report 