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
        
        # Check if we're in development mode
        is_dev = os.getenv("ENVIRONMENT", "development").lower() == "development"
        
        if is_dev:
            # Development mode: reload enabled, single worker with threading optimizations
            print("Running in DEVELOPMENT mode with auto-reload")
            uvicorn.run(
                "app.main:app",
                host="0.0.0.0",
                port=8081,
                reload=True,
                log_level="info",
                access_log=True,
                loop="asyncio",
                # Threading optimizations for development
                limit_concurrency=500,
                timeout_keep_alive=15,
                backlog=1024
            )
        else:
            # Production mode: multiple workers, no reload
            import multiprocessing
            worker_count = min((2 * multiprocessing.cpu_count()) + 1, 6)
            print(f"Running in PRODUCTION mode with {worker_count} workers")
            uvicorn.run(
                "app.main:app",
                host="0.0.0.0",
                port=8081,
                workers=worker_count,
                log_level="info",
                access_log=True,
                loop="asyncio",
                # Performance optimizations
                limit_concurrency=1000,
                limit_max_requests=8000,
                timeout_keep_alive=25,
                backlog=2048
            )
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc() 