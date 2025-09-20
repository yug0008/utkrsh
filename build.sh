#!/bin/bash
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Running database migrations..."
python -c "
from models.database import create_db_and_tables
create_db_and_tables()
"

echo "Build completed successfully!"
