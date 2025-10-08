#!/bin/bash

# Test Local Development Setup

API_BASE=${WGP_API_BASE:-http://localhost:8000}

echo "🧪 Testing Wolf-Goat-Pig Local Development Setup against ${API_BASE}..."
echo ""

# Test backend
echo "📦 Testing Backend API..."
BACKEND_RESPONSE=$(curl -s "${API_BASE}/health" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ Backend is running at ${API_BASE}"
else
    echo "❌ Backend is not running. Start with: cd backend && python -m uvicorn app.main:app --reload"
    exit 1
fi

# Test specific endpoints
echo ""
echo "Testing API Endpoints:"

# Test personalities endpoint
PERSONALITIES=$(curl -s "${API_BASE}/personalities" 2>/dev/null)
if echo "$PERSONALITIES" | grep -q "aggressive"; then
    echo "✅ /personalities endpoint working"
else
    echo "❌ /personalities endpoint failed"
fi

# Test suggested opponents endpoint
OPPONENTS=$(curl -s "${API_BASE}/suggested_opponents" 2>/dev/null)
if echo "$OPPONENTS" | grep -q "Clive"; then
    echo "✅ /suggested_opponents endpoint working"
else
    echo "❌ /suggested_opponents endpoint failed"
fi

# Test courses endpoint
COURSES=$(curl -s "${API_BASE}/courses" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ /courses endpoint working"
else
    echo "❌ /courses endpoint failed"
fi

# Test frontend
echo ""
echo "🎨 Testing Frontend..."
FRONTEND_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null)
if [ "$FRONTEND_CHECK" = "200" ]; then
    echo "✅ Frontend is running on port 3000"
else
    echo "⚠️  Frontend may still be starting up or not running"
    echo "   Start with: cd frontend && npm start"
fi

echo ""
echo "========================================="
echo "📊 Test Summary:"
echo "========================================="
echo "Backend URL:  http://localhost:8000"
echo "Frontend URL: http://localhost:3000"
echo "API Docs:     http://localhost:8000/docs"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Navigate to the simulation setup"
echo "3. Test the game flow"
echo "========================================="