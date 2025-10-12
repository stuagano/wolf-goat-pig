# Wolf Goat Pig Golf Simulation

Wolf Goat Pig is a golf wagering simulation that pairs a FastAPI backend with a React frontend. The service models an entire round of play, including handicaps, betting state, and scenario-driven decision making for both humans and AI partners.

## Repository layout

```
├── backend/                 # FastAPI application and domain logic
├── frontend/                # React single page application
├── config/                  # Infrastructure and environment configuration
├── docs/                    # Product, engineering, and archived reference docs
├── reports/                 # Generated analytics artifacts
├── scripts/diagnostics/     # Ad-hoc health checks and simulation exercisers
├── tests/                   # Automated test suites (backend, frontend, BDD)
├── install.py               # Convenience installer for local tooling
├── start_simulation.py      # Quick-start script for simulation checks
├── dev.sh                   # Combined backend/frontend development runner
└── README.md                # You are here
```

## Prerequisites

| Tool | Version | Notes |
| ---- | ------- | ----- |
| Python | 3.11.x | Required by the FastAPI backend. Pyenv is configured to use 3.12.0 – install that version or update `.python-version`. |
| Node.js | 20.x | Required for the React 19 frontend (React Scripts 5). |
| npm | 10.x | Ships with Node 20. |
| SQLite | Built-in | Default development database. |

## Environment variables

1. Copy the root `.env.example` to `.env` and customize values for your environment.
2. For backend-only work, you can also create `backend/.env` with overrides. Python services load from the process environment, so exporting variables before starting the server is sufficient.
3. Never hardcode secrets or hostnames—treat `.env.example` as the canonical source of truth.

## Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows use .venv\Scripts\activate
pip install -r requirements.txt
```

Start the API locally:

```bash
uvicorn app.main:app --reload
```

A convenience runner is available via `./dev.sh` (starts both services) or `python start_simulation.py`. The startup script will:

- Install any missing backend dependencies from `backend/requirements.txt`.
- Load environment variables from `.env` (falling back to `.env.example` for defaults) without overriding values already exported in your shell.
- Ensure a local SQLite database exists at `reports/wolf_goat_pig.db` unless `DATABASE_URL` points elsewhere.
- Launch the FastAPI server with host/port derived from `WGP_API_HOST`/`WGP_API_PORT`.

## Frontend setup

```bash
cd frontend
npm install
npm start
```

The frontend expects `REACT_APP_API_URL` to be defined. When running everything locally it defaults to `http://localhost:8000`.

## Testing & diagnostics

### Unit and Integration Tests

| Command | Purpose |
| ------- | ------- |
| `cd backend && pytest` | Backend unit and integration suites. Configure Pyenv or virtualenv to expose Python 3.12.0 when running inside the repository. |
| `cd frontend && npm test -- --watchAll=false` | Frontend component tests. |
| `./scripts/diagnostics/run_simulation_tests.sh` | Orchestrates backend pytest, frontend tests, and simulation smoke checks. |
| `./scripts/diagnostics/test-local.sh` | Legacy shell health check for quick API verification. |
| `python scripts/diagnostics/simulation_startup_check.py` | Validates that core simulation modules import correctly without external services. |

### Deployment Testing

| Command | Purpose |
| ------- | ------- |
| `./scripts/test-prod-all.sh` | Interactive menu for comprehensive deployment testing |
| `./scripts/test-prod-backend.sh` | Test backend in Render-like production environment |
| `./scripts/test-prod-frontend.sh` | Test frontend production build (Vercel-like) |
| `python scripts/verify-deployments.py` | Verify deployment health and integration |
| `docker-compose -f docker-compose.prod.yml up` | Full production stack simulation with PostgreSQL |

See [`docs/guides/local-deployment-testing.md`](./docs/guides/local-deployment-testing.md) for detailed deployment testing instructions.

## Documentation map

- **Guides** – development, deployment, and troubleshooting: [`docs/guides/`](./docs/guides/).
- **Product context** – gameplay UX and integration notes: [`docs/product/`](./docs/product/).
- **Reports** – historical environment and simulation findings: [`docs/reports/`](./docs/reports/).
- **Archive** – BMad framework artifacts and AI agent notes: [`docs/archive/`](./docs/archive/).
- **Stories** – feature backlog and BDD scenarios: [`docs/stories/`](./docs/stories/).

See [`docs/status/current-state.md`](./docs/status/current-state.md) for an up-to-date overview of what currently works and what still needs attention.

## Contributing

- Use feature branches and keep commits focused.
- Update or add tests when behavior changes.
- Run the relevant diagnostics listed above before opening a PR.
- Document notable deviations from the expected local workflow in [`docs/status/current-state.md`](./docs/status/current-state.md).

For any larger restructuring, create an issue outlining the proposed changes so the team can weigh in before implementation.
