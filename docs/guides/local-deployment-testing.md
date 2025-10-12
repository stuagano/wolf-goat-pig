# Local Deployment Testing Guide

This guide helps you test your Render (backend) and Vercel (frontend) deployments locally before pushing to production.

## Quick Start

### 1. Test Backend (Render-like)
```bash
./scripts/test-prod-backend.sh
```
This simulates Render's production environment with gunicorn.

### 2. Test Frontend (Vercel-like)
```bash
./scripts/test-prod-frontend.sh
```
This builds and serves the production frontend build.

### 3. Verify Both Deployments
```bash
python scripts/verify-deployments.py
```
This runs comprehensive tests on both services.

## Detailed Testing Options

### Backend Production Testing

The backend test script (`scripts/test-prod-backend.sh`) does the following:
1. Creates a production virtual environment
2. Installs all dependencies including gunicorn
3. Sets production environment variables
4. Runs the backend with gunicorn (like Render does)

**Environment Configuration:**
- Copy `.env.example` to `.env.production`
- Set production values (database URL, API keys, etc.)

**Test with PostgreSQL:**
```bash
# Start PostgreSQL locally
docker run -d \
  --name wgp-postgres \
  -e POSTGRES_PASSWORD=testpass \
  -e POSTGRES_DB=wgp_prod \
  -p 5432:5432 \
  postgres:15

# Set in .env.production
DATABASE_URL=postgresql://postgres:testpass@localhost/wgp_prod

# Run the test
./scripts/test-prod-backend.sh
```

### Frontend Production Testing

The frontend test script (`scripts/test-prod-frontend.sh`) performs:
1. Clean install of dependencies (`npm ci`)
2. Production build with optimizations
3. Build size and content analysis
4. Serves the build with a static server (like Vercel)

**Environment Configuration:**
- Create `frontend/.env.production`
- Set `REACT_APP_API_URL` to your backend URL

**Common Issues to Check:**
- Missing environment variables
- Build size too large (>10MB)
- API URL not configured correctly
- Missing static assets

### Full Stack Docker Testing

For the most accurate production simulation:

```bash
# Start everything with Docker Compose
docker-compose -f docker-compose.prod.yml up --build

# Services will be available at:
# - Backend: http://localhost:8000
# - Frontend: http://localhost:3000
# - PostgreSQL: localhost:5432
```

This creates:
- PostgreSQL database (production-like)
- Backend with gunicorn workers
- Frontend with nginx serving
- Proper networking between services

### Deployment Verification

The verification script (`scripts/verify-deployments.py`) tests:

#### Backend Tests
- Health endpoints
- API documentation
- Course data availability
- Game creation
- Monte Carlo simulation

#### Frontend Tests
- Build accessibility
- React app detection
- Backend URL configuration
- Static asset availability

#### Integration Tests
- CORS configuration
- Frontend-backend communication
- API response times

**Usage Examples:**

```bash
# Test local development
python scripts/verify-deployments.py

# Test local production builds
python scripts/verify-deployments.py \
  --backend http://localhost:8000 \
  --frontend http://localhost:3000

# Test actual production (configure URLs first)
python scripts/verify-deployments.py --production
```

## Pre-Deployment Checklist

Before deploying to Render/Vercel, verify:

### Backend (Render)
- [ ] Production environment variables set
- [ ] Database migrations ready
- [ ] Health endpoint responding
- [ ] CORS configured for frontend URL
- [ ] API rate limiting configured
- [ ] Error logging setup
- [ ] Gunicorn workers configured

### Frontend (Vercel)
- [ ] Production build succeeds
- [ ] Build size reasonable (<10MB)
- [ ] Environment variables set
- [ ] API URL correctly configured
- [ ] Static assets optimized
- [ ] Source maps disabled for production
- [ ] Error tracking configured

### Integration
- [ ] Frontend can reach backend API
- [ ] CORS headers properly configured
- [ ] Authentication working (if applicable)
- [ ] WebSocket connections work (if used)

## Troubleshooting

### Backend Issues

**Port already in use:**
```bash
lsof -i :8000
kill -9 <PID>
```

**Database connection fails:**
- Check DATABASE_URL format
- Ensure PostgreSQL is running
- Verify credentials

**Module import errors:**
- Ensure all dependencies in requirements.txt
- Check Python version (3.11.x required)

### Frontend Issues

**Build fails:**
- Check Node version (20.x required)
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall

**API connection fails:**
- Verify REACT_APP_API_URL is set
- Check CORS configuration on backend
- Ensure backend is running

**Large bundle size:**
- Run build analyzer: `npm run build -- --stats`
- Check for unnecessary dependencies
- Enable code splitting

### Docker Issues

**Container won't start:**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend

# Rebuild from scratch
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up
```

## Production URLs

Once verified locally, update these for your actual deployments:

**Render Backend:**
- URL: `https://your-app.onrender.com`
- Set environment variables in Render dashboard
- Enable health checks

**Vercel Frontend:**
- URL: `https://your-app.vercel.app`
- Set environment variables in Vercel dashboard
- Configure custom domain if needed

## Monitoring Deployments

After deployment, monitor:

1. **Render Dashboard:**
   - Service metrics
   - Request logs
   - Error rates
   - Database connections

2. **Vercel Dashboard:**
   - Build status
   - Function logs
   - Analytics
   - Error tracking

3. **Use the verification script:**
   ```bash
   python scripts/verify-deployments.py \
     --backend https://your-app.onrender.com \
     --frontend https://your-app.vercel.app
   ```

## Rollback Procedure

If issues occur after deployment:

**Render:**
1. Go to Render dashboard
2. Select your service
3. Click "Rollback" to previous deploy

**Vercel:**
1. Go to Vercel dashboard
2. Select your project
3. Go to "Deployments"
4. Promote previous working deployment

Always test thoroughly with these local tools before deploying to avoid the need for rollbacks!