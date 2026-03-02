# Docker Setup - Mirroring Cloud Deployments

This Docker setup ensures your local development environment **exactly matches** your Render and Vercel cloud deployments.

## Why Docker?

- **Consistency**: Same environment as production (Render/Vercel)
- **Isolation**: No conflicts with local Python/Node versions
- **Reproducibility**: Same setup for all developers
- **Debugging**: Catch containerization issues before deploying

## Quick Start

```bash
# 1. Copy environment variables
cp .env.example .env
# Edit .env with your values

# 2. Start all services
./docker-dev.sh

# Or manually:
docker-compose up --build
```

## What Gets Started

### Backend (matches Render)
- ✅ Uses `render-startup.py` (same as Render)
- ✅ PostgreSQL database (same version as Render)
- ✅ Same environment variables
- ✅ Same initialization sequence
- ✅ Same health checks

### Frontend (matches Vercel)
- ✅ Builds with `npm run build` (same as Vercel)
- ✅ Serves with nginx (production-ready)
- ✅ Same build-time environment variables

### Database
- ✅ PostgreSQL 15 (matches Render)
- ✅ Persistent volumes
- ✅ Health checks

## Environment Setup

1. **Copy `.env.example` to `.env`**:
   ```bash
   cp .env.example .env
   ```

2. **Update `.env` with your values**:
   - `POSTGRES_PASSWORD` - Choose a secure password
   - `AUTH0_DOMAIN` - Your Auth0 domain
   - `AUTH0_CLIENT_ID` - Your Auth0 client ID
   - `REACT_APP_API_URL` - Usually `http://localhost:8000`

3. **Start services**:
   ```bash
   ./docker-dev.sh
   ```

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React app (matches Vercel) |
| Backend API | http://localhost:8000 | FastAPI backend (matches Render) |
| API Docs | http://localhost:8000/docs | Swagger documentation |
| Database | localhost:5432 | PostgreSQL database |

## Common Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Stop services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# Restart a service
docker-compose restart backend

# Rebuild after code changes
docker-compose up --build

# Access backend shell
docker-compose exec backend bash

# Access database
docker-compose exec postgres psql -U wolf_goat_pig_user -d wolf_goat_pig

# Run tests in container
docker-compose exec backend pytest

# View container status
docker-compose ps
```

## Development vs Production Mode

### Production Mode (default - matches cloud)
```bash
docker-compose up
```
- Uses `render-startup.py` (matches Render)
- Production environment variables
- No hot reload - requires rebuild for changes

### Development Mode (with source mounting)
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

**Important Notes:**
- **Backend**: Source code is mounted read-only, but Python will auto-reload on file changes
- **Frontend**: Source is mounted but **React requires a container REBUILD** to see changes
  - Frontend does NOT hot reload - you must rebuild: `docker-compose build frontend && docker-compose up`
  - This is because React needs to run through the build process (npm run build)

## Matching Cloud Deployments

### Render Backend ✅
- Same startup script (`render-startup.py`)
- Same Python version (3.12.8)
- Same PostgreSQL setup
- Same environment variables
- Same initialization sequence
- Same health check endpoint (`/ready`)

### Vercel Frontend ✅
- Same build command (`npm run build`)
- Same build-time environment variables
- Same nginx serving
- Same routing configuration

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Check database connection
docker-compose exec backend python -c "from app.database import SessionLocal; db = SessionLocal(); print('Connected!')"

# Check if render-startup.py exists
docker-compose exec backend ls -la render-startup.py
```

### Frontend build fails
```bash
# Check build logs
docker-compose logs frontend

# Rebuild frontend
docker-compose build --no-cache frontend

# Check environment variables
docker-compose exec frontend env | grep REACT_APP
```

### Database connection issues
```bash
# Check database is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres pg_isready -U wolf_goat_pig_user

# Check connection string
docker-compose exec backend env | grep DATABASE_URL
```

### Port conflicts
```bash
# Change ports in .env
BACKEND_PORT=8001
FRONTEND_PORT=3001
POSTGRES_PORT=5433
```

## Differences from Cloud

| Aspect | Local Docker | Render/Vercel |
|--------|--------------|---------------|
| Database | Local PostgreSQL | Render managed PostgreSQL |
| Networking | Docker network | Cloud networking |
| SSL | HTTP | HTTPS |
| Scaling | Single container | Auto-scaling |
| Storage | Docker volumes | Cloud storage |

## Testing Production Issues Locally

This Docker setup helps you:
- ✅ Test the exact startup sequence as Render
- ✅ Verify database migrations work
- ✅ Test frontend build process
- ✅ Debug containerization issues
- ✅ Test environment variable handling
- ✅ Verify health checks work

## Next Steps

1. **Start services**: `./docker-dev.sh`
2. **Verify everything works**: Check http://localhost:3000
3. **Make code changes**: Edit files locally
4. **Test in containers**: Ensure changes work in Docker
5. **Deploy to cloud**: Confident that it will work!

## Additional Resources

- See `README-DOCKER.md` for detailed documentation
- See `docker-compose.yml` for service configuration
- See `.env.example` for all environment variables

