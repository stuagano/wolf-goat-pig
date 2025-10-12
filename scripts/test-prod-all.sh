#!/bin/bash

# Complete production testing workflow
# Tests both backend and frontend in production-like environment

set -e

echo "🚀 Wolf-Goat-Pig Production Testing Suite"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to handle cleanup
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    # Kill any running servers
    pkill -f "gunicorn app.main:app" 2>/dev/null || true
    pkill -f "serve -s build" 2>/dev/null || true
    # Deactivate virtual environments
    deactivate 2>/dev/null || true
}

# Set up trap for cleanup on exit
trap cleanup EXIT

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required but not installed${NC}"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is required but not installed${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker not found - skipping Docker tests${NC}"
    SKIP_DOCKER=true
else
    SKIP_DOCKER=false
fi

# Menu for test selection
echo -e "\n${BLUE}Select testing mode:${NC}"
echo "1) Quick test (Backend + Frontend separately)"
echo "2) Full Docker production test"
echo "3) Backend only (Render simulation)"
echo "4) Frontend only (Vercel simulation)"
echo "5) Verification only (test existing services)"
echo "6) All tests (comprehensive)"

read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        echo -e "\n${GREEN}Running Quick Test...${NC}"

        # Start backend in background
        echo -e "${BLUE}Starting backend...${NC}"
        ./scripts/test-prod-backend.sh &
        BACKEND_PID=$!
        sleep 10  # Wait for backend to start

        # Start frontend in background
        echo -e "${BLUE}Starting frontend...${NC}"
        ./scripts/test-prod-frontend.sh &
        FRONTEND_PID=$!
        sleep 10  # Wait for frontend to build and start

        # Run verification
        echo -e "${BLUE}Running verification tests...${NC}"
        python scripts/verify-deployments.py

        # Cleanup
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
        ;;

    2)
        if [ "$SKIP_DOCKER" = true ]; then
            echo -e "${RED}Docker is required for this test${NC}"
            exit 1
        fi

        echo -e "\n${GREEN}Running Docker Production Test...${NC}"

        # Check if docker-compose.prod.yml exists
        if [ ! -f "docker-compose.prod.yml" ]; then
            echo -e "${RED}docker-compose.prod.yml not found${NC}"
            exit 1
        fi

        # Start Docker containers
        echo -e "${BLUE}Building and starting Docker containers...${NC}"
        docker-compose -f docker-compose.prod.yml up --build -d

        # Wait for services to be ready
        echo -e "${YELLOW}Waiting for services to start...${NC}"
        sleep 20

        # Run verification
        echo -e "${BLUE}Running verification tests...${NC}"
        python scripts/verify-deployments.py

        # Show logs
        echo -e "\n${BLUE}Container logs:${NC}"
        docker-compose -f docker-compose.prod.yml logs --tail=50

        # Prompt for cleanup
        read -p "Stop Docker containers? [y/N]: " stop_docker
        if [[ $stop_docker =~ ^[Yy]$ ]]; then
            docker-compose -f docker-compose.prod.yml down
        fi
        ;;

    3)
        echo -e "\n${GREEN}Running Backend Test Only...${NC}"
        ./scripts/test-prod-backend.sh
        ;;

    4)
        echo -e "\n${GREEN}Running Frontend Test Only...${NC}"
        ./scripts/test-prod-frontend.sh
        ;;

    5)
        echo -e "\n${GREEN}Running Verification Only...${NC}"

        # Get URLs from user
        read -p "Backend URL [http://localhost:8000]: " BACKEND_URL
        BACKEND_URL=${BACKEND_URL:-http://localhost:8000}

        read -p "Frontend URL [http://localhost:3000]: " FRONTEND_URL
        FRONTEND_URL=${FRONTEND_URL:-http://localhost:3000}

        python scripts/verify-deployments.py \
            --backend "$BACKEND_URL" \
            --frontend "$FRONTEND_URL"
        ;;

    6)
        echo -e "\n${GREEN}Running All Tests...${NC}"

        # Test 1: Backend standalone
        echo -e "\n${BLUE}Test 1/4: Backend Production Build${NC}"
        timeout 30 ./scripts/test-prod-backend.sh || true

        # Test 2: Frontend standalone
        echo -e "\n${BLUE}Test 2/4: Frontend Production Build${NC}"
        timeout 30 ./scripts/test-prod-frontend.sh || true

        # Test 3: Docker if available
        if [ "$SKIP_DOCKER" = false ]; then
            echo -e "\n${BLUE}Test 3/4: Docker Compose Test${NC}"
            docker-compose -f docker-compose.prod.yml up --build -d
            sleep 20
            python scripts/verify-deployments.py
            docker-compose -f docker-compose.prod.yml down
        else
            echo -e "\n${YELLOW}Test 3/4: Docker test skipped (Docker not installed)${NC}"
        fi

        # Test 4: Final verification
        echo -e "\n${BLUE}Test 4/4: Production Readiness Check${NC}"

        # Check for common issues
        echo "Checking for common deployment issues..."

        # Check backend
        if [ -f "backend/requirements.txt" ]; then
            echo -e "${GREEN}✓${NC} Backend requirements.txt found"
        else
            echo -e "${RED}✗${NC} Backend requirements.txt missing"
        fi

        # Check frontend build
        if [ -f "frontend/package.json" ]; then
            echo -e "${GREEN}✓${NC} Frontend package.json found"
        else
            echo -e "${RED}✗${NC} Frontend package.json missing"
        fi

        # Check environment files
        if [ -f ".env.example" ]; then
            echo -e "${GREEN}✓${NC} Environment example file found"
        else
            echo -e "${YELLOW}⚠${NC} No .env.example file"
        fi

        echo -e "\n${GREEN}All tests completed!${NC}"
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "\n${GREEN}Testing complete!${NC}"
echo "Check the generated deployment-test-*.json files for detailed results."