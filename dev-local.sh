#!/bin/bash

# Quick Local Development Script for Wolf-Goat-Pig
# Starts both servers in separate terminal tabs/windows

echo "🐺🐐🐷 Starting Wolf-Goat-Pig Local Development..."
echo ""

# Start backend in background
echo "📦 Starting Backend (Port 8000)..."
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
cd ..

# Give backend time to start
sleep 3

# Start frontend 
echo "🎨 Starting Frontend (Port 3000)..."
echo "Note: Frontend will proxy API calls to http://localhost:8000"
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================="
echo "✅ Development servers are starting!"
echo "========================================="
echo "🔗 Frontend:  http://localhost:3000"
echo "🔗 Backend:   http://localhost:8000" 
echo "📚 API Docs:  http://localhost:8000/docs"
echo "========================================="
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID