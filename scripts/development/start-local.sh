#!/bin/bash

# Wolf-Goat-Pig Local Development Script
# This script starts both backend and frontend servers for local development

echo "🐺 Starting Wolf-Goat-Pig Local Development Environment..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    echo -e "${GREEN}✓ Backend virtual environment found${NC}"
fi

# Function to kill processes on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup EXIT INT TERM

# Start backend server
echo -e "${GREEN}Starting backend server on http://localhost:8000${NC}"
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Check if backend is running
if curl -f http://localhost:8000/health 2>/dev/null; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${YELLOW}⚠ Backend health check failed, but continuing...${NC}"
fi

# Start frontend server
echo -e "${GREEN}Starting frontend server on http://localhost:3000${NC}"
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# Display status
echo -e "\n${GREEN}=================================================="
echo "🚀 Local development environment is running!"
echo "=================================================="
echo -e "${NC}"
echo "Backend API: http://localhost:8000"
echo "API Docs:    http://localhost:8000/docs"
echo "Frontend:    http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "=================================================="

# Keep script running
wait