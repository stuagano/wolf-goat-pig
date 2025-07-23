# Wolf Goat Pig Deployment Guide

This guide covers deployment of the Wolf Goat Pig application to various platforms, with a focus on Render.com.

## 🚀 Quick Deployment

### Option 1: Using the automated deployment script
```bash
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
- `render.yaml` - Main Render deployment configuration
- `Procfile` - Heroku-style process definitions
- `runtime.txt` - Python version specification
- `requirements.txt` - Python dependencies

### Validation & Scripts
- `scripts/pre_deploy_check.py` - Pre-deployment validation
- `scripts/deploy.sh` - Automated deployment pipeline

## 🛠️ Troubleshooting

### Common Issues

#### 1. Syntax Errors
**Symptom:** Build fails with Python syntax errors
**Solution:** Run pre-deployment check
```bash
python3 scripts/pre_deploy_check.py
```

#### 2. Database Connection Issues
**Symptom:** "could not translate host name" errors
**Solutions:**
- Check DATABASE_URL environment variable
- Verify database service is running
- Check database credentials

#### 3. Import Errors
**Symptom:** "ModuleNotFoundError" during startup
**Solutions:**
- Verify all dependencies in `requirements.txt`
- Check Python version compatibility
- Ensure proper module structure

#### 4. Frontend Build Failures
**Symptom:** npm build errors
**Solutions:**
- Run `npm ci` instead of `npm install`
- Check package.json dependencies
- Verify Node.js version

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
  "environment": "production"
}
```

#### Frontend Check
```bash
curl https://wolf-goat-pig-frontend.onrender.com/
```

## 🔍 Deployment Validation

### Pre-deployment Checklist
- [ ] All Python files compile without syntax errors
- [ ] All imports resolve correctly
- [ ] Database connections work
- [ ] Frontend builds successfully
- [ ] All tests pass
- [ ] Environment variables are set

### Post-deployment Verification
- [ ] Health check endpoint responds
- [ ] Database is accessible
- [ ] API endpoints work correctly
- [ ] Frontend loads properly
- [ ] CORS is configured correctly

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

### Render Logs
```bash
# View logs via dashboard or CLI
render logs --service wolf-goat-pig-api
```

### Application Logs
The application uses structured logging:
- INFO: Normal operations
- WARNING: Non-critical issues
- ERROR: Critical failures

### Key Metrics to Monitor
- Response time
- Error rate
- Database connection count
- Memory usage
- CPU usage

## 🔐 Security Considerations

### Environment Variables
- `DATABASE_URL` - Database connection string
- `ENVIRONMENT` - Runtime environment (production/development)
- `REACT_APP_API_URL` - Frontend API endpoint

### CORS Configuration
Currently allows all origins for MVP. In production, restrict to:
- Frontend domain
- Development localhost

## 📈 Performance Optimization

### Backend
- Connection pooling enabled
- Health check caching
- Graceful error handling

### Frontend
- Build optimization with React Scripts
- Static asset serving
- CDN-ready configuration

### Database
- Connection pre-ping
- Connection recycling
- Pool size optimization

## 🆘 Emergency Procedures

### Service Down
1. Check Render dashboard for service status
2. Review recent deployments
3. Check health endpoint
4. Review application logs
5. Rollback if necessary

### Database Issues
1. Check database service status
2. Verify DATABASE_URL
3. Test connection manually
4. Check database logs
5. Consider database restart

## 📞 Support

### Useful Links
- [Render Documentation](https://render.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs)

### Getting Help
1. Check application logs first
2. Review this troubleshooting guide
3. Check platform status pages
4. Consult platform documentation
5. Contact platform support if needed