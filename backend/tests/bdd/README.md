# BDD / end-to-end layer (behave)

These behave scenarios exercise Wolf Goat Pig **game rules against a running
backend** over HTTP. They are an explicit **end-to-end layer and are NOT part
of the CI gate** (`backend-ci.yml` runs only the in-process pytest suite).

## Run

1. Start the backend locally so it answers on `http://localhost:8000`
   (override with `BACKEND_URL`).
2. From the repo root:

   ```bash
   ./scripts/testing/run_behave.sh
   # or directly:
   behave backend/tests/bdd/behave
   ```

Dependencies (`behave`, `pyhamcrest`) come from `backend/requirements-testing.txt`.

## Layout

- `behave/features/` — `.feature` scenarios (Gherkin)
- `behave/steps/`    — step definitions
- `environment.py`   — behave hooks; puts the repo root on `sys.path` and sets
  `ENVIRONMENT=test` / a sqlite `DATABASE_URL`

## Why it's not in CI

The rules under test are increasingly computed client-side; this layer needs a
live server and is kept for manual/local verification, not deploy gating.
