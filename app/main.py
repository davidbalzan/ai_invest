"""
Main FastAPI application for AI Investment Tool
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
import logging
from contextlib import asynccontextmanager

from app.database import init_db, check_db_connection
from app.api import portfolios, users, transactions, analysis
from app.api.web import web_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting AI Investment Tool server...")
    
    # Check database connection
    if not check_db_connection():
        logger.error("Failed to connect to database")
        raise Exception("Database connection failed")
    
    logger.info("Database connection successful")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    # Clean up stale running analysis sessions from previous server runs
    try:
        from app.services.database_service import DatabaseService
        from app.database import SessionLocal
        
        db = SessionLocal()
        try:
            db_service = DatabaseService(db)
            cleaned_count = db_service.clean_stale_running_sessions()
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} stale running analysis sessions")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to clean stale sessions: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Investment Tool server...")

# Create FastAPI app
app = FastAPI(
    title="AI Investment Tool",
    description="Intelligent investment analysis with multi-portfolio support",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include API routers
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(portfolios.router, prefix="/api/v1/portfolios", tags=["portfolios"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["transactions"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])

# Include web routes
app.include_router(web_routes.router, prefix="", tags=["web"])

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - redirect to dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_healthy = check_db_connection()
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 