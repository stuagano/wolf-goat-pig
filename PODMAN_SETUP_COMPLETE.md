# Podman Setup Complete! 🎉

Your local production-like environment is now fully operational.

## Summary of Changes

### 1. Podman Machine Configuration
- **Upgraded from**: 20GB disk, 4GB RAM
- **Upgraded to**: 60GB disk, 8GB RAM, 5 CPUs
- This provides plenty of space for building and running containers

### 2. Files Created

#### Configuration Files
- **`.env.local`** - Environment variables for local testing
- **`podman-test.sh`** - Control script for managing services
- **`PODMAN_QUICK_START.md`** - Quick reference guide
- **`docs/PODMAN_TESTING_GUIDE.md`** - Comprehensive guide

#### Fixed Issues
- **`frontend/Dockerfile.prod`** - Fixed npm install issues with husky
- **`docker-compose.prod.yml`** - Reduced workers from 2 to 1 to avoid database race condition

## Current Status

### ✅ All Services Running

```
CONTAINER                STATUS
-----------              ------
postgres                 Healthy
backend (API)            Running
frontend (nginx)         Healthy
```

### Health Check Results

**Backend API** (http://localhost:8000):
- Status: Healthy
- Environment: production
- Database: Connected
- Courses: 3 available
- Rules: 50 loaded
- AI Players: 6 available
- Simulation: Operational

**Frontend** (http://localhost:3000):
- Status: Healthy
- Serving React production build

## Access Your Application

### Frontend
```bash
open http://localhost:3000
```

### Backend API
```bash
# Health check
curl http://localhost:8000/health

# API Documentation
open http://localhost:8000/docs

# API endpoints
curl http://localhost:8000/api/courses
curl http://localhost:8000/api/players
curl http://localhost:8000/api/games
```

### Database
```bash
# Connect to PostgreSQL
podman exec -it wolf-goat-pig_postgres_1 psql -U wgp_user -d wolf_goat_pig

# Example queries
SELECT * FROM courses;
SELECT * FROM players;
SELECT * FROM rules;
```

## Common Commands

```bash
# Start services
./podman-test.sh start

# Stop services
./podman-test.sh stop

# View logs
./podman-test.sh logs              # All services
./podman-test.sh logs backend      # Backend only
./podman-test.sh logs frontend     # Frontend only

# Check status
./podman-test.sh status

# Restart services
./podman-test.sh restart

# Open shell in backend
./podman-test.sh shell

# Rebuild everything
./podman-test.sh rebuild

# Clean everything
./podman-test.sh clean
```

## What This Simulates

Your setup now accurately simulates production deployments:

### Backend (Render)
- Python 3.11 FastAPI application
- Gunicorn with Uvicorn workers
- PostgreSQL 15 database
- Production environment variables
- Health checks enabled

### Frontend (Vercel)
- React production build
- Served by nginx
- Production environment variables
- Static asset optimization

## Testing Workflow

### 1. Development Cycle
```bash
# Make changes to code
vim backend/app/main.py

# Rebuild and restart
./podman-test.sh rebuild

# Test changes
curl http://localhost:8000/health
```

### 2. Database Changes
```bash
# Stop services
./podman-test.sh stop

# Clean database
podman-compose -f docker-compose.prod.yml down -v

# Start fresh
./podman-test.sh start
```

### 3. Run Tests
```bash
# Backend tests
./podman-test.sh shell
pytest tests/ -v
exit

# Or from host
podman exec -it wolf-goat-pig_backend_1 pytest tests/
```

## Differences from Production

| Aspect | Local (Podman) | Production |
|--------|----------------|------------|
| Backend | http://localhost:8000 | https://wolf-goat-pig.onrender.com |
| Frontend | http://localhost:3000 | https://wolf-goat-pig.vercel.app |
| Database | Local PostgreSQL container | Render managed PostgreSQL |
| SSL | No (HTTP) | Yes (automatic HTTPS) |
| Scaling | Single instance | Auto-scaling |
| CDN | No | Vercel Edge Network |

## Troubleshooting

### Services Won't Start
```bash
./podman-test.sh clean
./podman-test.sh start
```

### Disk Space Issues
```bash
# Check disk usage
podman system df

# Clean up
podman system prune -af --volumes
```

### Backend Fails to Start
```bash
# Check logs
./podman-test.sh logs backend

# Common issues:
# - Database not ready: Wait 10-15 seconds after start
# - Port conflict: Stop other services on port 8000
# - Stale database: Run `./podman-test.sh clean` and restart
```

### Frontend Build Issues
```bash
# Check Node version matches Dockerfile (node:20-alpine)
# Rebuild without cache
podman-compose -f docker-compose.prod.yml build --no-cache frontend
```

## Performance Notes

With your current Podman machine configuration:
- **Disk**: 60GB (plenty for all images and containers)
- **Memory**: 8GB (good for running multiple services)
- **CPUs**: 5 (fast builds)

If you need more resources:
```bash
podman machine stop
podman machine rm -f podman-machine-default
podman machine init --cpus 8 --memory 16384 --disk-size 100
podman machine start
```

## Next Steps

1. **Test your application**: Open http://localhost:3000 and verify all features work
2. **Run your test suite**: Use `./podman-test.sh test` or run tests in the container
3. **Compare with production**: Test features that should match production behavior
4. **CI/CD Integration**: Consider adding Podman tests to your CI pipeline

## Useful Links

- **Quick Start**: `PODMAN_QUICK_START.md`
- **Full Guide**: `docs/PODMAN_TESTING_GUIDE.md`
- **Backend Dockerfile**: `backend/Dockerfile.prod`
- **Frontend Dockerfile**: `frontend/Dockerfile.prod`
- **Compose File**: `docker-compose.prod.yml`
- **Environment**: `.env.local`

## Tips

1. **Keep logs running**: Open a second terminal with `./podman-test.sh logs` while developing
2. **Use rebuild**: After significant code changes, use `./podman-test.sh rebuild`
3. **Check disk usage**: Periodically run `podman system df` to monitor space
4. **Database persistence**: Volumes persist between runs unless you use `down -v`
5. **Production parity**: Test features in this environment before deploying

---

**Status**: ✅ All systems operational
**Date**: 2025-10-24
**Podman Version**: 5.6.2
**Machine**: podman-machine-default (60GB, 8GB RAM, 5 CPUs)
