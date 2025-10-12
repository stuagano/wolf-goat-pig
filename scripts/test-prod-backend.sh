#!/bin/bash

# Test production-like backend deployment locally
# Simulates Render deployment environment

set -e

echo "🔍 Testing Production Backend Deployment..."
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "backend/requirements.txt" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    exit 1
fi

# Create production environment file if it doesn't exist
if [ ! -f ".env.production" ]; then
    echo -e "${YELLOW}Creating .env.production from template...${NC}"
    cp config/.env.production.template .env.production 2>/dev/null || cp .env.example .env.production
    echo -e "${YELLOW}Please edit .env.production with your production values${NC}"
fi

# Load production environment
export $(cat .env.production | grep -v '^#' | xargs)

# Set production mode
export ENVIRONMENT=production
export DATABASE_URL=${DATABASE_URL:-postgresql://user:pass@localhost/wgp_prod}
export PORT=${PORT:-8000}

echo -e "\n${GREEN}1. Setting up production virtual environment...${NC}"
cd backend
python3 -m venv .venv-prod
source .venv-prod/bin/activate

echo -e "\n${GREEN}2. Installing production dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # Render uses gunicorn

echo -e "\n${GREEN}3. Running database migrations (if PostgreSQL configured)...${NC}"
if [[ $DATABASE_URL == postgresql://* ]]; then
    echo "PostgreSQL detected, would run migrations here"
    # python -c "from app.database import init_db; init_db()"
else
    echo "Using SQLite for local testing"
    python -c "from app.database import init_db; init_db()"
fi

echo -e "\n${GREEN}4. Running production server with gunicorn...${NC}"
echo "Server will start on http://localhost:${PORT}"
echo "Press Ctrl+C to stop"
echo ""

# Run with gunicorn like Render does
gunicorn app.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT} \
    --access-logfile - \
    --error-logfile - \
    --log-level info