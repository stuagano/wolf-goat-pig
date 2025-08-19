# 🚀 Wolf Goat Pig - Agent Deployment Instructions

## Overview
This document provides specific instructions for AI agents to ensure successful deployments when pushing code changes to the wolf-goat-pig project.

## 🏗️ Architecture Overview

**Backend**: FastAPI + SQLAlchemy + PostgreSQL (Render)
**Frontend**: React SPA (Vercel)
**Deployments**: 
- Backend → Render (render.yaml)
- Frontend → Vercel (vercel.json)

## ⚠️ Critical Deployment Gates

Before making ANY code changes, agents MUST verify these gates:

### 1. 🐍 Backend Health Gate
```bash
# ALWAYS run this first
cd backend && source venv/bin/activate
python -c "from app.database import init_db; init_db()"
python -m pytest tests/test_api_endpoints.py -v
```
**Requirement**: Tests must pass OR at least not introduce new failures

### 2. ⚛️ Frontend Build Gate  
```bash
# ALWAYS run this before committing frontend changes
cd frontend
npm ci
npm run build
```
**Requirement**: Build must complete successfully (warnings OK, errors FAIL)

### 3. 🔗 Integration Gate
```bash
# Test backend startup
uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 &
# Wait 3 seconds
curl -s http://localhost:8001/health
# Kill server
pkill -f uvicorn
```
**Requirement**: Health endpoint must return 200 status

## 📋 Pre-Deployment Checklist

### Before Any Code Changes:
- [ ] Read current git status: `git status`
- [ ] Check recent commits: `git log --oneline -5`
- [ ] Run existing tests to establish baseline
- [ ] Verify current deployment status

### After Code Changes:
- [ ] Run affected tests
- [ ] Test build processes (frontend/backend)
- [ ] Check for unused variables/imports
- [ ] Verify environment variables are set correctly
- [ ] Test API endpoints if backend changed
- [ ] Validate React components if frontend changed

## 🛠️ Common Deployment Issues & Fixes

### Issue 1: Missing Python Dependencies
**Symptoms**: `ModuleNotFoundError` in backend tests
**Fix**: 
```bash
cd backend && source venv/bin/activate
pip install -r requirements.txt
```

### Issue 2: Frontend Build Failures
**Symptoms**: ESLint errors, compilation failures
**Fix**:
```bash
cd frontend
npm ci --only=production
# Fix unused variables/imports
npm run build
```

### Issue 3: Database Connection Issues
**Symptoms**: SQLAlchemy connection errors
**Fix**:
```bash
cd backend && source venv/bin/activate
python -c "from app.database import init_db; init_db()"
```

### Issue 4: CORS Issues
**Symptoms**: Frontend can't connect to backend
**Check**: 
- `backend/app/main.py` has proper CORS configuration
- Environment variables match between deployments

## 🔄 Deployment Workflow

### For Backend Changes:
1. **Activate Environment**: `cd backend && source venv/bin/activate`
2. **Run Tests**: `python -m pytest tests/ -v --tb=short`
3. **Test Startup**: `uvicorn app.main:app --reload` (should start without errors)
4. **Commit & Push**: Render auto-deploys on push

### For Frontend Changes:
1. **Install Dependencies**: `cd frontend && npm ci`
2. **Build**: `npm run build` (must succeed)
3. **Fix ESLint Issues**: Remove unused variables/imports
4. **Commit & Push**: Vercel auto-deploys on push

### For Full Stack Changes:
1. **Backend First**: Follow backend workflow
2. **Frontend Second**: Follow frontend workflow
3. **Integration Test**: Start both locally and test
4. **Deploy**: Push backend first, then frontend

## 📝 Environment Variables

### Render (Backend)
```
DATABASE_URL=postgresql://... (auto-provided)
ENVIRONMENT=production
FRONTEND_URL=https://wolf-goat-pig.vercel.app
GHIN_API_USER=""
GHIN_API_PASS=""
GHIN_API_STATIC_TOKEN=""
```

### Vercel (Frontend)
```
REACT_APP_API_URL=https://wolf-goat-pig-api.onrender.com
NODE_ENV=production
```

## 🚨 Emergency Rollback

If deployment fails:
1. **Check logs**: 
   - Render: Check build logs in dashboard
   - Vercel: Check deployment logs
2. **Quick fix**: Revert last commit
3. **Redeploy**: Push revert commit

## 🔍 Health Monitoring

### Backend Health Check
- URL: `https://wolf-goat-pig-api.onrender.com/health`
- Expected: `{"status":"healthy",...}`

### Frontend Health Check  
- URL: `https://wolf-goat-pig.vercel.app`
- Expected: React app loads without errors

## 🎯 Agent Success Criteria

For a deployment to be considered successful:

✅ **Backend**: Health endpoint returns 200
✅ **Frontend**: Build completes without errors  
✅ **Integration**: Frontend can reach backend APIs
✅ **Tests**: No new test failures introduced
✅ **Performance**: Apps load within reasonable time

## 📞 Troubleshooting Commands

```bash
# Backend debugging
cd backend && source venv/bin/activate
python -c "import app.main; print('Backend imports OK')"
uvicorn app.main:app --reload --log-level debug

# Frontend debugging  
cd frontend
npm run build 2>&1 | grep -E "(ERROR|FAIL)"
npm start

# Full system test
./deploy.sh test
```

## 🔗 Key Files to Monitor

### Never Break These:
- `backend/app/main.py` - Main FastAPI app
- `backend/app/database.py` - Database configuration  
- `frontend/src/index.js` - React entry point
- `frontend/package.json` - Dependencies
- `render.yaml` - Backend deployment config
- `vercel.json` - Frontend deployment config

### Safe to Modify:
- Component files in `frontend/src/components/`
- API routes in `backend/app/`
- Test files
- Documentation files

---

**Remember**: Test locally first, deploy incrementally, monitor after deployment! 🎯