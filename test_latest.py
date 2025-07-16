#!/usr/bin/env python3

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import AnalysisSession

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def main():
    # Create database connection
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ai_user:ai_password@localhost:5432/ai_investment")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # Get the most recent COMPLETED analysis session
        sessions = db.query(AnalysisSession).filter(AnalysisSession.status == 'COMPLETED').order_by(AnalysisSession.started_at.desc()).limit(2).all()
        
        if not sessions:
            print("No completed analysis sessions found!")
            return
        
        session = sessions[0]  # Get the most recent completed one
        
        print(f"✅ Latest session: {session.id}")
        print(f"   Status: {session.status}")
        print(f"   Started: {session.started_at}")
        print(f"   Completed: {session.completed_at}")
        
        # Check JSONB fields
        print(f"\n🔍 JSONB Field Analysis:")
        print(f"   Portfolio Snapshot: {bool(session.portfolio_snapshot)}")
        if session.portfolio_snapshot:
            print(f"      Keys: {list(session.portfolio_snapshot.keys())}")
            if "holdings" in session.portfolio_snapshot:
                holdings = session.portfolio_snapshot["holdings"]
                print(f"      Holdings: {list(holdings.keys()) if holdings else 'Empty'}")
                
        print(f"   Market Data: {bool(session.market_data_snapshot)}")
        if session.market_data_snapshot:
            print(f"      Symbols: {list(session.market_data_snapshot.keys())}")
            # Check structure of first symbol
            first_symbol = list(session.market_data_snapshot.keys())[0]
            market_data_keys = list(session.market_data_snapshot[first_symbol].keys()) if session.market_data_snapshot[first_symbol] else []
            print(f"      First symbol ({first_symbol}) keys: {market_data_keys}")
                
        print(f"   Technical Indicators: {bool(session.technical_indicators)}")
        if session.technical_indicators:
            print(f"      Symbols: {list(session.technical_indicators.keys())}")
                
        print(f"   AI Recommendations: {bool(session.ai_recommendations)}")
        if session.ai_recommendations:
            print(f"      Symbols: {list(session.ai_recommendations.keys())}")
                
        print(f"   Sentiment Analysis: {bool(session.sentiment_analysis)}")
        if session.sentiment_analysis:
            print(f"      Symbols: {list(session.sentiment_analysis.keys())}")
        
        if session.portfolio_snapshot and session.market_data_snapshot:
            print(f"\n🎉 SUCCESS: JSONB data found!")
        else:
            print(f"\n❌ No JSONB data found")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main() 