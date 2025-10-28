#!/bin/bash

# Run Playwright tests in Podman container
# Usage: ./scripts/run-playwright-podman.sh [test-pattern]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎭 Running Playwright Tests in Podman${NC}"
echo "================================================"

# Check if podman is installed
if ! command -v podman &> /dev/null; then
    echo -e "${RED}❌ Error: podman is not installed${NC}"
    echo "Install with: brew install podman"
    exit 1
fi

# Initialize podman machine if needed
echo -e "${BLUE}📦 Checking Podman machine status...${NC}"
if ! podman machine list | grep -q "Currently running"; then
    echo -e "${YELLOW}⚠️  Starting Podman machine...${NC}"
    podman machine start || true
    sleep 5
fi

# Build the container
IMAGE_NAME="wgp-playwright-tests"
echo -e "${BLUE}🔨 Building Playwright test container...${NC}"

cd "$PROJECT_ROOT"

podman build \
    -f tests/e2e/Dockerfile \
    -t "$IMAGE_NAME" \
    . || {
        echo -e "${RED}❌ Container build failed${NC}"
        exit 1
    }

echo -e "${GREEN}✅ Container built successfully${NC}"

# Start backend API (needed for tests)
echo -e "${BLUE}🚀 Starting backend API...${NC}"
BACKEND_CONTAINER="wgp-backend-test"

# Check if backend is already running
if podman ps | grep -q "$BACKEND_CONTAINER"; then
    echo -e "${YELLOW}⚠️  Backend container already running, using existing instance${NC}"
else
    # Start backend in background
    podman run -d \
        --name "$BACKEND_CONTAINER" \
        --rm \
        -p 8000:8000 \
        -v "$PROJECT_ROOT/backend:/app/backend" \
        -w /app/backend \
        python:3.11 \
        bash -c "pip install -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port 8000" || {
            echo -e "${YELLOW}⚠️  Could not start backend container (may already be running locally)${NC}"
        }

    # Wait for backend to be ready
    echo -e "${BLUE}⏳ Waiting for backend to be ready...${NC}"
    sleep 5
fi

# Start frontend dev server
echo -e "${BLUE}🌐 Starting frontend server...${NC}"
FRONTEND_CONTAINER="wgp-frontend-test"

# Check if frontend is already running
if podman ps | grep -q "$FRONTEND_CONTAINER"; then
    echo -e "${YELLOW}⚠️  Frontend container already running, using existing instance${NC}"
else
    # Start frontend in background
    podman run -d \
        --name "$FRONTEND_CONTAINER" \
        --rm \
        -p 3001:3000 \
        -v "$PROJECT_ROOT/frontend:/app" \
        -w /app \
        -e REACT_APP_API_URL=http://host.containers.internal:8000 \
        node:20 \
        bash -c "npm install && npm start" || {
            echo -e "${YELLOW}⚠️  Could not start frontend container (may already be running locally)${NC}"
        }

    # Wait for frontend to be ready
    echo -e "${BLUE}⏳ Waiting for frontend to be ready...${NC}"
    sleep 10
fi

# Run Playwright tests
echo -e "${BLUE}🧪 Running Playwright tests...${NC}"
TEST_PATTERN="${1:-}"

if [ -z "$TEST_PATTERN" ]; then
    # Run all tests
    podman run \
        --rm \
        --network host \
        -v "$PROJECT_ROOT/tests/e2e/test-results:/app/tests/e2e/test-results" \
        -v "$PROJECT_ROOT/tests/e2e/playwright-report:/app/tests/e2e/playwright-report" \
        -e BASE_URL=http://localhost:3001 \
        -e CI=true \
        "$IMAGE_NAME" \
        npx playwright test --reporter=list
else
    # Run specific test pattern
    echo -e "${BLUE}📝 Running tests matching: ${TEST_PATTERN}${NC}"
    podman run \
        --rm \
        --network host \
        -v "$PROJECT_ROOT/tests/e2e/test-results:/app/tests/e2e/test-results" \
        -v "$PROJECT_ROOT/tests/e2e/playwright-report:/app/tests/e2e/playwright-report" \
        -e BASE_URL=http://localhost:3001 \
        -e CI=true \
        "$IMAGE_NAME" \
        npx playwright test --reporter=list --grep "$TEST_PATTERN"
fi

TEST_EXIT_CODE=$?

# Cleanup
echo -e "${BLUE}🧹 Cleaning up containers...${NC}"
podman stop "$BACKEND_CONTAINER" 2>/dev/null || true
podman stop "$FRONTEND_CONTAINER" 2>/dev/null || true

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All Playwright tests passed!${NC}"
    echo -e "${BLUE}📊 Test results saved to: tests/e2e/test-results/${NC}"
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo -e "${BLUE}📊 View test report: npx playwright show-report tests/e2e/playwright-report${NC}"
    exit 1
fi
