from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Sports Talent AI Ecosystem API")
    
    # Check environment variables
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "DATABASE_URL"]
    for var in required_vars:
        if not os.getenv(var):
            logger.warning(f"Environment variable {var} is not set")
    
    # Initialize database
    try:
        from models.database import create_db_and_tables
        create_db_and_tables()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")

app = FastAPI(
    title="Sports Talent AI Ecosystem API",
    description="Backend for AI-powered sports talent discovery and assessment",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers with error handling
try:
    from routers import auth, videos, metrics, dashboard, gamification
    
    app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
    app.include_router(videos.router, prefix="/videos", tags=["Videos"])
    app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])
    app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
    app.include_router(gamification.router, prefix="/gamification", tags=["Gamification"])
    
    logger.info("All routers loaded successfully")
except ImportError as e:
    logger.error(f"Failed to load routers: {e}")
except Exception as e:
    logger.error(f"Error setting up routers: {e}")

@app.get("/")
async def root():
    return {
        "message": "Welcome to Sports Talent AI Ecosystem API", 
        "docs": "/docs",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    # Check if essential services are available
    from models.database import get_supabase_client, get_db_engine
    
    supabase_status = "available" if get_supabase_client() else "unavailable"
    db_status = "available" if get_db_engine() else "unavailable"
    
    return {
        "status": "healthy", 
        "service": "sports-talent-api",
        "supabase": supabase_status,
        "database": db_status
    }

# For Render deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, workers=1)
