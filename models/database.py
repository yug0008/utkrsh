from supabase import create_client, Client
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# SQLAlchemy setup for PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_supabase_client():
    return supabase

def create_db_and_tables():
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
            
            connection.commit()
            print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")
        # Don't raise exception to allow app to start
