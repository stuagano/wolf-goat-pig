# Wolf Goat Pig Deployment Checklist

## Pre-Deployment Verification

### Backend Checks
- [ ] **Environment Variables**: Ensure `NODE_ENV=production` is set
- [ ] **Database Connection**: Verify `DATABASE_URL` is properly configured
- [ ] **Dependencies**: Run `pip install -r requirements.txt` without errors
- [ ] **Import Test**: Test `python -c "from app.main import app; print('OK')"`
- [ ] **Health Check**: Ensure `/health` endpoint responds correctly
- [ ] **CORS Configuration**: Verify frontend URL is in allowed origins

### Frontend Checks  
- [ ] **Environment Variables**: Verify `REACT_APP_API_URL` points to backend
- [ ] **Build Test**: Run `npm run build` successfully
- [ ] **Dependencies**: Run `npm ci` without errors
- [ ] **API Connection**: Test API calls work with backend URL

### Deployment Configuration
- [ ] **render.yaml**: Valid YAML syntax and correct service definitions
- [ ] **Startup Scripts**: Ensure `backend/start.sh` is executable
- [ ] **Health Checks**: Configure proper health check endpoints
- [ ] **Database**: PostgreSQL service configured correctly

## Quick Test Commands

### Backend Test
```bash
cd backend
python -c "from app.main import app; print('Backend imports successfully')"
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
curl http://localhost:8000/health
```

### Frontend Test
```bash
cd frontend
npm ci
npm run build
```

## Common Issues & Solutions

### Issue: SQLAlchemy Import Error
**Solution**: Use SQLAlchemy==2.0.25 (compatible with Python 3.13)

### Issue: CORS Errors in Production
**Solution**: Update CORS allowed_origins in `backend/app/main.py`

### Issue: Frontend Can't Connect to Backend
**Solution**: Check `REACT_APP_API_URL` in `.env.production`

### Issue: Database Connection Failed
**Solution**: Verify `DATABASE_URL` environment variable

## Rollback Plan
If deployment fails:
1. Revert to previous commit: `git revert HEAD`
2. Check this checklist
3. Fix issues and re-deploy

## Post-Deployment Verification
- [ ] Backend health check: `https://wgp-backend.onrender.com/health`
- [ ] Frontend loads: `https://wgp-frontend.onrender.com`
- [ ] API calls work from frontend
- [ ] Database operations function correctly