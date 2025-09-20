#!/bin/bash

echo "Starting Sports Talent AI Backend..."
echo "Checking environment variables..."

# Check if required environment variables are set
if [ -z "$SUPABASE_URL" ]; then
    echo "WARNING: SUPABASE_URL is not set"
fi

if [ -z "$SUPABASE_KEY" ]; then
    echo "WARNING: SUPABASE_KEY is not set"
fi

if [ -z "$DATABASE_URL" ]; then
    echo "WARNING: DATABASE_URL is not set"
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize database
echo "Initializing database..."
python -c "
from models.database import create_db_and_tables
create_db_and_tables()
"

# Start the server
echo "Starting server on port ${PORT:-8000}..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
