# Skill: Deploy to Staging

## Description
Deploys the Wolf Goat Pig application to staging environment (Render for backend, Vercel for frontend) with proper validation.

## Usage
Invoke this skill when you want to deploy changes to staging for testing before production deployment.

## Prerequisites
- Git repository is clean (all changes committed)
- All tests passing
- Render account configured
- Vercel account configured
- Environment variables set

## Steps

### 1. Pre-deployment Validation

```bash
# Ensure we're on the right branch
git checkout develop  # or your staging branch

# Pull latest changes
git pull origin develop

# Run all tests
cd backend && pytest -v
cd ../frontend && npm test -- --watchAll=false

# Run code quality checks
cd ../backend && ruff check .
cd ../frontend && npm run lint

echo "Pre-deployment validation complete!"
```

### 2. Deploy Backend to Render

```bash
# Option A: Trigger via deploy hook
curl -X POST "$RENDER_DEPLOY_HOOK_STAGING"

# Option B: Push to Render git remote
git remote add render-staging <render-git-url>
git push render-staging develop:main

echo "Backend deployment initiated..."
```

### 3. Wait for Backend Deployment

```bash
# Wait for deployment to complete (typically 2-3 minutes)
echo "Waiting for backend deployment..."
sleep 120

# Check health endpoint
BACKEND_URL="https://your-staging-backend.onrender.com"
response=$(curl -s -o /dev/null -w "%{http_code}" $BACKEND_URL/health)

if [ $response -eq 200 ]; then
  echo "✅ Backend health check passed"
else
  echo "❌ Backend health check failed with status $response"
  exit 1
fi
```

### 4. Deploy Frontend to Vercel

```bash
cd frontend

# Install Vercel CLI if needed
npm install -g vercel

# Deploy to staging
vercel deploy --token=$VERCEL_TOKEN

# Get deployment URL
DEPLOY_URL=$(vercel ls --token=$VERCEL_TOKEN | grep -m1 'https://')
echo "Frontend deployed to: $DEPLOY_URL"
```

### 5. Run Smoke Tests

```bash
# Test critical endpoints
echo "Running smoke tests..."

# Backend
curl -f $BACKEND_URL/health || exit 1
curl -f $BACKEND_URL/healthz || exit 1
curl -f $BACKEND_URL/api/courses || exit 1

# Frontend
curl -f $DEPLOY_URL || exit 1

echo "✅ Smoke tests passed"
```

### 6. Run E2E Tests Against Staging

```bash
cd tests/e2e

# Set staging URLs
export BACKEND_URL="https://your-staging-backend.onrender.com"
export FRONTEND_URL=$DEPLOY_URL

# Run critical E2E tests
npx playwright test smoke.spec.js

echo "✅ E2E tests passed on staging"
```

### 7. Database Migrations (if needed)

```bash
# Connect to staging database
# Render provides a shell for running migrations

# Option A: Via Render shell
# Go to Render dashboard > Shell > Run:
# cd /opt/render/project/src/backend
# alembic upgrade head

# Option B: Via remote connection
export DATABASE_URL="postgresql://user:pass@render-host/db"
cd backend
alembic upgrade head

echo "✅ Database migrations applied"
```

### 8. Verify Deployment

```bash
echo "=== DEPLOYMENT SUMMARY ==="
echo ""
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $DEPLOY_URL"
echo ""
echo "Health checks:"
curl -s $BACKEND_URL/health | jq .
echo ""
echo "Deployment completed successfully!"
```

## Post-Deployment Checklist

- [ ] Backend health check returns 200
- [ ] Frontend loads without errors
- [ ] Database migrations applied
- [ ] Critical API endpoints working
- [ ] Smoke tests passed
- [ ] E2E tests passed
- [ ] No errors in Render logs
- [ ] No errors in Vercel logs

## Rollback Procedure

If deployment fails:

```bash
# Rollback backend (redeploy previous commit)
PREVIOUS_COMMIT=$(git rev-parse HEAD~1)
git checkout $PREVIOUS_COMMIT
git push -f render-staging main

# Rollback frontend
vercel rollback <previous-deployment-url> --token=$VERCEL_TOKEN

echo "Rollback completed"
```

## Environment Variables

Ensure these are set in Render and Vercel:

**Backend (Render)**:
```
DATABASE_URL=<postgresql-url>
SECRET_KEY=<app-secret>
GHIN_API_KEY=<ghin-key>
EMAIL_SERVICE_KEY=<email-key>
ENVIRONMENT=staging
```

**Frontend (Vercel)**:
```
REACT_APP_API_URL=https://your-staging-backend.onrender.com
REACT_APP_AUTH0_DOMAIN=<auth0-domain>
REACT_APP_AUTH0_CLIENT_ID=<auth0-client-id>
REACT_APP_ENVIRONMENT=staging
```

## Monitoring

After deployment, monitor:

```bash
# Render logs
# Visit: https://dashboard.render.com/web/<service-id>/logs

# Vercel logs
vercel logs <deployment-url> --token=$VERCEL_TOKEN

# Or via dashboard:
# Visit: https://vercel.com/<team>/<project>/deployments
```

## Success Indicators
- ✅ Backend deployed and healthy
- ✅ Frontend deployed and accessible
- ✅ All smoke tests passing
- ✅ No errors in deployment logs
- ✅ Database migrations successful
- ✅ E2E tests passing on staging
