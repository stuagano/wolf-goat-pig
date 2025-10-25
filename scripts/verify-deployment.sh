#!/bin/bash

# Deployment Verification Script
# Verifies backend and frontend connectivity in production

set -e

echo "🔍 Wolf Goat Pig Deployment Verification"
echo "========================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default URLs
BACKEND_URL="${BACKEND_URL:-https://wolf-goat-pig.onrender.com}"
FRONTEND_URL="${FRONTEND_URL:-https://wolf-goat-pig.vercel.app}"

# Function to check HTTP endpoint
check_endpoint() {
    local url=$1
    local name=$2
    local expected_status=${3:-200}

    echo -e "${BLUE}Testing $name...${NC}"

    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 30 || echo "000")

    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✅ $name: OK (HTTP $response)${NC}"
        return 0
    else
        echo -e "${RED}❌ $name: FAILED (HTTP $response, expected $expected_status)${NC}"
        return 1
    fi
}

# Function to check CORS headers
check_cors() {
    local url=$1
    local origin=$2

    echo -e "${BLUE}Testing CORS from $origin...${NC}"

    cors_headers=$(curl -s -I -H "Origin: $origin" -H "Access-Control-Request-Method: GET" -X OPTIONS "$url" || echo "")

    if echo "$cors_headers" | grep -qi "access-control-allow-origin"; then
        echo -e "${GREEN}✅ CORS: Configured${NC}"
        return 0
    else
        echo -e "${RED}❌ CORS: Not properly configured${NC}"
        return 1
    fi
}

# Function to check API health with detailed info
check_api_health() {
    local url="$1/health"

    echo -e "${BLUE}Checking API health...${NC}"

    health_response=$(curl -s "$url" --max-time 30 || echo "{}")

    if echo "$health_response" | grep -q "status"; then
        echo -e "${GREEN}✅ API Health: Responding${NC}"
        echo "   Response: $health_response"
        return 0
    else
        echo -e "${RED}❌ API Health: Not responding properly${NC}"
        echo "   Response: $health_response"
        return 1
    fi
}

# Main verification flow
echo ""
echo -e "${BLUE}Backend URL: $BACKEND_URL${NC}"
echo -e "${BLUE}Frontend URL: $FRONTEND_URL${NC}"
echo ""

# Backend checks
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Backend Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

BACKEND_FAILURES=0

check_endpoint "$BACKEND_URL" "Backend Root" || ((BACKEND_FAILURES++))
check_api_health "$BACKEND_URL" || ((BACKEND_FAILURES++))
check_endpoint "$BACKEND_URL/docs" "API Documentation" || ((BACKEND_FAILURES++))
check_cors "$BACKEND_URL/health" "$FRONTEND_URL" || ((BACKEND_FAILURES++))

echo ""

# Frontend checks
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Frontend Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

FRONTEND_FAILURES=0

check_endpoint "$FRONTEND_URL" "Frontend Root" || ((FRONTEND_FAILURES++))
check_endpoint "$FRONTEND_URL/manifest.json" "Manifest" || ((FRONTEND_FAILURES++))

echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Verification Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL_FAILURES=$((BACKEND_FAILURES + FRONTEND_FAILURES))

if [ $BACKEND_FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ Backend: All checks passed${NC}"
else
    echo -e "${RED}❌ Backend: $BACKEND_FAILURES check(s) failed${NC}"
fi

if [ $FRONTEND_FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend: All checks passed${NC}"
else
    echo -e "${RED}❌ Frontend: $FRONTEND_FAILURES check(s) failed${NC}"
fi

echo ""

if [ $TOTAL_FAILURES -eq 0 ]; then
    echo -e "${GREEN}🎉 All deployment checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ $TOTAL_FAILURES check(s) failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Verify backend is deployed on Render: $BACKEND_URL"
    echo "  2. Verify frontend is deployed on Vercel: $FRONTEND_URL"
    echo "  3. Check Vercel environment variables (REACT_APP_API_URL)"
    echo "  4. Check Render environment variables (FRONTEND_URL)"
    echo "  5. Check CORS configuration in backend/app/main.py"
    echo ""
    exit 1
fi
