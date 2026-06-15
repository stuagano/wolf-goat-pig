# Test Infrastructure Consolidation — Design

**Date:** 2026-06-14
**Status:** Approved (design phase)
**Author:** Stuart Gano (with Isaac)

## Problem

The repo carries two parallel test trees that have drifted apart:

| | `backend/tests/` | root `tests/` |
|---|---|---|
| Files | 85 | 14 |
| Import style | `from app.*` (consistent) | mixed `from app` / `from backend.app` |
| In CI? | yes (`backend-ci.yml`) | no |
| Collects? | yes — 1245+ unit tests pass | **6 of 14 error on collection** |
| Nature | real unit/service/engine/router/infra coverage | legacy smoke scripts, print-demos, broken-import regressions, an orphaned-feeling BDD suite |

On top of the two trees: two backend virtualenvs (`backend/.venv`, 90 pkgs, broken — missing `resend`; `backend/venv`, 97 pkgs, working) and three requirements files (`requirements.txt`, `requirements-testing.txt`, `requirements-local.txt`). The result is "which suite / which venv / which config?" ambiguity every time tests are run.

## Goal

**One test infrastructure, one suite.** `backend/` becomes the single test home: one pytest config, one conftest chain, one documented venv. The root `tests/` tree is dissolved file-by-file — salvaged, relocated, or deleted.

Non-goals: rewriting backend test coverage, changing CI gating semantics, touching production code.

## Design

### 1. Single config & conftest

- **Keep** `backend/pyproject.toml` `[tool.pytest.ini_options]` as the only pytest config. It already carries `pythonpath = ["../.ctk"]`.
- **Delete** root `tests/conftest.py`. The `.ctk` `sys.path` wiring previously added to it disappears with the file, leaving `.ctk` wired through exactly one point: backend's `pythonpath`.

### 2. Disposition of the 14 root files

**DELETE (9)** — live-server smoke scripts and print-demos with no real in-process assertions; their topics (monte-carlo, courses, holes, sheets, deployment) are already covered by backend router/engine tests:

- `tests/test_monte_carlo_api.py`
- `tests/integration/test_monte_carlo.py`
- `tests/integration/test_deployment.py`
- `tests/integration/test_course_import.py`
- `tests/integration/functional_test_suite.py` (selenium)
- `tests/integration/simple_course_test.py`
- `tests/integration/test_course_enhancements.py`
- `tests/integration/test_multi_hole_tracking.py` (0 test functions)
- `tests/conftest.py`

**SALVAGE (2)** — real bug-regressions, rewritten as in-process `TestClient`/service tests with `from app.*` imports, placed next to their closest existing peer:

- `tests/test_hole_update_fix.py` → regression "updating a past hole must not erase future holes." Verify whether `backend/tests/unit/routers/test_games_holes_router.py` already asserts this (it has save/delete/state coverage but not obviously the edit-preserves-later-holes case). If a gap exists, add the assertion there as a `TestClient` test. If already covered, document that and delete.
- `tests/integration/test_sheet_sync_fix.py` → regression "one bad player must not abort the whole sheet-sync transaction." Confirmed **not** covered by `test_spreadsheet_sync_router.py` (that file covers endpoints/validation only). Rewrite as a service-level test under `backend/tests/unit/services/` driving `SheetIntegrationService` directly (matching the original's import style).

**RELOCATE (4)** → `backend/tests/bdd/` — a runnable behave suite (126 step defs + `game_rules_core.feature`):

- `tests/bdd/environment.py`
- `tests/bdd/behave/steps/game_rules_steps.py`
- `tests/bdd/behave/steps/utils/__init__.py`
- `tests/bdd/behave/features/game_rules_core.feature`

Fixups on relocation:
- `environment.py` computes repo root via `Path(__file__).resolve().parents[2]`. After the move to `backend/tests/bdd/environment.py`, that becomes `parents[3]`. Adjust so the repo root still resolves correctly.
- Add `backend/tests/bdd/README.md` documenting this as an **explicitly non-CI e2e layer**: it hits a live backend at `http://localhost:8000` (override via `BACKEND_URL`), is run manually with `behave backend/tests/bdd/behave`, and is *not* part of the deploy gate.

### 3. One venv / requirements story

Both venvs are gitignored (local only) — so this is documentation plus a local cleanup, not a committed deletion of tracked files.

- Canonical venv: `backend/venv` (working). Remove the local `backend/.venv` directory.
- Document the single setup in `CLAUDE.md`:
  ```bash
  cd backend && python -m venv venv && source venv/bin/activate
  pip install -r requirements.txt -r requirements-testing.txt
  ```
- **Delete `backend/requirements-local.txt`** — its only addition (`httpx`) is already in `requirements.txt`, making it redundant. Confirm nothing references it (Dockerfiles, scripts, CI) before deleting; update any reference to point at `requirements.txt`.

### 4. CI — unchanged

`backend-ci.yml` already runs from `backend/` and is the single gate (`pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic`). The relocated BDD suite stays manual and documented in its README. No workflow edits required. `requirements-testing.txt` already includes `behave` and `pytest-playwright`, so the BDD/e2e deps remain installable.

### 5. Net result

```
backend/
  pyproject.toml          # the one pytest config (+ .ctk pythonpath)
  conftest.py             # the one root conftest
  venv/                   # the one venv
  requirements.txt
  requirements-testing.txt
  tests/
    unit/{routers,services,engine}/   # + 2 salvaged regressions land here
    services/ infra/ integration/ game_rules/ api/
    bdd/                  # relocated behave e2e (non-CI, documented)
.ctk/                     # wired only via backend pyproject now
# root tests/ — removed
# backend/.venv, backend/requirements-local.txt — removed
```

## Verification

After implementation, the consolidation is correct when:

1. `cd backend && pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic -q` is green (no regression vs. the current 1245+ pass), run with `backend/venv`.
2. The 2 salvaged regressions exist as passing in-process tests (or are documented as already-covered).
3. `behave backend/tests/bdd/behave` discovers the feature + steps and resolves the repo root (smoke: collection succeeds; full run requires a live backend).
4. The repo root has no `tests/` directory and no `tests/conftest.py`.
5. `grep -rn "requirements-local" .` returns no live references; `backend/.venv` is gone.
6. `from ctk import ...` still resolves in the backend suite (single wiring point intact).

## Risks

- **Hidden coverage loss:** a deleted smoke script might assert something backend doesn't. Mitigation: the salvage step explicitly verifies the two known regressions; the deleted 9 are smoke/print-demos whose *topics* are covered by backend router/engine tests, but their specific assertions are not audited line-by-line. Accepted per "salvage incl. BDD" scope.
- **BDD path math:** off-by-one on `parents[N]` after the move would silently break repo-root import. Mitigation: verify behave collection post-move (verification step 3).
- **Stale references to deleted files:** Dockerfiles/scripts/CI may reference `requirements-local.txt` or root `tests/`. Mitigation: grep before deleting (verification steps 5).
