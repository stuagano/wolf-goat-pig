# Podman Quick Start

Quick reference for testing Wolf-Goat-Pig locally with Podman.

## Prerequisites Check

```bash
podman --version          # Should show 5.6.2 or later
podman-compose --version  # Should show 1.5.0 or later
podman machine list       # Should show "Currently running"
```

## Common Commands

```bash
# Start all services (backend, frontend, database)
./podman-test.sh start

# View logs
./podman-test.sh logs              # All services
./podman-test.sh logs backend      # Backend only
./podman-test.sh logs frontend     # Frontend only

# Check status
./podman-test.sh status

# Stop services
./podman-test.sh stop

# Restart services
./podman-test.sh restart

# Run tests
./podman-test.sh test

# Open shell in backend
./podman-test.sh shell

# Clean rebuild
./podman-test.sh rebuild

# Remove everything
./podman-test.sh clean
```

## Access Points

After running `./podman-test.sh start`:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Typical Workflow

```bash
# 1. Start services
./podman-test.sh start

# 2. In another terminal, watch logs
./podman-test.sh logs backend

# 3. Test the application
open http://localhost:3000

# 4. When done, stop services
./podman-test.sh stop
```

## Troubleshooting

### Services won't start
```bash
./podman-test.sh clean
./podman-test.sh start
```

### Port already in use
```bash
lsof -i :8000  # Find what's using port 8000
lsof -i :3000  # Find what's using port 3000
```

### Podman machine not running
```bash
podman machine start
```

### Need to rebuild after code changes
```bash
./podman-test.sh rebuild
```

## Configuration

- **Environment variables**: `.env.local`
- **Compose file**: `docker-compose.prod.yml`
- **Backend Dockerfile**: `backend/Dockerfile.prod`
- **Frontend Dockerfile**: `frontend/Dockerfile.prod`

## What's Running?

This setup simulates:

- **Render** (backend): Python/FastAPI with Gunicorn + Uvicorn
- **Vercel** (frontend): React app built and served by nginx
- **Database**: PostgreSQL 15

All running in isolated Podman containers with production-like settings.

## Full Documentation

See [docs/PODMAN_TESTING_GUIDE.md](docs/PODMAN_TESTING_GUIDE.md) for complete documentation.
