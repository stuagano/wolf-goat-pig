#!/bin/bash

# Wolf Goat Pig Deployment Script
# Runs pre-deployment validation and triggers deployment

set -e  # Exit on any error

echo "🚀 Wolf Goat Pig Deployment Pipeline"
echo "===================================="

# Step 1: Run pre-deployment validation
echo "📋 Step 1: Running pre-deployment validation..."
python3 scripts/pre_deploy_check.py

if [ $? -ne 0 ]; then
    echo "❌ Pre-deployment validation failed!"
    echo "🔧 Please fix the issues before deploying."
    exit 1
fi

echo "✅ Pre-deployment validation passed!"

# Step 2: Git status check
echo ""
echo "📋 Step 2: Checking git status..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: You have uncommitted changes"
    echo "🔧 Consider committing your changes before deployment"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 3: Build frontend locally to catch issues early
echo ""
echo "📋 Step 3: Testing frontend build..."
cd frontend
npm ci --prefer-offline --no-audit
npm run build
if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed!"
    exit 1
fi
cd ..
echo "✅ Frontend build successful!"

# Step 4: Commit and push (if changes exist)
echo ""
echo "📋 Step 4: Pushing to repository..."
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 Committing changes..."
    git add .
    git commit -m "deployment: fixes and improvements $(date '+%Y-%m-%d %H:%M:%S')"
fi

git push origin main
echo "✅ Code pushed to repository!"

echo ""
echo "🎉 Deployment pipeline completed successfully!"
echo "🚀 Your changes should now trigger auto-deployment on Render"
echo ""
echo "📊 Monitor your deployment at:"
echo "   • Backend:  https://dashboard.render.com/"
echo "   • Frontend: https://dashboard.render.com/"
echo ""
echo "🔍 Check deployment status with:"
echo "   curl https://wolf-goat-pig-api.onrender.com/health"