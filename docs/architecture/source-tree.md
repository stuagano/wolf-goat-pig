# Source Tree Documentation

This documents the actual top-level layout of the repository. It is kept at the
directory/entry-point level on purpose — exhaustive per-file listings drift fast.
For deeper detail, browse the directories directly or see
[architecture.md](./architecture.md).

## Project Structure Overview

```
wolf-goat-pig/
├── api/                  # Vercel serverless functions (e.g. gemini-proxy.js)
├── backend/              # FastAPI backend application
├── booking-service/      # Standalone Node tee-sheet booking service
├── frontend/             # React + Vite frontend application
├── docs/                 # Project documentation
├── scripts/              # Deployment, development, diagnostics, testing scripts
├── render.yaml           # Render deployment (backend + booking-service)
├── vercel.json           # Vercel deployment (frontend)
├── docker-compose.yml    # Local container stack
├── capabilities.yaml     # Capability manifest (caps tooling)
├── package.json          # Root scripts that delegate into frontend/backend
└── README.md             # Project overview
```

## Backend Structure (`/backend`)

```
backend/
├── app/                  # Main application code
│   ├── main.py          # FastAPI application entry
│   ├── database.py      # Database configuration / session
│   ├── models.py        # SQLAlchemy models
│   ├── wolf_goat_pig.py # Core game simulation
│   ├── routers/         # API route modules (one file per resource area)
│   ├── schemas/         # Pydantic request/response schemas
│   ├── services/        # Service layer (email, ghin, foretees, callouts, ...)
│   ├── domain/          # Domain models and game-type handlers
│   ├── engine/          # Scoring / betting / partnership engine modules
│   ├── managers/        # Rule, scoring, and websocket managers
│   ├── state/           # App/course/player/shot state
│   ├── middleware/      # Caching, rate limiting
│   ├── mixins/          # Reusable model mixins (persistence)
│   ├── observability/   # Sentry + external health checks
│   ├── validators/      # Betting / game-state / handicap validators
│   ├── utils/           # Helpers (auth, api, response types, time)
│   ├── migrations/      # Migration package
│   └── data/            # Seed data (legacy players, course data)
├── migrations/          # `*_postgres.sql` files applied at startup
├── tests/               # Test suite (see below)
├── render-startup.py    # Render entrypoint (runs migrations, then uvicorn)
├── requirements.txt     # Python dependencies
└── venv/                # Virtual environment (local; not committed)
```

### Key Backend Modules

- `app/routers/` — FastAPI routers split by area: `games.py`, `games_holes.py`,
  `games_players.py`, `players.py`, `courses.py`, `leaderboard.py`,
  `callouts.py`, `ghin.py`, `foretees.py`, `commissioner.py`, `admin.py`,
  `health.py`, and more.
- `app/services/` — integration and business services: `email_service.py`,
  `ghin_service.py`, `foretees_service.py`, `callout_service.py`,
  `legacy_player_service.py`, `matchmaking_service.py`, etc.
- `app/engine/` — scoring and wagering engine: `scoring.py`, `betting_actions.py`,
  `partnership.py`, `aardvark.py`, `simulation_api.py`.

## Frontend Structure (`/frontend`)

```
frontend/
├── public/              # Static assets
├── src/                 # Source code
│   ├── App.jsx          # Root application component
│   ├── index.jsx        # Application entry / React mount
│   ├── components/      # React components (grouped by feature)
│   ├── pages/           # Route page components (*.jsx)
│   ├── context/         # React context providers (AuthContext, ...)
│   ├── hooks/           # Custom React hooks
│   ├── services/        # API + sync + offline-storage services
│   ├── config/          # Runtime config (api.config.js)
│   ├── constants/       # Shared constants
│   ├── theme/           # Theme provider and tokens
│   ├── utils/           # Utility functions
│   ├── styles/          # CSS
│   └── sentry.js        # Sentry initialization
├── vite.config.js       # Vite build + dev-server proxy config
├── package.json         # Node dependencies and scripts
└── build/               # Production build output (Vite `build.outDir`)
```

### Key Frontend Modules

- `src/components/` — feature folders: `game/`, `betting/`, `signup/`, `chat/`,
  `admin/`, `analytics/`, `auth/`, `email/`, `foretees/`, `tutorial/`,
  `visualization/`, `ui/`, `common/`, `integration/`.
- `src/config/api.config.js` — resolves the backend base URL from
  `import.meta.env.VITE_API_URL`.
- `src/context/AuthContext.jsx` — Auth0 wiring (reads `VITE_AUTH0_*`).
- `src/services/` — `fetchJson.jsx`, `syncManager.jsx`, `offlineStorage.jsx`,
  `gameReconcile.js`, `cacheManager.jsx`, `ghinService.js`.

## Documentation (`/docs`)

```
docs/
├── architecture/        # System architecture, source tree, schema, tech stack
├── backend/             # Backend-specific guides (migrations, sessions, ...)
├── guides/              # Developer/operator guides
├── features/            # Feature specs and rules
├── product/             # Product context
├── observability/       # Sentry / uptime / Render blueprint
├── development/         # Contributor + automation docs
└── README.md            # Documentation index
```

## Environment Variables

### Backend (.env / Render dashboard)
```
DATABASE_URL=postgresql://...
ENVIRONMENT=development|production
FRONTEND_URL=http://localhost:3000
```

### Frontend (.env.local / Vercel dashboard)
```
VITE_API_URL=http://localhost:8000   # empty locally → uses vite.config.js proxy
VITE_AUTH0_DOMAIN=...
VITE_AUTH0_CLIENT_ID=...
VITE_AUTH0_AUDIENCE=https://wolf-goat-pig.onrender.com
```

See `frontend/.env.example` for the full, authoritative list.

## Key Entry Points

### Backend Entry
- **File**: `backend/app/main.py`
- **Render start**: `python render-startup.py` (applies migrations, then serves)
- **Local start**: `uvicorn app.main:app`

### Frontend Entry
- **File**: `frontend/src/index.jsx`
- **Dev start**: `npm start` (runs Vite dev server on port 3000)
- **Build**: `npm run build` (Vite)

## Testing Structure

```
backend/tests/
├── unit/                # Unit tests
├── integration/         # Integration tests
├── contract/            # Mocked external-service contract tests (in CI)
├── live/                # Real external APIs (on-demand: pytest -m live)
├── api/                 # API/router tests
├── game_rules/          # Game-rule tests
├── bdd/                 # behave e2e (non-CI; needs live backend)
├── infra/               # Infra/startup tests
├── fixtures/            # Shared fixtures
├── manual/              # Manual/excluded-from-CI tests
└── conftest.py          # Pytest configuration
```

Frontend tests live alongside source under `__tests__/` directories and `*.test.js[x]`
files, run with Vitest.

## Deployment Artifacts

### Backend Deployment
- Render reads from root `render.yaml` (`rootDir: backend`).
- Migrations run at startup via `render-startup.py` → `app/migrations_runner.py`.

### Frontend Deployment
- Vercel reads from root `vercel.json` (builds `frontend/` with Vite).
- Output directory: `frontend/build`, served as a static SPA with CDN.

### Booking Service
- Separate Render service (`rootDir: booking-service`, `node server.js`).

---

*Reflects the repository structure as of 2026-06-17.*
