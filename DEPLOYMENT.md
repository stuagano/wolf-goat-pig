# Deployment Guide

This document provides instructions for deploying the Wolf-Goat-Pig application to Vercel (frontend) and Render (backend).

## Overview

- **Frontend**: React app deployed to Vercel
- **Backend**: FastAPI app deployed to Render
- **Database**: PostgreSQL hosted on Render

## Prerequisites

1. A Vercel account (https://vercel.com)
2. A Render account (https://render.com)
3. Git repository connected to both platforms

## Deployment Configuration

### Vercel (Frontend)

The frontend is configured for deployment via:
- `vercel.json` (root-level configuration)
- `frontend/vercel.json` (frontend-specific configuration)

#### Environment Variables

Set these in the Vercel dashboard:

```
REACT_APP_API_URL=https://wolf-goat-pig.onrender.com
REACT_APP_AUTH0_DOMAIN=dev-jm88n088hpt7oe48.us.auth0.com
REACT_APP_AUTH0_CLIENT_ID=qAZuRv5E9mPQ9uTGg7NWpkpfVj8bCeoB
REACT_APP_AUTH0_AUDIENCE=https://api.wolf-goat-pig.com
REACT_APP_USE_MOCK_AUTH=false
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_DEPLOY_PLATFORM=vercel
```

#### Build Configuration

- **Build Command**: Automatically detected from `vercel.json` (`cd frontend && npm ci && npm run build`)
- **Output Directory**: `frontend/build`
- **Install Command**: `cd frontend && npm ci`

### Render (Backend)

The backend is configured via `render.yaml` in the root directory.

#### Services

1. **Database** (`wolf-goat-pig-db`):
   - Type: PostgreSQL
   - Plan: Free
   - Region: Oregon

2. **API** (`wolf-goat-pig-api`):
   - Type: Web Service
   - Runtime: Python 3.12.8
   - Plan: Free
   - Region: Oregon
   - Root Directory: `backend`

#### Environment Variables

These are configured in `render.yaml` but can be overridden in the Render dashboard:

```
DATABASE_URL=<automatically provided by Render>
PYTHON_VERSION=3.12.8
ENVIRONMENT=production
FRONTEND_URL=https://wolf-goat-pig.vercel.app
BACKEND_URL=https://wolf-goat-pig.onrender.com
ENABLE_GHIN_INTEGRATION=false
AUTH0_DOMAIN=dev-jm88n088hpt7oe48.us.auth0.com
AUTH0_API_AUDIENCE=https://wolf-goat-pig.onrender.com
AUTH0_CLIENT_ID=qAZuRv5E9mPQ9uTGg7NWpkpfVj8bCeoB
```

## Deployment Process

### Initial Setup

1. **Connect Repository**:
   - Vercel: Connect your GitHub repository and select the `frontend` directory as root
   - Render: Connect your GitHub repository using the `render.yaml` blueprint

2. **Configure Environment Variables**:
   - Set all required environment variables in each platform's dashboard
   - Ensure URLs match between frontend and backend configurations

3. **Deploy**:
   - Both platforms will auto-deploy on push to the main branch
   - Monitor deployment logs for any errors

### Vercel Deployment

```bash
# Deploy from command line (optional)
cd frontend
npm install -g vercel
vercel --prod
```

### Render Deployment

Render deploys automatically based on `render.yaml`. To manually trigger:

1. Go to the Render dashboard
2. Select the `wolf-goat-pig-api` service
3. Click "Manual Deploy" → "Deploy latest commit"

## Common Issues and Solutions

### Vercel Issues

#### Issue: Build fails with "Module not found"
**Solution**: Ensure all dependencies are in `frontend/package.json` and run `npm install` locally first to verify

#### Issue: Environment variables not available
**Solution**: Check that all `REACT_APP_*` variables are set in Vercel dashboard under Settings → Environment Variables

#### Issue: Routes return 404
**Solution**: Verify the `rewrites` configuration in `vercel.json` is correct:
```json
"rewrites": [
  {
    "source": "/(.*)",
    "destination": "/index.html"
  }
]
```

### Render Issues

#### Issue: Build fails with Python version error
**Solution**: Verify these files have matching Python versions:
- `backend/runtime.txt`: `python-3.12.8`
- `backend/.python-version`: `3.12.8`
- `render.yaml` envVar `PYTHON_VERSION`: `3.12.8`

#### Issue: Health check fails
**Solution**:
1. Check logs for database connection errors
2. Verify `DATABASE_URL` environment variable is set correctly
3. The health endpoint `/health` should be accessible and return proper status

#### Issue: Database connection fails
**Solution**:
1. Ensure the database service is created before the web service
2. Verify `DATABASE_URL` is being injected from the database service
3. Check that database migrations have run successfully

#### Issue: "Application failed to respond to health check"
**Solution**:
1. Increase health check timeout in Render dashboard
2. Check that the app is binding to `0.0.0.0` not `localhost`
3. Verify `$PORT` environment variable is being used
4. Check logs for startup errors

### Database Issues

#### Issue: Tables not created
**Solution**: The app automatically creates tables on startup via `database.init_db()`. Check logs for migration errors.

#### Issue: Seed data missing
**Solution**: The app seeds data on startup. If seeding fails, it continues with fallback data. Check logs for seeding errors.

## Health Checks

### Backend Health Endpoint

- **URL**: `https://wolf-goat-pig.onrender.com/health`
- **Components Checked**:
  - Database connectivity
  - Course data availability
  - Rules data availability
  - GHIN integration (if enabled)

### Expected Response

```json
{
  "status": "healthy",
  "timestamp": "2025-10-31T...",
  "environment": "production",
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful"
    },
    "courses": {
      "status": "healthy",
      "message": "X courses available",
      "courses": ["..."]
    }
  }
}
```

## Monitoring

### Vercel

- View deployment logs in the Vercel dashboard
- Check real-time logs for runtime errors
- Monitor performance in the Analytics tab

### Render

- View deployment and runtime logs in the Render dashboard
- Monitor service health and uptime
- Check database metrics and connection pools

## Rollback

### Vercel

1. Go to Deployments tab
2. Find the last working deployment
3. Click "..." → "Promote to Production"

### Render

1. Go to the service dashboard
2. Click "Rollback" to deploy a previous version
3. Or manually deploy a specific commit from the "Manual Deploy" menu

## Updating Dependencies

### Frontend

```bash
cd frontend
npm update
npm audit fix
git commit -am "chore: update frontend dependencies"
git push
```

### Backend

```bash
cd backend
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
git commit -am "chore: update backend dependencies"
git push
```

## Support

For deployment issues:
1. Check the logs in Vercel/Render dashboards
2. Review this deployment guide
3. Check the health endpoints
4. Review the main README.md for application-specific issues

## Security Notes

- Never commit secrets or API keys to the repository
- Use environment variables for all sensitive configuration
- Rotate Auth0 credentials if they are exposed
- Keep dependencies updated for security patches
- Monitor deployment logs for suspicious activity
