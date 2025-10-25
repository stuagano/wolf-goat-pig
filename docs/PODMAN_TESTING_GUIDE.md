# Podman Local Testing Guide

This guide explains how to use Podman to test the Wolf-Goat-Pig application locally in an environment that simulates the production deployments on Render (backend) and Vercel (frontend).

## Table of Contents

- [Why Podman?](#why-podman)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Detailed Usage](#detailed-usage)
- [Testing Scenarios](#testing-scenarios)
- [Troubleshooting](#troubleshooting)
- [Differences from Production](#differences-from-production)

## Why Podman?

Podman provides several advantages for local testing:

- **Rootless containers**: More secure than Docker
- **Docker-compatible**: Uses the same Dockerfile and docker-compose syntax
- **Production parity**: Closely simulates Render and Vercel environments
- **No daemon**: Lightweight and easier to manage
- **Native on macOS**: Works well with Apple Silicon

## Prerequisites

### Install Podman

```bash
# macOS
brew install podman podman-compose

# Linux
sudo apt-get install podman podman-compose  # Debian/Ubuntu
sudo dnf install podman podman-compose      # Fedora/RHEL
```

### Initialize Podman Machine (macOS only)

```bash
podman machine init
podman machine start
```

### Verify Installation

```bash
podman --version
podman-compose --version
podman machine list  # Should show a running machine
```

## Quick Start

### 1. Start All Services

```bash
./podman-test.sh start
```

This will:
- Start PostgreSQL database
- Build and start the backend API (simulating Render)
- Build and start the frontend (simulating Vercel)

### 2. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 3. View Logs

```bash
# All services
./podman-test.sh logs

# Specific service
./podman-test.sh logs backend
./podman-test.sh logs frontend
./podman-test.sh logs postgres
```

### 4. Stop Services

```bash
./podman-test.sh stop
```

## Architecture

The local Podman setup simulates your production architecture:

```
┌─────────────────────────────────────────────┐
│         Local Podman Environment            │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐      ┌──────────────┐   │
│  │   Frontend   │      │   Backend    │   │
│  │   (nginx)    │ ───> │  (gunicorn)  │   │
│  │ Port: 3000   │      │  Port: 8000  │   │
│  │              │      │              │   │
│  │ Simulates:   │      │ Simulates:   │   │
│  │   Vercel     │      │   Render     │   │
│  └──────────────┘      └───────┬──────┘   │
│                                 │          │
│                         ┌───────▼──────┐   │
│                         │  PostgreSQL  │   │
│                         │  Port: 5432  │   │
│                         └──────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

### Service Details

#### Frontend Container (Vercel Simulation)
- **Image**: nginx:alpine
- **Build**: React app built with production settings
- **Port**: 3000 (maps to nginx:80)
- **Environment**: Production build with API URL pointing to backend
- **Config**: Dockerfile.prod in `frontend/`

#### Backend Container (Render Simulation)
- **Image**: Python 3.11-slim
- **Build**: Gunicorn + Uvicorn workers
- **Port**: 8000
- **Environment**: Production mode with PostgreSQL
- **Config**: Dockerfile.prod in `backend/`

#### Database Container
- **Image**: PostgreSQL 15 Alpine
- **Port**: 5432
- **Data**: Persisted in named volume `postgres_data`

## Detailed Usage

### Available Commands

```bash
./podman-test.sh [command]
```

| Command | Description |
|---------|-------------|
| `start` | Start all services |
| `stop` | Stop all services |
| `restart` | Restart all services |
| `status` | Show service status |
| `logs` | View all logs (follow mode) |
| `logs <service>` | View specific service logs |
| `test` | Run tests in production environment |
| `shell` | Open bash shell in backend container |
| `rebuild` | Rebuild all services from scratch |
| `clean` | Remove all containers, images, volumes |
| `help` | Show help message |

### Examples

#### Start and Monitor Services

```bash
# Start services
./podman-test.sh start

# Check status
./podman-test.sh status

# Watch backend logs
./podman-test.sh logs backend
```

#### Debug Backend Issues

```bash
# Open shell in backend
./podman-test.sh shell

# Inside container, you can:
# - Check database connection: python -c "from app.database import engine; print(engine)"
# - Run specific tests: pytest tests/test_specific.py -v
# - Check environment: printenv
# - Inspect files: ls -la
```

#### Full Rebuild

```bash
# Clean rebuild (useful after code changes)
./podman-test.sh rebuild

# Nuclear option - clean everything
./podman-test.sh clean
./podman-test.sh start
```

### Environment Configuration

The `.env.local` file contains all environment variables for local testing:

```bash
# Backend (Render simulation)
DATABASE_URL=postgresql://wgp_user:wgp_pass_secure_123@postgres:5432/wolf_goat_pig
ENVIRONMENT=production
FRONTEND_URL=http://localhost:3000

# Frontend (Vercel simulation)
REACT_APP_API_URL=http://localhost:8000

# Auth0 (same as production)
AUTH0_DOMAIN=dev-jm88n088hpt7oe48.us.auth0.com
# ... etc
```

You can modify `.env.local` to test different configurations.

## Testing Scenarios

### 1. Test Production Build

```bash
./podman-test.sh start
# Verify both services are running
./podman-test.sh status
# Test API
curl http://localhost:8000/health
# Open browser to http://localhost:3000
```

### 2. Test Database Migrations

```bash
./podman-test.sh shell
# Inside container:
alembic upgrade head
# Check migrations applied
```

### 3. Test API Endpoints

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test game creation
curl -X POST http://localhost:8000/api/games \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Game"}'

# Test with API docs
open http://localhost:8000/docs
```

### 4. Test Frontend Build

```bash
# The frontend container serves the production build
# Test that all routes work:
open http://localhost:3000
open http://localhost:3000/games
open http://localhost:3000/profile

# Check console for errors
# Verify API calls work
```

### 5. Test Full Stack Integration

```bash
# Start services
./podman-test.sh start

# In another terminal, run integration tests
pytest tests/integration/ -v

# Or run functional tests
pytest tests/functional/ -v
```

### 6. Test Database Persistence

```bash
# Start services and create data
./podman-test.sh start
# Use the app to create games, players, etc.

# Stop services
./podman-test.sh stop

# Start again - data should persist
./podman-test.sh start
# Verify data is still there
```

### 7. Performance Testing

```bash
# Start services
./podman-test.sh start

# Use Apache Bench or similar
ab -n 1000 -c 10 http://localhost:8000/health

# Monitor logs during load
./podman-test.sh logs backend
```

## Troubleshooting

### Podman Machine Not Running

```bash
# Check status
podman machine list

# Start machine
podman machine start

# If that fails, reinitialize
podman machine stop
podman machine rm
podman machine init
podman machine start
```

### Port Already in Use

```bash
# Find what's using the port
lsof -i :8000
lsof -i :3000

# Kill the process or change ports in .env.local
PORT=8001 ./podman-test.sh start
```

### Services Won't Start

```bash
# Check logs
./podman-test.sh logs

# Try rebuilding
./podman-test.sh rebuild

# Check Podman system
podman system info
podman system df
```

### Database Connection Issues

```bash
# Check postgres is running
./podman-test.sh status

# Check logs
./podman-test.sh logs postgres

# Connect to database directly
podman exec -it <postgres-container-id> psql -U wgp_user -d wolf_goat_pig
```

### Frontend Build Fails

```bash
# Check Node version in Dockerfile.prod
# Verify all environment variables are set in .env.local

# Build frontend manually to see errors
cd frontend
npm run build

# Check logs
./podman-test.sh logs frontend
```

### Image Build Fails

```bash
# Clean everything and retry
./podman-test.sh clean
podman system prune -af

# Build with verbose output
podman-compose -f docker-compose.prod.yml build --no-cache --progress=plain
```

### Out of Disk Space

```bash
# Check disk usage
podman system df

# Clean up
podman system prune -af --volumes

# Remove unused images
podman image prune -af
```

## Differences from Production

While this setup closely simulates production, be aware of these differences:

### Architecture Differences

| Aspect | Local (Podman) | Production |
|--------|----------------|------------|
| **Backend Host** | Render uses managed infrastructure | Local uses Podman containers |
| **Frontend Host** | Vercel CDN | Local nginx container |
| **Database** | Local PostgreSQL container | Render managed PostgreSQL |
| **Domain** | localhost | wolf-goat-pig.onrender.com / vercel.app |
| **HTTPS** | No (HTTP only) | Yes (automatic SSL) |
| **Scaling** | Single instance | Auto-scaling |
| **CDN** | No | Vercel Edge Network |

### Environment Variables

- **Local**: All in `.env.local`
- **Production**: Split between Render and Vercel dashboards

### Performance

- **Local**: Limited by your machine
- **Production**: Cloud resources, potentially better performance

### Monitoring

- **Local**: Manual log viewing
- **Production**: Render/Vercel dashboards, metrics, alerts

### Database

- **Local**: Fresh database each time (unless volumes preserved)
- **Production**: Persistent, backed up database

### Testing Production-Only Features

Some features may behave differently:
- **Auth0**: Works the same (uses production Auth0 instance)
- **External APIs**: Works if API keys are in `.env.local`
- **File uploads**: Different storage paths
- **Email**: May need SMTP configuration

## Best Practices

### 1. Keep .env.local Updated

Whenever production environment variables change, update `.env.local`.

### 2. Test Before Deploying

```bash
# Always test locally first
./podman-test.sh start
./podman-test.sh test
# Then deploy
```

### 3. Use Clean Rebuilds for Major Changes

```bash
# After major code changes
./podman-test.sh rebuild
```

### 4. Monitor Logs

```bash
# Keep logs running in a separate terminal
./podman-test.sh logs
```

### 5. Preserve Database During Development

The database volume persists between runs. To reset:

```bash
./podman-test.sh clean  # Removes volumes
./podman-test.sh start  # Fresh database
```

### 6. Test with Production Data

```bash
# Export from production (if safe)
pg_dump <production-db> > backup.sql

# Import to local
podman exec -i <postgres-container> psql -U wgp_user -d wolf_goat_pig < backup.sql
```

## Next Steps

- Set up CI/CD to run tests in Podman
- Create automated test scripts
- Add monitoring tools (Prometheus, Grafana)
- Set up development vs production compose files
- Document deployment procedures

## Resources

- [Podman Documentation](https://docs.podman.io/)
- [Docker Compose Compatibility](https://docs.podman.io/en/latest/markdown/podman-compose.1.html)
- [Render Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
