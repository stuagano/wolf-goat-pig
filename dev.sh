#!/bin/bash
# Helper script to start both backend and frontend for Wolf Goat Pig

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🐺 Wolf Goat Pig Development Servers"
echo "===================================="

# Check if the actual dev.sh exists in scripts/development
DEV_SCRIPT="$SCRIPT_DIR/scripts/development/dev.sh"

if [ -f "$DEV_SCRIPT" ]; then
    echo "🚀 Using development script from scripts/development/dev.sh"
    exec "$DEV_SCRIPT"
else
    echo "📁 Running from root directory with direct commands"
    
    # Set environment variables
    export ENVIRONMENT=development
    export DATABASE_URL="sqlite:///./reports/wolf_goat_pig.db"
    
    # Create reports directory if it doesn't exist
    mkdir -p "$SCRIPT_DIR/reports"
    
    echo "🔧 Environment configured"
    echo "📁 Database: $DATABASE_URL"
    
    # Check if we can start the backend
    if [ ! -f "$SCRIPT_DIR/backend/app/main.py" ]; then
        echo "❌ Backend not found at: $SCRIPT_DIR/backend/app/main.py"
        exit 1
    fi
    
    echo "🚀 Starting backend server..."
    echo "📍 Backend API: http://localhost:8000"
    echo "📖 API Docs: http://localhost:8000/docs"
    echo ""
    echo "💡 To start frontend separately:"
    echo "  cd frontend && npm start"
    echo ""
    echo "Press Ctrl+C to stop the server"
    
    # Start backend with Python
    cd "$SCRIPT_DIR/backend"
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi