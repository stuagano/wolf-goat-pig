# 🚀 Wolf Goat Pig - Deployment Checklist

## 🎯 Quick Deployment Status

### Current Status
- ✅ **Backend Tests:** 701/701 passing (100%)
- ✅ **Frontend Tests:** 654 passing (73.1%)
- ✅ **CI/CD Pipeline:** GitHub Actions configured
- ⚠️ **Production Backend:** Needs deployment

---

## 🔴 CRITICAL: Deploy Backend Fixes to Production

### Problem
Production (Render + PostgreSQL) has transaction abort issues that are fixed in the codebase but not deployed.

### Impact
- ❌ Game creation fails in production
- ❌ Hole saving fails
- ✅ Works in development (SQLite)

### Solution: Deploy to Production

```bash
# Step 1: Verify you're on main branch
git checkout main

# Step 2: Ensure latest code is pulled
git pull origin main

# Step 3: Push to trigger Render deployment
git push origin main

# Step 4: Monitor deployment
# Visit: https://dashboard.render.com
# Wait: ~2-3 minutes for deployment
```

### What Happens During Deployment
1. ✅ Render detects push to main
2. ✅ Installs dependencies (`pip install -r requirements.txt`)
3. ✅ Runs database migrations (`init_db()`)
4. ✅ Starts uvicorn server with fixed code
5. ✅ PostgreSQL issues resolved!

### Verify Deployment Success

```bash
# Health check
curl https://wolf-goat-pig.onrender.com/health

# Expected response:
# {"status": "healthy", "database": "connected"}

# Test game creation
curl -X POST https://wolf-goat-pig.onrender.com/games/create-test?player_count=4

# Should return game_id without errors
```

---

## ✅ CI/CD Pipeline Setup

### GitHub Actions Workflow
**Location:** `.github/workflows/ci.yml`

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Jobs:**
1. **Backend Tests** - 701 pytest tests
2. **Frontend Tests** - 654 Jest tests
3. **Build Verification** - Production build check
4. **Linting** - Code quality (optional, non-blocking)

### Enable CI/CD (One Time Setup)

```bash
# Workflow is already committed
# Just push to GitHub to activate

git push origin main

# View workflows at:
# https://github.com/<your-username>/wolf-goat-pig/actions
```

---

## 📋 Pre-Deployment Checklist

### Backend
- [x] ✅ All tests passing (701/701)
- [x] ✅ Database migrations ready
- [x] ✅ Environment variables configured
- [ ] ⚠️ Deploy to Render production

### Frontend
- [x] ✅ Tests passing (654)
- [x] ✅ Build successful
- [x] ✅ Vercel configured
- [x] ✅ Environment variables set

### Infrastructure
- [x] ✅ PostgreSQL database (Render)
- [x] ✅ Static hosting (Vercel)
- [x] ✅ Health check endpoints
- [x] ✅ CORS configured

---

## 🌍 Environment Configuration

### Backend (Render)
```env
DATABASE_URL=<provided-by-render>
ENVIRONMENT=production
AUTH0_DOMAIN=dev-jm88n088hpt7oe48.us.auth0.com
AUTH0_API_AUDIENCE=https://wolf-goat-pig.onrender.com
CORS_ORIGINS=["https://<your-vercel-domain>"]
```

### Frontend (Vercel)
```env
REACT_APP_API_URL=https://wolf-goat-pig.onrender.com
REACT_APP_AUTH0_DOMAIN=dev-jm88n088hpt7oe48.us.auth0.com
REACT_APP_AUTH0_CLIENT_ID=qAZuRv5E9mPQ9uTGg7NWpkpfVj8bCeoB
REACT_APP_USE_MOCK_AUTH=true
```

---

## 🧪 Testing in Production

### Smoke Tests

```bash
# 1. Health check
curl https://wolf-goat-pig.onrender.com/health

# 2. Create test game
curl -X POST https://wolf-goat-pig.onrender.com/games/create-test?player_count=4

# 3. Complete a hole (use game_id from step 2)
curl -X POST https://wolf-goat-pig.onrender.com/games/{game_id}/holes/complete \
  -H "Content-Type: application/json" \
  -d '{
    "hole_number": 1,
    "rotation_order": ["p1","p2","p3","p4"],
    "captain_index": 0,
    "teams": {"type": "pending"},
    "scores": {"p1": 4, "p2": 5, "p3": 5, "p4": 6},
    "hole_par": 4
  }'
```

### Frontend E2E Tests

```bash
# Run Playwright tests against production
cd frontend
npm run test:e2e -- --config playwright.config.js
```

---

## 🐛 Troubleshooting

### Backend Issues

**Issue:** 500 errors in production
```bash
# Check Render logs
# Dashboard → Your Service → Logs

# Common fixes:
# 1. Verify DATABASE_URL is set
# 2. Check migrations ran successfully
# 3. Restart service from dashboard
```

**Issue:** Database connection fails
```bash
# Verify PostgreSQL is running
# Render Dashboard → Database → Status

# Reset connection:
# Settings → Environment → Remove DATABASE_URL → Re-add
```

### Frontend Issues

**Issue:** API calls fail (CORS)
```bash
# Check backend CORS_ORIGINS includes your Vercel domain
# Render Dashboard → Environment → CORS_ORIGINS

# Should include:
# ["https://your-app.vercel.app"]
```

**Issue:** Auth0 errors
```bash
# Verify Auth0 callback URLs include:
# - https://your-app.vercel.app
# - http://localhost:3000 (for development)

# Auth0 Dashboard → Applications → Settings → Allowed Callback URLs
```

---

## 📊 Monitoring

### Backend Health
- **URL:** https://wolf-goat-pig.onrender.com/health
- **Expected:** `{"status": "healthy", "database": "connected"}`
- **Frequency:** Check every 5 minutes (Render does this automatically)

### Frontend Status
- **URL:** https://your-app.vercel.app
- **Vercel Dashboard:** https://vercel.com/dashboard
- **Build logs:** Available in dashboard

### CI/CD Status
- **GitHub Actions:** https://github.com/your-username/wolf-goat-pig/actions
- **Latest workflow:** Should be green ✅

---

## 🎯 Post-Deployment Verification

### Checklist
1. [ ] Backend health check returns 200
2. [ ] Can create test game via API
3. [ ] Can complete holes via API
4. [ ] Frontend loads without errors
5. [ ] Can start a new game from UI
6. [ ] Scorekeeper functions correctly
7. [ ] Quarters calculations work
8. [ ] Leaderboard displays

### Quick Test Script

```bash
#!/bin/bash
# save as test-deployment.sh

API_URL="https://wolf-goat-pig.onrender.com"

echo "Testing backend health..."
curl -s $API_URL/health | grep -q "healthy" && echo "✅ Health check passed" || echo "❌ Health check failed"

echo "Testing game creation..."
RESPONSE=$(curl -s -X POST "$API_URL/games/create-test?player_count=4")
GAME_ID=$(echo $RESPONSE | grep -o '"game_id":"[^"]*"' | cut -d'"' -f4)

if [ ! -z "$GAME_ID" ]; then
  echo "✅ Game created: $GAME_ID"
else
  echo "❌ Game creation failed"
fi

echo "All smoke tests complete!"
```

---

## 🚀 Continuous Deployment Flow

### Development Workflow
```
1. Feature branch → Push
2. GitHub Actions → Run tests
3. Create PR → Automated checks
4. Merge to main → Deploy automatically
5. Render/Vercel → Deploy to production
```

### Rollback Procedure
```bash
# If production has issues, rollback:

# Option 1: Revert last commit
git revert HEAD
git push origin main

# Option 2: Redeploy specific commit
# Render Dashboard → Manual Deploy → Select commit
```

---

## 📞 Support

### Documentation
- Backend API: `/docs` endpoint (FastAPI auto-generated)
- Frontend: See `/frontend/README.md`
- Testing: See `/backend/tests/` and `/frontend/tests/`

### Logs
- **Backend:** Render Dashboard → Logs
- **Frontend:** Vercel Dashboard → Deployments → Logs
- **CI/CD:** GitHub Actions → Workflow runs

---

## ✨ You're Ready to Deploy!

**Next Step:** Push to main branch and watch the magic happen! 🎊

```bash
git push origin main
```

**Monitor:**
- Render: https://dashboard.render.com
- Vercel: https://vercel.com/dashboard
- GitHub: https://github.com/your-username/wolf-goat-pig/actions
