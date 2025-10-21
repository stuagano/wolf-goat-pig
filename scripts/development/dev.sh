#!/bin/bash
# Helper script to start both backend and frontend for Wolf Goat Pig MVP

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
REPORTS_DIR="$ROOT_DIR/reports"
DB_PATH="$REPORTS_DIR/wolf_goat_pig.db"
VENV_DIR="$BACKEND_DIR/venv"
REQUIREMENTS_FILE="$BACKEND_DIR/requirements.txt"

mkdir -p "$REPORTS_DIR"

export ENVIRONMENT="${ENVIRONMENT:-development}"
export DATABASE_URL="sqlite:////${DB_PATH#/}"

echo "🐺 Starting backend (FastAPI)..."

if [ ! -f "$REQUIREMENTS_FILE" ]; then
  echo "❌ Expected requirements file at $REQUIREMENTS_FILE" >&2
  exit 1
fi

cd "$BACKEND_DIR"

if [ ! -d "$VENV_DIR" ]; then
  echo "📦 Creating backend virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "📚 Ensuring backend dependencies are installed..."
python -m pip install --upgrade pip >/dev/null
python -m pip install -r "$REQUIREMENTS_FILE" >/dev/null

if [ ! -f "$DB_PATH" ]; then
  echo "🌱 Seeding default course data..."
  python app/seed_courses.py >/dev/null || true
fi

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd "$ROOT_DIR"

cleanup() {
  echo "\n🛑 Stopping backend..."
  kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "🎨 Starting frontend (React)..."
cd "$FRONTEND_DIR"

if [ ! -d node_modules ]; then
  echo "📦 Installing frontend dependencies..."
  npm install
fi

npm start
