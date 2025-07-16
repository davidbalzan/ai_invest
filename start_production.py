#!/usr/bin/env python3
"""
Production server startup script for AI Investment Tool
Optimized for performance with multiple workers and threading
"""
import os
import sys
import multiprocessing

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_worker_count():
    """Calculate optimal worker count based on CPU cores"""
    cpu_count = multiprocessing.cpu_count()
    # Formula: (2 x CPU cores) + 1 for I/O bound applications
    return min((2 * cpu_count) + 1, 8)  # Cap at 8 workers to prevent resource exhaustion

if __name__ == "__main__":
    try:
        import uvicorn
        from app.main import app
        
        worker_count = get_worker_count()
        
        print("=" * 60)
        print("🚀 AI Investment Tool - Production Server")
        print("=" * 60)
        print(f"CPU Cores: {multiprocessing.cpu_count()}")
        print(f"Workers: {worker_count}")
        print(f"Port: 8081")
        print(f"Database: {os.getenv('DATABASE_URL', 'postgresql://ai_user:ai_password@localhost:5432/ai_investment')}")
        print("=" * 60)
        
        # Set environment for production
        os.environ["ENVIRONMENT"] = "production"
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8081,
            workers=worker_count,
            log_level="info",
            access_log=True,
            loop="asyncio",
            # Threading optimizations
            limit_concurrency=1000,
            limit_max_requests=10000,
            timeout_keep_alive=30,
            # Performance tuning
            backlog=2048,
            # Security headers
            server_header=False,
            date_header=True
        )
    except Exception as e:
        print(f"❌ Error starting production server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 