from supabase import create_client, Client
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Initialize Supabase client lazily to avoid errors at import time
_supabase_client = None
_engine = None
_SessionLocal = None

def get_supabase_client():
    global _supabase_client
    if _supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.warning("Supabase credentials not found. Some features may not work.")
            return None
        
        try:
            _supabase_client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {str(e)}")
            return None
    
    return _supabase_client

def get_db_engine():
    global _engine
    if _engine is None:
        DATABASE_URL = os.getenv("DATABASE_URL")
        
        if not DATABASE_URL:
            logger.warning("DATABASE_URL not found. Database operations will not work.")
            return None
        
        # Fix common connection string issues
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
        try:
            _engine = create_engine(DATABASE_URL, pool_pre_ping=True)
            logger.info("Database engine created successfully")
        except Exception as e:
            logger.error(f"Error creating database engine: {str(e)}")
            return None
    
    return _engine

def get_db_session():
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_db_engine()
        if engine is None:
            return None
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return _SessionLocal

def get_db():
    SessionLocal = get_db_session()
    if SessionLocal is None:
        raise Exception("Database not configured")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_db_and_tables():
    engine = get_db_engine()
    if engine is None:
        logger.error("Cannot create tables - database engine not available")
        return
    
    # Create necessary tables if they don't exist
    try:
        with engine.connect() as connection:
            # Create users table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(255) PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    full_name VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    sport VARCHAR(100),
                    position VARCHAR(100),
                    date_of_birth DATE,
                    height FLOAT,
                    weight FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create videos table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS videos (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) REFERENCES users(id),
                    filename VARCHAR(255) NOT NULL,
                    original_name VARCHAR(255) NOT NULL,
                    sport_type VARCHAR(100) NOT NULL,
                    skill_type VARCHAR(100) NOT NULL,
                    file_url TEXT NOT NULL,
                    uploaded_at TIMESTAMP NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    analyzed_at TIMESTAMP,
                    error_message TEXT
                )
            """))
            
            # Create video_analyses table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS video_analyses (
                    id SERIAL PRIMARY KEY,
                    video_id INTEGER REFERENCES videos(id),
                    analysis_data JSONB NOT NULL,
                    analyzed_at TIMESTAMP NOT NULL
                )
            """))
            
            # Create performance_metrics table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) REFERENCES users(id),
                    metric_type VARCHAR(100) NOT NULL,
                    value FLOAT NOT NULL,
                    unit VARCHAR(50) NOT NULL,
                    recorded_at TIMESTAMP NOT NULL,
                    session_id VARCHAR(255),
                    notes TEXT
                )
            """))
            
            # Create achievements table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS achievements (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    badge_url TEXT,
                    criteria JSONB
                )
            """))
            
            # Create user_achievements table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS user_achievements (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) REFERENCES users(id),
                    achievement_id INTEGER REFERENCES achievements(id),
                    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    awarded_by VARCHAR(255)
                )
            """))
            
            connection.commit()
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
