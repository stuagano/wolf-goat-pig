#!/bin/bash

# Test production-like frontend deployment locally
# Simulates Vercel deployment environment

set -e

echo "🔍 Testing Production Frontend Build..."
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "frontend/package.json" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    exit 1
fi

# Create production environment file if needed
if [ ! -f "frontend/.env.production" ]; then
    echo -e "${YELLOW}Creating frontend/.env.production...${NC}"
    cat > frontend/.env.production << EOF
# Production Frontend Environment
REACT_APP_API_URL=https://your-backend-url.onrender.com
NODE_ENV=production
GENERATE_SOURCEMAP=false
EOF
    echo -e "${YELLOW}Please edit frontend/.env.production with your production API URL${NC}"
fi

cd frontend

echo -e "\n${GREEN}1. Installing dependencies...${NC}"
npm ci  # Use ci for reproducible builds like Vercel

echo -e "\n${GREEN}2. Running production build...${NC}"
npm run build

# Check if build succeeded
if [ ! -d "build" ]; then
    echo -e "${RED}Build failed! No build directory created.${NC}"
    exit 1
fi

# Check build size
BUILD_SIZE=$(du -sh build | cut -f1)
echo -e "${GREEN}✓ Build successful! Size: ${BUILD_SIZE}${NC}"

echo -e "\n${GREEN}3. Analyzing build...${NC}"
echo "Build contents:"
ls -la build/

# Check for common issues
echo -e "\n${BLUE}Checking for common deployment issues...${NC}"

# Check if index.html exists
if [ ! -f "build/index.html" ]; then
    echo -e "${RED}⚠ Missing index.html${NC}"
else
    echo -e "${GREEN}✓ index.html found${NC}"
fi

# Check if static assets exist
if [ ! -d "build/static" ]; then
    echo -e "${RED}⚠ Missing static directory${NC}"
else
    echo -e "${GREEN}✓ Static assets found${NC}"
    echo "  JS files: $(find build/static/js -name "*.js" 2>/dev/null | wc -l)"
    echo "  CSS files: $(find build/static/css -name "*.css" 2>/dev/null | wc -l)"
fi

# Check for environment variables in build
echo -e "\n${BLUE}Checking environment configuration...${NC}"
if grep -q "REACT_APP_API_URL" build/static/js/*.js 2>/dev/null; then
    echo -e "${YELLOW}⚠ Found REACT_APP_API_URL in build (this is expected)${NC}"
    FOUND_URL=$(grep -oh 'https://[^"]*onrender.com' build/static/js/*.js 2>/dev/null | head -1 || echo "Not found")
    echo "  Configured API URL: $FOUND_URL"
fi

echo -e "\n${GREEN}4. Starting local production server...${NC}"
echo "Installing serve if needed..."
npm install -g serve 2>/dev/null || true

echo -e "\n${GREEN}Server starting at http://localhost:3000${NC}"
echo -e "${YELLOW}This simulates Vercel's static hosting${NC}"
echo "Press Ctrl+C to stop"
echo ""

# Serve the production build
npx serve -s build -l 3000