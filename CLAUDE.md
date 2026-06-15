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
cd frontend && npx vitest run

# Backend env (one venv — `backend/venv`; do NOT use backend/.venv):
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-testing.txt

# Backend
cd backend && pytest

# Type checking
cd backend && mypy app          # advisory only (pre-existing errors)
cd frontend && npm run typecheck
```

## Definition of done — REQUIRED before every push

Pushing to main auto-deploys (Vercel + Render). The local gate must mirror CI
**exactly** — a subset is not a gate. Run ALL of these and check real exit
codes (don't pipe away failures):

```bash
# Frontend changes (mirrors .github/workflows/frontend-ci.yml):
cd frontend && npm run typecheck && npx vitest run && npm run build
# ⚠️ typecheck is NOT optional — esbuild/vite tolerate syntax tsc rejects,
#    so "build passed" alone has shipped broken code before.

# Backend changes (mirrors .github/workflows/backend-ci.yml):
cd backend && ruff check app/ tests/ && ruff format --check app/ tests/ \
  && pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic
```

Editing rules that prevent past deploy failures:
- NEVER edit source files via shell heredocs/perl when the code contains `!`
  — zsh mangles it to `\!` silently. Use the Edit/Write tools, or a Python
  script written to a file first.
- After any sed/perl/python bulk edit, grep the file for the literal `\!`
  and re-run typecheck.

## Deployment

- Backend deploys to Render via `render.yaml` — but the live service does NOT
  sync env vars from render.yaml; set those in the Render dashboard
- Frontend deploys to Vercel via `vercel.json`
- Local Docker setup via `docker-compose.yml`
- After backend deploys, verify: `curl https://wolf-goat-pig.onrender.com/health`
  (`environment` must be `production`; junk Bearer token to `/players/me`
  should return 401, not 500)

## File Organization

- `backend/` - FastAPI application
- `frontend/` - React SPA
- `scripts/` - Deployment, development, diagnostics, and testing scripts

## Code Style

- Modular design: files under 500 lines
- Never hardcode secrets
- No `console.log` in production code
- Separate concerns with clean architecture
