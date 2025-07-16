from openai import OpenAI
import os
from dotenv import load_dotenv
import requests
import time
from datetime import datetime, timezone
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from cache_manager import CacheManager

load_dotenv()

# Initialize cache manager
cache_manager = CacheManager()

def get_news_sentiment(symbol):
    """Get real news sentiment using Finnhub API and VADER sentiment analysis"""
    try:
        sentiment_retrieval_timestamp = datetime.now(timezone.utc)
        
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
        
        # Finnhub company news endpoint (free tier: 60 calls/minute)
        url = f"https://finnhub.io/api/v1/company-news"
        params = {
            'symbol': symbol,
            'from': '2024-01-01',  # Get recent news
            'to': '2024-12-31',
            'token': finnhub_api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"Warning: Finnhub API returned status {response.status_code} for {symbol}")
            return {
                "sentiment": "neutral", 
                "score": 0.0, 
                "articles_analyzed": 0,
                "retrieval_timestamp": sentiment_retrieval_timestamp,
                "news_age_minutes": "error",
                "symbol": symbol
            }
        
        news_data = response.json()
        
        if not news_data or len(news_data) == 0:
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
        
        # Analyze sentiment of recent news (last 10 articles)
        recent_news = news_data[:10]
        sentiment_scores = []
        latest_news_timestamp = None
        
        for article in recent_news:
            headline = article.get('headline', '')
            summary = article.get('summary', '')
            
            # Track the most recent news timestamp
            if article.get('datetime'):
                news_timestamp = datetime.fromtimestamp(article['datetime'], tz=timezone.utc)
                if latest_news_timestamp is None or news_timestamp > latest_news_timestamp:
                    latest_news_timestamp = news_timestamp
            
            # Combine headline and summary for analysis
            text_to_analyze = f"{headline} {summary}"
            
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
- RSI: {indicators['rsi']:.2f}
- 20-day MA: ${indicators['ma_20']:.2f}
- 50-day MA: ${indicators['ma_50']:.2f}
- MACD: {indicators['macd']:.4f}
- Signal: {indicators['signal']:.4f}

{sentiment_context}

{data_freshness_context}

{portfolio_context}

RISK MANAGEMENT:
- Stop loss threshold: {stop_loss_percent}%
- Take profit threshold: {take_profit_percent}%

Consider market trends, sector performance, company fundamentals, news sentiment, and risk management.
Provide one of: BUY, SELL, HOLD with a brief 2-3 sentence explanation focusing on:
1. Key technical signals and news sentiment
2. Risk/reward assessment
3. Specific action if holding shares

Format: "RECOMMENDATION: [BUY/SELL/HOLD] - [explanation]"
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        
        recommendation = response.choices[0].message.content.strip()
        
        # Add timestamp to recommendation
        recommendation_with_timestamp = f"{recommendation}\n[AI Analysis: {ai_analysis_timestamp.strftime('%H:%M:%S UTC')}]"
        
        # Cache the AI recommendation for future use
        enable_caching = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
        if enable_caching and cache_context:
            success = cache_manager.cache_data('ai_recommendations', symbol, recommendation_with_timestamp, **cache_context)
            if success:
                print(f"💾 Cached AI recommendation for {symbol}")
            else:
                print(f"⚠️ Failed to cache AI recommendation for {symbol}")
        
        return recommendation_with_timestamp
        
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