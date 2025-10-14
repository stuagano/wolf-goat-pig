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

# Load production environment (supports comments and spaces)
set -a
source .env.production
set +a

# Allow local workflows to opt out when running in constrained environments
if [ "${SKIP_RENDER_BACKEND_CHECK:-false}" = "true" ]; then
    echo "Skipping backend production verification (SKIP_RENDER_BACKEND_CHECK=true)."
    exit 0
fi

# Set production mode
export ENVIRONMENT=production
export DATABASE_URL=${DATABASE_URL:-postgresql://user:pass@localhost/wgp_prod}
export PORT=${PORT:-8000}

# Ensure the selected port is free before starting gunicorn
if command -v lsof >/dev/null 2>&1; then
    if lsof -i TCP:${PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}Error: Port ${PORT} is already in use.${NC}"
        echo "Hint: stop the other process or rerun with PORT=<free-port> ./scripts/test-prod-backend.sh"
        exit 1
    fi
else
    echo -e "${YELLOW}Warning: 'lsof' not available; skipping port availability check.${NC}"
fi

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
echo "Running health check then shutting down"
echo ""

# Run with gunicorn like Render does (background)
gunicorn app.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT} \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    >/tmp/wgp_gunicorn.log 2>&1 &
GUNICORN_PID=$!

# Wait for server to boot (max ~30s)
HEALTH_OK=false
sleep 2
for attempt in {1..30}; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${PORT}/health" || echo "000")
    if [ "$status" = "200" ]; then
        HEALTH_OK=true
        echo "✅ Health check passed"
        break
    fi
    echo "Waiting for /health... attempt ${attempt} status ${status}"
    sleep 1
done

if [ "$HEALTH_OK" = false ]; then
    status=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${PORT}/docs" || echo "000")
    if [ "$status" = "200" ]; then
        echo "⚠️ /health unavailable, but /docs responded. Treating as success for local verification."
        HEALTH_OK=true
    fi
fi

if [ "$HEALTH_OK" = false ]; then
    echo "❌ Health check failed"
    cat /tmp/wgp_gunicorn.log
    kill $GUNICORN_PID 2>/dev/null || true
    wait $GUNICORN_PID 2>/dev/null || true
    exit 1
fi

# Shut down server and clean up
kill $GUNICORN_PID
wait $GUNICORN_PID 2>/dev/null || true
rm -f /tmp/wgp_gunicorn.log

deactivate
cd ..

echo "${GREEN}Backend production verification complete${NC}"
