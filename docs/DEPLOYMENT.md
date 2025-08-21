# Wolf Goat Pig Deployment Guide

This guide covers deploying the Wolf Goat Pig application to Render (backend) and Vercel (frontend), including automated deployment bots and validation.

## Environment Variables

### Local Development
For local development, the frontend uses the proxy configuration in `package.json`:
```json
"proxy": "http://localhost:8000"
```

This means `API_URL` will be empty and requests will be proxied to `http://localhost:8000`.

### Production Deployment (Vercel)

For production deployment on Vercel, you need to set the following environment variable:

1. Go to your Vercel project dashboard
2. Navigate to Settings → Environment Variables
3. Add the following environment variable:
   - **Name**: `REACT_APP_API_URL`
   - **Value**: `https://wolf-goat-pig.onrender.com`
   - **Environment**: Production, Preview, Development

### Environment Variable Configuration

The frontend uses `API_URL = process.env.REACT_APP_API_URL || ""` for all API calls.

- **Local Development**: `API_URL` is empty, uses proxy
- **Production**: `API_URL` points to Render backend

## CORS Configuration

The backend has been configured to allow all origins without CORS restrictions. No additional CORS configuration is needed on the frontend.

## Deployment Steps

1. **Set Environment Variables** in Vercel dashboard
2. **Deploy** - Vercel will automatically build and deploy when you push to GitHub
3. **Verify** - Check that the frontend can communicate with the backend

## 🚀 Render (Backend) Deployment

### Configuration
The backend is configured using `config/render.yaml`:
- **Database**: PostgreSQL (free tier)
- **API Service**: Python with FastAPI
- **Health Check**: `/health` endpoint
- **Environment**: Production with proper variables

### Required Environment Variables
Set these in your Render dashboard:
- `DATABASE_URL`: Automatically provided by Render PostgreSQL service
- `ENVIRONMENT`: `production`
- `FRONTEND_URL`: `https://wolf-goat-pig.vercel.app`
- `GHIN_API_USER`: (Optional) Your GHIN email
- `GHIN_API_PASS`: (Optional) Your GHIN password  
- `GHIN_API_STATIC_TOKEN`: (Optional) Static token

### Deployment Process
1. Connect your GitHub repository to Render
2. Create services using the `render.yaml` configuration
3. Environment variables will be set automatically
4. Render will build and deploy automatically on git push

## 🔗 Vercel (Frontend) Deployment

### Configuration
The frontend is configured using `config/vercel.json`:
- **Build**: React app with optimized production build
- **Static Files**: Proper caching headers
- **Security**: Security headers configured
- **Routing**: SPA routing with fallback to index.html

### Required Environment Variables
Set these in your Vercel dashboard:
- `REACT_APP_API_URL`: `https://wolf-goat-pig-api.onrender.com`
- `NODE_ENV`: `production`

### Deployment Process
1. Connect your GitHub repository to Vercel
2. Import project and configure environment variables
3. Vercel will deploy automatically on git push

## 🤖 Deployment Bots & Validation

### GitHub Actions Workflow
Automated deployment validation runs via `.github/workflows/deployment-validation.yml`:
- **Triggers**: Push to main, PRs, daily schedule
- **Validation**: Tests both Render and Vercel deployments
- **Health Checks**: Verifies all endpoints and functionality
- **Notifications**: Reports status in PR comments and job summaries

### Manual Validation
Run deployment validation manually:
```bash
# Validate both deployments
python scripts/deployment/validate_deployments.py

# Custom URLs
python scripts/deployment/validate_deployments.py \
  --backend "https://your-backend.onrender.com" \
  --frontend "https://your-frontend.vercel.app"

# JSON output
python scripts/deployment/validate_deployments.py --output json
```

### Validation Checks
**Backend (Render):**
- ✅ Health endpoint (`/health`)
- ✅ API documentation (`/docs`)
- ✅ CORS configuration
- ✅ Database connectivity
- ✅ Component health status

**Frontend (Vercel):**
- ✅ Main page loads
- ✅ Static assets accessible
- ✅ Security headers configured
- ✅ React app initialization

**Integration:**
- ✅ Frontend-backend connectivity
- ✅ API endpoint accessibility
- ✅ Environment configuration

## 🔧 Configuration Files

### `config/render.yaml`
```yaml
services:
  - type: pserv
    name: wolf-goat-pig-db
    env: postgresql
    
  - type: web
    name: wolf-goat-pig-api
    env: python
    startCommand: |
      cd backend && python -c "from app.database import init_db; init_db()" && 
      uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
    healthCheckPath: /health
```

### `config/vercel.json`
```json
{
  "builds": [{
    "src": "frontend/package.json",
    "use": "@vercel/static-build",
    "config": {
      "distDir": "build",
      "buildCommand": "cd frontend && npm ci --only=production && npm run build"
    }
  }],
  "env": {
    "REACT_APP_API_URL": "https://wolf-goat-pig-api.onrender.com"
  }
}
```

## 📊 Monitoring & Status

### Health Endpoints
- **Backend Health**: `https://wolf-goat-pig-api.onrender.com/health`
- **Frontend Status**: `https://wolf-goat-pig.vercel.app`

### GitHub Actions Status
Check deployment validation status in:
- Repository Actions tab
- PR comments (for automated validation)
- Job summaries with detailed results

### Render Dashboard
Monitor backend deployment:
- Build logs and status
- Performance metrics
- Database health
- Environment variables

### Vercel Dashboard  
Monitor frontend deployment:
- Build status and logs
- Analytics and performance
- Domain configuration
- Environment variables

## 🚨 Troubleshooting

### Backend Issues
**Health Check Failures:**
1. Check Render logs for startup errors
2. Verify database connection string
3. Ensure all required environment variables are set
4. Check Python dependencies in `requirements.txt`

**Import/Module Errors:**
1. Verify the `startCommand` in `render.yaml`
2. Check Python path configuration
3. Ensure all app modules are properly structured

### Frontend Issues  
**Build Failures:**
1. Check Node.js version compatibility
2. Verify all dependencies in `package.json`
3. Check build command in `vercel.json`

**API Connection Issues:**
1. Verify `REACT_APP_API_URL` environment variable
2. Check CORS configuration on backend
3. Ensure backend is accessible from frontend

### CORS Errors
1. Verify the `REACT_APP_API_URL` environment variable is set correctly in Vercel
2. Check that the backend is running on Render
3. Ensure the backend URL is accessible
4. Check backend CORS middleware configuration

### Deployment Bot Issues
**GitHub Actions Failures:**
1. Check workflow permissions
2. Verify script dependencies
3. Review validation script logs
4. Check deployment URLs are accessible

**Validation Script Issues:**
1. Install required dependencies: `pip install requests`
2. Check network connectivity to deployment URLs
3. Verify URL formats are correct 