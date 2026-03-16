# Wolf Goat Pig

Golf wagering app with FastAPI backend and React frontend.

## Stack

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL (deployed on Render)
- **Frontend**: React with hooks, JavaScript/JSX (deployed on Vercel)
- **Auth**: Auth0
- **Testing**: Jest (frontend), pytest (backend)

## Build & Test

```bash
# Frontend
cd frontend && npm run build
cd frontend && npm test -- --watchAll=false

# Backend
cd backend && pytest

# Type checking
cd backend && mypy app
cd frontend && npm run typecheck
```

## Deployment

- Backend deploys to Render via `render.yaml`
- Frontend deploys to Vercel via `vercel.json`
- Local Docker setup via `docker-compose.yml`

## File Organization

- `backend/` - FastAPI application
- `frontend/` - React SPA
- `scripts/` - Deployment, development, diagnostics, and testing scripts

## Code Style

- Modular design: files under 500 lines
- Never hardcode secrets
- No `console.log` in production code
- Separate concerns with clean architecture
