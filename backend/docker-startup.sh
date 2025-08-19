#!/bin/bash

# Wolf-Goat-Pig Docker Startup Script
# This script handles the startup sequence for containerized deployments

set -e  # Exit on any error

echo "🐺 Wolf-Goat-Pig Docker Startup"
echo "================================"

# Set default values
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
ENVIRONMENT=${ENVIRONMENT:-production}
LOG_LEVEL=${LOG_LEVEL:-INFO}

echo "Environment: $ENVIRONMENT"
echo "Host: $HOST"
echo "Port: $PORT"
echo "Log Level: $LOG_LEVEL"

# Wait for database if DATABASE_URL is provided
if [ ! -z "$DATABASE_URL" ]; then
    echo "🔍 Checking database connection..."
    
    # Extract host and port from DATABASE_URL if it's PostgreSQL
    if [[ $DATABASE_URL == postgresql* ]]; then
        # Simple wait - in production, use a proper wait script
        echo "⏳ Waiting for database to be ready..."
        sleep 5
    fi
fi

# Run health check and setup verification
echo "🏥 Running startup verification..."
python startup.py --verify-setup --environment="$ENVIRONMENT" --log-level="$LOG_LEVEL"

if [ $? -ne 0 ]; then
    echo "❌ Startup verification failed"
    exit 1
fi

echo "✅ Startup verification passed"

# Start the server
echo "🚀 Starting Wolf-Goat-Pig server..."
python startup.py \
    --host="$HOST" \
    --port="$PORT" \
    --environment="$ENVIRONMENT" \
    --log-level="$LOG_LEVEL" \
    --no-reload

echo "🏁 Server shutdown"