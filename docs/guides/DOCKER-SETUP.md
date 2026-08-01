# Local Containers (Docker / Podman)

Run the full stack locally in containers that approximate Cloud Run (backend)
and Firebase Hosting (frontend) — useful for catching containerization issues
before they reach production. Docker is the default; Podman works too (same
compose file). For the cloud deploy itself, see [DEPLOYMENT.md](./DEPLOYMENT.md).

## What you get

| Service | URL | Mirrors |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Firebase-style static production build |
| Backend API | http://localhost:8000 | Cloud Run container (`render-startup.py`, `/ready`) |
| API docs | http://localhost:8000/docs | — |
| Database | localhost:5432 | Cloud SQL PostgreSQL |

The backend uses the production container startup sequence and PostgreSQL setup;
the frontend builds with `npm run build` and is served by nginx.

## Quick start (Docker)

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env — at minimum set a non-default POSTGRES_PASSWORD

# 2. Start everything
./scripts/development/docker-dev.sh
# or: docker-compose up --build
```

### Environment

Copy `.env.example` to `.env` and set values. Key variables:

- `POSTGRES_PASSWORD` — **change from the default** (the `docker-dev.sh` script warns if unset/default).
- `DATABASE_URL` — derived from `POSTGRES_PASSWORD`, override if needed.
- `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID` — Auth0 config (defaults provided).
- `VITE_API_URL` — usually `http://localhost:8000`.

Optional: `ENVIRONMENT` (`production`/`development`), `LOG_LEVEL`, `*_PORT`,
`ENABLE_GHIN_INTEGRATION`, `ENABLE_EMAIL_NOTIFICATIONS`, `WEB_CONCURRENCY`, and the
`VITE_*` frontend toggles. See `.env.example` for the full list.

## Common commands

```bash
docker-compose up -d                 # start detached
docker-compose logs -f backend       # follow logs (backend|frontend|postgres)
docker-compose down                  # stop
docker-compose down -v               # stop + wipe volumes (clean slate)
docker-compose up --build            # rebuild after code changes
docker-compose exec backend bash     # shell into backend
docker-compose exec backend pytest   # run backend tests in-container
docker-compose exec postgres psql -U wolf_goat_pig_user -d wolf_goat_pig
docker-compose ps                    # status
```

**Hot reload:** the backend auto-reloads Python changes; the **frontend does not** —
React must go through `npm run build`, so rebuild it to see changes:
`docker-compose build frontend && docker-compose up`.

## Podman (rootless alternative)

Podman is Docker-compatible (same `docker-compose.yml`) and runs rootless. A helper
script wraps the common operations:

```bash
# macOS: install + start the Podman VM once
brew install podman podman-compose
podman machine init && podman machine start

# Drive the stack
./scripts/testing/podman-test.sh start     # start all services
./scripts/testing/podman-test.sh status
./scripts/testing/podman-test.sh logs backend
./scripts/testing/podman-test.sh shell     # shell into backend
./scripts/testing/podman-test.sh rebuild   # clean rebuild
./scripts/testing/podman-test.sh clean     # remove containers/images/volumes
./scripts/testing/podman-test.sh stop
```

Podman uses `.env.local` for its environment. Differences from Docker are minor;
the main extra step on macOS is the `podman machine` VM.

## Troubleshooting

**Backend won't start**
```bash
docker-compose logs backend
docker-compose exec backend python -c "from app.database import SessionLocal; SessionLocal(); print('Connected!')"
```

**Frontend build fails**
```bash
docker-compose logs frontend
docker-compose build --no-cache frontend
docker-compose exec frontend env | grep VITE
```

**Database connection issues**
```bash
docker-compose ps postgres
docker-compose exec postgres pg_isready -U wolf_goat_pig_user
docker-compose exec backend env | grep DATABASE_URL
```

**Port conflicts** — change the ports in `.env`:
```bash
BACKEND_PORT=8001
FRONTEND_PORT=3001
POSTGRES_PORT=5433
```

For Podman, substitute `./scripts/testing/podman-test.sh logs <service>` and
`podman machine list` to confirm the VM is running.

## Differences from cloud

| Aspect | Local container | GCP production |
|--------|-----------------|-----------------|
| Database | Local PostgreSQL | Cloud SQL PostgreSQL |
| SSL | HTTP | HTTPS (automatic) |
| Scaling | Single container | Auto-scaling |
| Env vars | `.env` / `.env.local` | Cloud Run + Secret Manager / GitHub Actions |
| CDN | none | Firebase Hosting CDN |

Auth0 uses the real production tenant in both, and external APIs work locally only
if their keys are present in your env file.
