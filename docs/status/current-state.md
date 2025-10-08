# Current Project Status

_Last updated: 2025-10-08_

This document captures the real-world status of the Wolf Goat Pig stack so contributors can quickly understand what works, what is flaky, and the next cleanup priorities.

## High-level summary

- ✅ Repository layout has been normalized; reference documentation now lives under `docs/` with clear categories.
- ⚠️ `start_simulation.py` now auto-installs backend dependencies and configures `.env` defaults, but it needs internet access to pull packages on a fresh environment.
- ⚠️ Backend test execution expects Python 3.12.0 (via Pyenv); the version is missing in clean environments, so `pytest` fails until Pyenv is configured.
- ❓ Frontend build/test status is currently unverified—run `npm test` and `npm run build` after reinstalling dependencies to confirm.

## Backend checklist

| Item | Status | Notes |
| ---- | ------ | ----- |
| `python start_simulation.py` | ⚠️ Installs backend dependencies from `backend/requirements.txt`, loads `.env` defaults, and then starts Uvicorn. Requires network access the first time dependencies are installed. |
| Direct `uvicorn app.main:app --reload` | ⚠️ Blocked by same missing dependency unless optional email service is disabled. |
| Database migrations | ✅ SQLite bootstrap occurs automatically through SQLAlchemy on first run. |
| Third-party integrations | ⚠️ Auth0, GHIN, and email services require secrets supplied via environment variables before production use. |

## Frontend checklist

| Item | Status | Notes |
| ---- | ------ | ----- |
| `npm install` | ✅ Package manifests are up-to-date. |
| `npm start` | ❓ Not exercised in this run. |
| `npm test -- --watchAll=false` | ❓ Pending verification. |
| `npm run build` | ❓ Pending verification. |

## Testing & diagnostics

| Tool | Status | Notes |
| ---- | ------ | ----- |
| `cd backend && pytest` | ⚠️ Fails because Pyenv is pinned to Python 3.12.0 but that version is not installed in the default dev container. Install with `pyenv install 3.12.0` or update `.python-version`. |
| `./scripts/diagnostics/run_simulation_tests.sh` | ❓ Not executed after restructuring—update once backend pytest runs. |
| Legacy shell/python diagnostics | ✅ Scripts moved under `scripts/diagnostics/` and now operate relative to the repository root. |

## Follow-up work

1. Install or mock the `emails` dependency so the backend can start without manual package tweaks.
2. Decide whether to keep Pyenv pinned to 3.12.0 or adjust to 3.11.x to match currently installed runtimes.
3. Run the full diagnostic suite (`./scripts/diagnostics/run_simulation_tests.sh`) once the Python version mismatch is resolved.
4. Capture frontend verification results here after the next maintainer run.
