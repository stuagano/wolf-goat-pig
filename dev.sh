#!/bin/bash
# Helper script to start both backend and frontend for Wolf Goat Pig MVP

# Start backend (FastAPI)
echo "Starting backend (FastAPI)..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload &
BACKEND_PID=$!
cd ..

# Start frontend (React)
echo "Starting frontend (React)..."
cd frontend
npm start

# On exit, kill backend
trap "kill $BACKEND_PID" EXIT 