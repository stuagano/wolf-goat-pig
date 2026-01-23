#!/bin/bash

# Post-Deployment Verification Script
# Validates that deployment was successful and caches are properly busted
#
# This script catches issues like:
# - Service worker not updating (stale cache)
# - Version mismatch between build and deployed
# - CSS/JS not loading properly
# - API connectivity issues

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
FRONTEND_URL="${FRONTEND_URL:-https://wolf-goat-pig.vercel.app}"
BACKEND_URL="${BACKEND_URL:-https://wolf-goat-pig.onrender.com}"
EXPECTED_VERSION="${EXPECTED_VERSION:-}"
MAX_RETRIES=5
RETRY_DELAY=10

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "    POST-DEPLOYMENT VERIFICATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo "Expected Version: ${EXPECTED_VERSION:-'(not specified)'}"
echo ""

FAILURES=0
WARNINGS=0

# Function to log results
log_pass() { echo -e "${GREEN}✅ PASS:${NC} $1"; }
log_fail() { echo -e "${RED}❌ FAIL:${NC} $1"; ((FAILURES++)); }
log_warn() { echo -e "${YELLOW}⚠️  WARN:${NC} $1"; ((WARNINGS++)); }
log_info() { echo -e "${BLUE}ℹ️  INFO:${NC} $1"; }

# 1. Check version.json is accessible and valid
echo ""
echo "━━━ Version Verification ━━━"

VERSION_RESPONSE=$(curl -s --max-time 15 "${FRONTEND_URL}/version.json" 2>/dev/null || echo "FETCH_FAILED")

if [ "$VERSION_RESPONSE" = "FETCH_FAILED" ]; then
    log_fail "Could not fetch version.json"
else
    # Validate JSON
    if echo "$VERSION_RESPONSE" | jq . >/dev/null 2>&1; then
        DEPLOYED_VERSION=$(echo "$VERSION_RESPONSE" | jq -r '.version // empty')
        BUILD_TIME=$(echo "$VERSION_RESPONSE" | jq -r '.buildTime // empty')

        if [ -n "$DEPLOYED_VERSION" ]; then
            log_pass "version.json accessible (v${DEPLOYED_VERSION})"
            log_info "Build time: $BUILD_TIME"

            # Check if expected version matches
            if [ -n "$EXPECTED_VERSION" ] && [ "$DEPLOYED_VERSION" != "$EXPECTED_VERSION" ]; then
                log_fail "Version mismatch! Expected: $EXPECTED_VERSION, Got: $DEPLOYED_VERSION"
            fi
        else
            log_fail "version.json missing 'version' field"
        fi
    else
        log_fail "version.json is not valid JSON"
    fi
fi

# 2. Check service worker is served with correct headers
echo ""
echo "━━━ Service Worker Verification ━━━"

SW_HEADERS=$(curl -sI --max-time 15 "${FRONTEND_URL}/service-worker.js" 2>/dev/null || echo "FETCH_FAILED")

if [ "$SW_HEADERS" = "FETCH_FAILED" ]; then
    log_fail "Could not fetch service-worker.js headers"
else
    # Check HTTP status
    HTTP_STATUS=$(echo "$SW_HEADERS" | head -1 | grep -o '[0-9][0-9][0-9]' | head -1)
    if [ "$HTTP_STATUS" = "200" ]; then
        log_pass "service-worker.js returns HTTP 200"
    else
        log_fail "service-worker.js returns HTTP $HTTP_STATUS (expected 200)"
    fi

    # Check cache headers - should NOT be aggressively cached
    if echo "$SW_HEADERS" | grep -qi "cache-control.*no-cache\|cache-control.*max-age=0"; then
        log_pass "Service worker has no-cache headers (good for updates)"
    elif echo "$SW_HEADERS" | grep -qi "cache-control.*max-age"; then
        MAX_AGE=$(echo "$SW_HEADERS" | grep -i "cache-control" | grep -o 'max-age=[0-9]*' | head -1)
        log_warn "Service worker has cache headers: $MAX_AGE"
    fi
fi

# 3. Verify service worker contains expected version
SW_CONTENT=$(curl -s --max-time 15 "${FRONTEND_URL}/service-worker.js" 2>/dev/null || echo "FETCH_FAILED")

if [ "$SW_CONTENT" != "FETCH_FAILED" ]; then
    SW_VERSION=$(echo "$SW_CONTENT" | grep -o "SW_VERSION = '[^']*'" | head -1 || echo "")
    if [ -n "$SW_VERSION" ]; then
        log_pass "Service worker version found: $SW_VERSION"
    else
        log_warn "Could not extract SW_VERSION from service worker"
    fi
fi

# 4. Check main HTML loads and contains expected elements
echo ""
echo "━━━ Frontend HTML Verification ━━━"

HTML_CONTENT=$(curl -s --max-time 15 "${FRONTEND_URL}" 2>/dev/null || echo "FETCH_FAILED")

if [ "$HTML_CONTENT" = "FETCH_FAILED" ]; then
    log_fail "Could not fetch frontend HTML"
else
    # Check for React root
    if echo "$HTML_CONTENT" | grep -q 'id="root"'; then
        log_pass "React root element found"
    else
        log_fail "React root element missing"
    fi

    # Check for CSS links
    CSS_COUNT=$(echo "$HTML_CONTENT" | grep -c 'link.*stylesheet\|\.css"' || echo "0")
    if [ "$CSS_COUNT" -gt 0 ]; then
        log_pass "CSS stylesheets found ($CSS_COUNT links)"
    else
        log_warn "No CSS stylesheet links found in HTML"
    fi

    # Check for JS bundles
    JS_COUNT=$(echo "$HTML_CONTENT" | grep -c '\.js"' || echo "0")
    if [ "$JS_COUNT" -gt 0 ]; then
        log_pass "JavaScript bundles found ($JS_COUNT scripts)"
    else
        log_warn "No JavaScript bundle links found in HTML"
    fi

    # Check for service worker registration
    if echo "$HTML_CONTENT" | grep -qi "serviceWorker\|service-worker"; then
        log_pass "Service worker reference found in HTML"
    else
        log_info "No service worker reference in HTML (may be in JS bundle)"
    fi
fi

# 5. Check static assets load correctly (sample CSS/JS files)
echo ""
echo "━━━ Static Asset Verification ━━━"

# Extract and test first JS file
JS_FILE=$(echo "$HTML_CONTENT" | grep -o '/static/js/[^"]*\.js' | head -1)
if [ -n "$JS_FILE" ]; then
    JS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "${FRONTEND_URL}${JS_FILE}" 2>/dev/null || echo "000")
    if [ "$JS_STATUS" = "200" ]; then
        log_pass "JavaScript bundle loads (${JS_FILE})"
    else
        log_fail "JavaScript bundle failed to load: HTTP $JS_STATUS"
    fi
fi

# Extract and test first CSS file
CSS_FILE=$(echo "$HTML_CONTENT" | grep -o '/static/css/[^"]*\.css' | head -1)
if [ -n "$CSS_FILE" ]; then
    CSS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "${FRONTEND_URL}${CSS_FILE}" 2>/dev/null || echo "000")
    if [ "$CSS_STATUS" = "200" ]; then
        log_pass "CSS stylesheet loads (${CSS_FILE})"
    else
        log_fail "CSS stylesheet failed to load: HTTP $CSS_STATUS"
    fi
fi

# 6. Check manifest.json
MANIFEST_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "${FRONTEND_URL}/manifest.json" 2>/dev/null || echo "000")
if [ "$MANIFEST_STATUS" = "200" ]; then
    log_pass "manifest.json accessible"
else
    log_warn "manifest.json not accessible: HTTP $MANIFEST_STATUS"
fi

# 7. Backend connectivity from frontend perspective
echo ""
echo "━━━ Backend Connectivity ━━━"

BACKEND_HEALTH=$(curl -s --max-time 30 "${BACKEND_URL}/health" 2>/dev/null || echo "FETCH_FAILED")

if [ "$BACKEND_HEALTH" = "FETCH_FAILED" ]; then
    log_fail "Could not reach backend health endpoint"
else
    if echo "$BACKEND_HEALTH" | grep -qi "status.*healthy\|status.*ok"; then
        log_pass "Backend health check passed"
    else
        log_warn "Backend returned unexpected health response: $BACKEND_HEALTH"
    fi
fi

# 8. CORS check
CORS_CHECK=$(curl -s -I -H "Origin: ${FRONTEND_URL}" "${BACKEND_URL}/health" 2>/dev/null | grep -i "access-control-allow-origin" || echo "")
if [ -n "$CORS_CHECK" ]; then
    log_pass "CORS headers present"
else
    log_warn "CORS headers not detected (may affect frontend-backend communication)"
fi

# 9. Cache-busting verification (compare two fetches)
echo ""
echo "━━━ Cache Busting Verification ━━━"

# Fetch version.json twice with cache-busting query params
V1=$(curl -s --max-time 10 "${FRONTEND_URL}/version.json?t=$(date +%s)" 2>/dev/null | jq -r '.version // empty' 2>/dev/null)
sleep 1
V2=$(curl -s --max-time 10 "${FRONTEND_URL}/version.json?t=$(date +%s)" 2>/dev/null | jq -r '.version // empty' 2>/dev/null)

if [ -n "$V1" ] && [ -n "$V2" ] && [ "$V1" = "$V2" ]; then
    log_pass "Consistent version across requests: $V1"
else
    log_warn "Inconsistent versions: $V1 vs $V2 (possible CDN caching issue)"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "    VERIFICATION SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $FAILURES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}🎉 All checks passed! Deployment verified successfully.${NC}"
    exit 0
elif [ $FAILURES -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Deployment verified with $WARNINGS warning(s).${NC}"
    echo "Review warnings above - deployment may work but could have issues."
    exit 0
else
    echo -e "${RED}❌ Deployment verification FAILED with $FAILURES error(s) and $WARNINGS warning(s).${NC}"
    echo ""
    echo "Troubleshooting steps:"
    echo "  1. Check Vercel deployment logs for build errors"
    echo "  2. Verify version.json was created during build"
    echo "  3. Clear CDN cache if version mismatch persists"
    echo "  4. Check browser DevTools for service worker status"
    echo "  5. Hard refresh (Ctrl+Shift+R) to bypass local cache"
    exit 1
fi
