# Docker Development Environment

This Docker setup mirrors your Render and Vercel cloud deployments exactly, ensuring local development matches production.

## Quick Start

```bash
# Start all services (matches cloud deployments)
./docker-dev.sh

# Or manually:
docker-compose up --build
```

## What This Provides

### Backend (matches Render)
- Uses `render-startup.py` (same as Render)
- PostgreSQL database connection
- Same environment variables as Render
- Same startup sequence and health checks

### Frontend (matches Vercel)
- Builds with `npm run build` (same as Vercel)
- Serves with nginx (production-ready)
- Same environment variables as Vercel build

### Database
- PostgreSQL 15 (matches Render's PostgreSQL service)
- Persistent data volumes
- Health checks and proper initialization

## Environment Variables

Copy `.env.example` to `.env` and update with your values:

```bash
cp .env.example .env
# Edit .env with your actual values
```

### Required Variables

These variables must be set for the application to work:

- `POSTGRES_PASSWORD` - Database password (default: `wgp_password_change_me` - **CHANGE THIS**)
- `DATABASE_URL` - Auto-generated from POSTGRES_PASSWORD, but can be overridden
- `AUTH0_DOMAIN` - Your Auth0 domain (default provided, but should be updated)
- `AUTH0_CLIENT_ID` - Your Auth0 client ID (default provided, but should be updated)
- `REACT_APP_API_URL` - Backend API URL (default: `http://localhost:8000`)

### Optional Variables

These have sensible defaults but can be customized:

**Backend:**
- `ENVIRONMENT` - `production` or `development` (default: `production`)
- `LOG_LEVEL` - Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`)
- `BACKEND_PORT` - Backend port (default: `8000`)
- `FRONTEND_URL` - Frontend URL for CORS (default: `http://localhost:3000`)
- `BACKEND_URL` - Backend URL (default: `http://localhost:8000`)
- `AUTH0_API_AUDIENCE` - Auth0 API audience (default: `http://localhost:8000`)
- `ENABLE_GHIN_INTEGRATION` - Enable GHIN integration (default: `false`)
- `GHIN_API_USER`, `GHIN_API_PASS`, `GHIN_API_STATIC_TOKEN` - GHIN API credentials
- `ENABLE_EMAIL_NOTIFICATIONS` - Enable email notifications (default: `false`)
- `WEB_CONCURRENCY` - Number of worker processes (default: `1`)
- `POSTGRES_PORT` - PostgreSQL port (default: `5432`)

**Frontend:**
- `FRONTEND_PORT` - Frontend port (default: `3000`)
- `REACT_APP_AUTH0_DOMAIN` - Auth0 domain for frontend (default provided)
- `REACT_APP_AUTH0_CLIENT_ID` - Auth0 client ID for frontend (default provided)
- `REACT_APP_AUTH0_AUDIENCE` - Auth0 audience for frontend (default: `http://localhost:8000`)
- `REACT_APP_USE_MOCK_AUTH` - Use mock authentication (default: `false`)
- `REACT_APP_ENABLE_ANALYTICS` - Enable analytics (default: `true`)
- `REACT_APP_DEPLOY_PLATFORM` - Deployment platform identifier (default: `docker`)

### Environment Variable Validation

The `docker-dev.sh` script will validate critical variables and warn if:
- `POSTGRES_PASSWORD` is not set or using default value
- Database configuration appears incomplete

Always update `POSTGRES_PASSWORD` from the default value for security!

## Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432

## Common Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# Restart a service
docker-compose restart backend

# Access backend shell
docker-compose exec backend bash

# Access database
docker-compose exec postgres psql -U wolf_goat_pig_user -d wolf_goat_pig

# Rebuild after code changes
docker-compose up --build

# Run backend tests in container
docker-compose exec backend pytest

# View container status
docker-compose ps
```

## Development Workflow

### Production Mode (default)
```bash
docker-compose up --build
```
- Uses `render-startup.py` (matches Render deployment)
- No hot reload - requires rebuild for changes
- Production environment variables

### Development Mode (with hot reload)
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

**Important Notes:**
- **Backend**: Source code is mounted and will auto-reload on Python file changes
- **Frontend**: Source is mounted but **requires container rebuild** to see changes
  - To see frontend changes: `docker-compose build frontend && docker-compose up`
  - React build process requires a full rebuild, not hot reload

### Typical Development Workflow

1. **Start services**: `./docker-dev.sh` (production mode) or use dev override
2. **Backend changes**: Edit Python files - changes are reflected automatically in dev mode
3. **Frontend changes**: Rebuild frontend container: `docker-compose build frontend && docker-compose up`
4. **View logs**: `docker-compose logs -f [service]`
5. **Test changes**: Access http://localhost:3000
6. **Stop services**: `docker-compose down`

## Matching Cloud Deployments

### Render Backend
- ✅ Uses `render-startup.py` (same startup script)
- ✅ Same PostgreSQL connection setup
- ✅ Same environment variables
- ✅ Same health check endpoints
- ✅ Same initialization sequence

### Vercel Frontend
- ✅ Builds with `npm run build`
- ✅ Serves static files with nginx
- ✅ Same build-time environment variables
- ✅ Same routing configuration

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Check database connection
docker-compose exec backend python -c "from app.database import SessionLocal; db = SessionLocal(); print('Connected!')"
```

### Frontend build fails
```bash
# Check build logs
docker-compose logs frontend

# Rebuild frontend
docker-compose build --no-cache frontend
```

### Database connection issues
```bash
# Check database is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres pg_isready -U wolf_goat_pig_user
```

### Port already in use
```bash
# Change ports in .env
BACKEND_PORT=8001
FRONTEND_PORT=3001
POSTGRES_PORT=5433
```

## Production-like Testing

This setup allows you to:
- Test the exact same startup sequence as Render
- Verify database migrations work correctly
- Test frontend build process matches Vercel
- Debug issues that only appear in containerized environments
- Ensure environment variable handling matches production

## Differences from Cloud

- **Database**: Local PostgreSQL vs Render's managed PostgreSQL (same version)
- **Networking**: Local Docker network vs Render/Vercel networking
- **Scaling**: Single container vs cloud auto-scaling
- **SSL**: HTTP locally vs HTTPS in cloud (use nginx with SSL for local HTTPS)

