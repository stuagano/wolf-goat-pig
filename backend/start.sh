#!/bin/bash

# Production startup script for Wolf Goat Pig backend

echo "Starting Wolf Goat Pig backend..."

# Set production environment
export NODE_ENV=production

# Initialize database if needed
echo "Initializing database..."
python init_db_script.py

# Start the FastAPI application
echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1