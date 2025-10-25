#!/bin/bash

# Local Development Connectivity Test
# Verifies backend/frontend can communicate locally

set -e

echo "🔍 Local Development Connectivity Test"
echo "======================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Local URLs
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

# Function to check if service is running
check_service() {
    local url=$1
    local name=$2

    echo -e "${BLUE}Checking $name at $url...${NC}"

    if curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 5 | grep -q "200\|404"; then
        echo -e "${GREEN}✅ $name: Running${NC}"
        return 0
    else
        echo -e "${RED}❌ $name: Not running${NC}"
        return 1
    fi
}

# Function to test API endpoint
test_api() {
    local url=$1
    local endpoint=$2

    echo -e "${BLUE}Testing $endpoint...${NC}"

    response=$(curl -s "$url$endpoint" --max-time 5 || echo "ERROR")

    if [ "$response" != "ERROR" ]; then
        echo -e "${GREEN}✅ $endpoint: Responding${NC}"
        return 0
    else
        echo -e "${RED}❌ $endpoint: Failed${NC}"
        return 1
    fi
}

# Function to test CORS
test_cors() {
    local backend=$1
    local frontend=$2

    echo -e "${BLUE}Testing CORS configuration...${NC}"

    cors_response=$(curl -s -I \
        -H "Origin: $frontend" \
        -H "Access-Control-Request-Method: GET" \
        -X OPTIONS \
        "$backend/health" || echo "")

    if echo "$cors_response" | grep -qi "access-control-allow-origin"; then
        echo -e "${GREEN}✅ CORS: Configured for $frontend${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  CORS: May not be configured for $frontend${NC}"
        return 1
    fi
}

# Main test flow
echo ""
echo -e "${BLUE}Backend URL: $BACKEND_URL${NC}"
echo -e "${BLUE}Frontend URL: $FRONTEND_URL${NC}"
echo ""

FAILURES=0

# Check if services are running
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Service Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_service "$BACKEND_URL" "Backend" || {
    echo -e "${YELLOW}💡 Start backend with: cd backend && uvicorn app.main:app --reload${NC}"
    ((FAILURES++))
}

check_service "$FRONTEND_URL" "Frontend" || {
    echo -e "${YELLOW}💡 Start frontend with: cd frontend && npm start${NC}"
    ((FAILURES++))
}

echo ""

# Test API endpoints
if [ $FAILURES -eq 0 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " API Endpoint Tests"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    test_api "$BACKEND_URL" "/health" || ((FAILURES++))
    test_api "$BACKEND_URL" "/docs" || ((FAILURES++))
    test_api "$BACKEND_URL" "/api/players" || ((FAILURES++))

    echo ""

    # Test CORS
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " CORS Configuration"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    test_cors "$BACKEND_URL" "$FRONTEND_URL" || {
        echo -e "${YELLOW}💡 CORS may need to be configured in backend/app/main.py${NC}"
        ((FAILURES++))
    }

    echo ""
fi

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}🎉 All connectivity tests passed!${NC}"
    echo ""
    echo "✅ Backend and frontend are communicating properly"
    echo ""
    exit 0
else
    echo -e "${RED}❌ $FAILURES test(s) failed${NC}"
    echo ""
    echo "Troubleshooting steps:"
    echo "  1. Ensure backend is running on $BACKEND_URL"
    echo "  2. Ensure frontend is running on $FRONTEND_URL"
    echo "  3. Check CORS configuration in backend/app/main.py"
    echo "  4. Check REACT_APP_API_URL in frontend/.env.local"
    echo "  5. Check proxy setting in frontend/package.json"
    echo ""
    exit 1
fi
