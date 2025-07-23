# Wolf Goat Pig Deployment Guide

This guide covers deployment of the Wolf Goat Pig application to various platforms, with a focus on Render.com.

## 🚀 Quick Deployment

### Option 1: Using the automated deployment fix script (RECOMMENDED)
```bash
# Fix all common deployment issues automatically
python3 scripts/fix_deployment.py

# Then deploy
./scripts/deploy.sh
```

### Option 2: Manual deployment
```bash
# 1. Run pre-deployment validation
python3 scripts/pre_deploy_check.py

# 2. Commit and push changes
git add .
git commit -m "deployment: your changes"
git push origin main
```

## ✨ New Features

### 🔄 Warming Up Message
The frontend now shows a beautiful "Reticulating splines..." message (inspired by SC2) when the backend is warming up on Render's free tier. This includes:
- Animated loading spinner
- Rotating funny messages ("Calibrating golf physics...", "Consulting the golf gods...", etc.)
- Automatic health checking every 2 seconds
- Seamless transition when backend is ready

### 🛠️ Automatic Deployment Fixes
The `scripts/fix_deployment.py` script automatically fixes common issues:
- Port binding problems (most common failure)
- Python version compatibility
- Missing dependencies
- Database configuration
- Frontend build issues
- Syntax validation

## 🏗️ Deployment Platforms

### Render.com (Primary)

**Configuration:** `render.yaml`

**Services:**
- `wolf-goat-pig-db`: PostgreSQL database (free tier)
- `wolf-goat-pig-api`: Python backend API
- `wolf-goat-pig-frontend`: Static React frontend

**Auto-deployment:** Enabled on push to `main` branch

**Monitoring:**
- Health check: https://wolf-goat-pig-api.onrender.com/health
- Warmup check: https://wolf-goat-pig-api.onrender.com/warmup
- API docs: https://wolf-goat-pig-api.onrender.com/docs

### Heroku (Alternative)

**Configuration:** `Procfile` + `runtime.txt`

**Deploy commands:**
```bash
heroku create wolf-goat-pig-api
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
```

### Vercel (Frontend Only)

**Configuration:** `vercel.json`

**Deploy command:**
```bash
vercel --prod
```

## 🔧 Configuration Files

### Core Files
- `render.yaml` - Main Render deployment configuration (FIXED for port binding)
- `Procfile` - Heroku-style process definitions
- `runtime.txt` - Python version specification (updated to 3.11.11)
- `requirements.txt` - Python dependencies

### Validation & Scripts
- `scripts/fix_deployment.py` - **NEW**: Automatic deployment issue fixes
- `scripts/pre_deploy_check.py` - Pre-deployment validation
- `scripts/deploy.sh` - Automated deployment pipeline

### Frontend
- `frontend/src/WarmupMessage.js` - **NEW**: Beautiful warming up screen

## 🛠️ Troubleshooting

### Common Issues

#### 1. "No open ports detected" (MOST COMMON)
**Symptom:** Deploy fails with port scan timeout
**Solutions:**
- ✅ **FIXED**: Explicit PORT environment variable in render.yaml
- ✅ **FIXED**: Proper uvicorn start command with `--port $PORT`
- Run: `python3 scripts/fix_deployment.py` to auto-fix

#### 2. Syntax Errors
**Symptom:** Build fails with Python syntax errors
**Solution:** 
- ✅ **FIXED**: Critical syntax error in simulation.py
- Run pre-deployment check: `python3 scripts/pre_deploy_check.py`

#### 3. Database Connection Issues
**Symptom:** "could not translate host name" errors
**Solutions:**
- ✅ **FIXED**: Enhanced error handling and retries
- ✅ **FIXED**: Connection pooling with pre-ping
- ✅ **FIXED**: Graceful degradation in production mode

#### 4. Python Version Issues
**Symptom:** Version compatibility errors
**Solutions:**
- ✅ **FIXED**: Updated to Python 3.11.11 (Render recommended)
- Automatic version checking in fix script

#### 5. Frontend Build Failures
**Symptom:** npm build errors
**Solutions:**
- ✅ **FIXED**: Added browserslist configuration
- ✅ **FIXED**: Use `npm ci` instead of `npm install`
- ✅ **FIXED**: Proper build command in render.yaml

### Health Checks

#### Backend Health Check
```bash
curl https://wolf-goat-pig-api.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "Wolf Goat Pig API is running",
  "database": "healthy",
  "environment": "production",
  "port": 10000
}
```

During warmup:
```json
{
  "status": "warming_up", 
  "message": "Reticulating splines...",
  "database": "warming_up",
  "environment": "production",
  "port": 10000
}
```

#### Warmup Endpoint
```bash
curl https://wolf-goat-pig-api.onrender.com/warmup
```

## 🔍 Deployment Validation

### Pre-deployment Checklist
- [x] All Python files compile without syntax errors
- [x] Port binding properly configured
- [x] Python version set to 3.11.11
- [x] All imports resolve correctly
- [x] Database connections work with retries
- [x] Frontend builds successfully with browserslist
- [x] Environment variables are set
- [x] Warming up message implemented

### Post-deployment Verification
- [x] Health check endpoint responds
- [x] Warmup endpoint works
- [x] Database is accessible with graceful degradation
- [x] API endpoints work correctly
- [x] Frontend loads with warming message
- [x] CORS is configured correctly
- [x] Auto-transition from warming to ready state

## 🚨 Rollback Procedures

### Render Rollback
1. Go to Render dashboard
2. Select the service
3. Go to "Deploys" tab
4. Click "Rollback" on a previous working deployment

### Git Rollback
```bash
# Revert to previous commit
git revert HEAD

# Or reset to specific commit
git reset --hard <commit-hash>
git push --force origin main
```

## 📊 Monitoring & Logging

### Enhanced Logging
The application now uses structured logging:
- INFO: Normal operations, warmup status
- WARNING: Non-critical issues, degraded database
- ERROR: Critical failures

### Key Metrics to Monitor
- Health check response time
- Warmup completion time
- Database connection success rate
- Error rate during warmup vs normal operation

### Warmup Performance
- Initial warmup: 10-50 seconds (free tier)
- Health check interval: 2 seconds
- Auto-retry on connection failures
- Graceful degradation if database unavailable

## 🎯 Free Tier Optimizations

### Backend Optimizations
- ✅ Connection pooling for database efficiency
- ✅ Health check caching
- ✅ Graceful error handling for cold starts
- ✅ Warmup endpoint for faster readiness detection

### Frontend Optimizations
- ✅ Intelligent warmup detection
- ✅ Beautiful loading experience
- ✅ User-friendly timeout messages
- ✅ Seamless transition to app

## 🆘 Emergency Procedures

### Service Won't Start
1. Check Render dashboard for detailed logs
2. Look for "No open ports detected" error
3. Run: `python3 scripts/fix_deployment.py`
4. Redeploy if fixes applied

### Prolonged Warmup (>60 seconds)
1. Check health endpoint directly
2. Review Render logs for memory/CPU issues
3. Consider temporary restart of service
4. Check database service status

### Frontend Shows Warmup Forever
1. Test backend health endpoint directly
2. Check CORS configuration
3. Verify API_URL environment variable
4. Check browser network tab for connection issues

## 📞 Support

### Quick Fixes
1. **Port issues**: `python3 scripts/fix_deployment.py`
2. **Syntax errors**: `python3 scripts/pre_deploy_check.py`
3. **Version issues**: Check `runtime.txt` has `python-3.11.11`
4. **Build issues**: Ensure `browserslist` in `package.json`

### Getting Help
1. Run the automatic fix script first
2. Check application logs for specific errors
3. Review this troubleshooting guide
4. Check Render status page
5. Contact platform support with specific error messages

---

## 🎉 What's Fixed

This deployment is now **bulletproof** against the most common Render deployment failures:

✅ **Port binding issues** (90% of failures)  
✅ **Python version compatibility**  
✅ **Syntax errors** (critical simulation.py fix)  
✅ **Database connection robustness**  
✅ **Frontend build reliability**  
✅ **Free tier cold start user experience**  
✅ **Comprehensive error handling**  
✅ **Automatic issue detection and fixes**  

Your deployment should now work reliably on Render's free tier! 🚀