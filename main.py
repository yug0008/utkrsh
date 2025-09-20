from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os

# Import routers conditionally to avoid errors during startup
try:
    from routers import auth, videos, metrics, dashboard, gamification
    from utils.auth import get_current_user
    from models.database import create_db_and_tables, supabase
    routers_available = True
except ImportError as e:
    logging.warning(f"Some modules not available: {e}")
    routers_available = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Sports Talent AI Ecosystem API")
    try:
        if routers_available:
            create_db_and_tables()
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

# CORS middleware - configure for your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers only if they're available
if routers_available:
    app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
    app.include_router(videos.router, prefix="/videos", tags=["Videos"])
    app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])
    app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
    app.include_router(gamification.router, prefix="/gamification", tags=["Gamification"])
else:
    logger.warning("Routers not available - running in minimal mode")

@app.get("/")
async def root():
    return {"message": "Welcome to Sports Talent AI Ecosystem API", "docs": "/docs"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "sports-talent-api"}

# For Render deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
