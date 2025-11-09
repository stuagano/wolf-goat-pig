#!/bin/bash
#
# Run Playwright E2E tests in a Podman container
# This bypasses local Chromium permission issues
#
# Usage:
#   ./run-in-podman.sh                    # Run all tests
#   ./run-in-podman.sh smoke-test.spec.js # Run specific test

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🐳 Running Playwright E2E Tests in Podman${NC}"
echo ""

# Get the test file (optional)
TEST_FILE="${1:-tests/e2e/tests/}"

# Get absolute paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../../.." && pwd )"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo -e "${YELLOW}Project root:${NC} $PROJECT_ROOT"
echo -e "${YELLOW}Frontend dir:${NC} $FRONTEND_DIR"
echo -e "${YELLOW}Backend dir:${NC} $BACKEND_DIR"
echo -e "${YELLOW}Test target:${NC} $TEST_FILE"
echo ""

# Check if backend is running
if ! curl -s http://localhost:8000 > /dev/null 2>&1; then
  echo -e "${RED}❌ Backend not running on port 8000${NC}"
  echo -e "${YELLOW}Please start backend:${NC} cd backend && uvicorn app.main:app --reload"
  exit 1
fi

# Check if frontend is running
if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
  echo -e "${RED}❌ Frontend not running on port 3000${NC}"
  echo -e "${YELLOW}Please start frontend:${NC} cd frontend && npm start"
  exit 1
fi

echo -e "${GREEN}✅ Backend and Frontend are running${NC}"
echo ""

# Run Playwright tests in Podman
echo -e "${GREEN}🚀 Starting Playwright tests in Podman container...${NC}"
echo ""

podman run --rm \
  --network=host \
  -v "$FRONTEND_DIR:/work" \
  -w /work \
  mcr.microsoft.com/playwright:v1.48.1-jammy \
  /bin/bash -c "
    echo '📦 Installing dependencies...'
    npm install
    echo ''
    echo '🎭 Running Playwright tests...'
    npx playwright test --config=tests/e2e/playwright.config.js $TEST_FILE
  "

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}✅ Tests completed successfully!${NC}"
else
  echo -e "${RED}❌ Tests failed with exit code $EXIT_CODE${NC}"
  echo ""
  echo -e "${YELLOW}View test report:${NC}"
  echo "  cd frontend && npm run test:e2e:report"
fi

exit $EXIT_CODE
