#!/usr/bin/env python3
"""
Simple server startup script for AI Investment Tool
"""
import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    try:
        import uvicorn
        from app.main import app
        
        print("Starting AI Investment Tool server...")
        print("Database URL:", os.getenv("DATABASE_URL", "postgresql://ai_user:ai_password@localhost:5432/ai_investment"))
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8081,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc() 