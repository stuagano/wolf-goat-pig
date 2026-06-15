# Test Infrastructure Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse the two divergent test trees into a single `backend/`-rooted suite — salvaging two real regressions, relocating the behave BDD suite as a documented non-CI e2e layer, and deleting legacy smoke/print-demo scripts — leaving one config, one conftest, one venv story.

**Architecture:** `backend/tests/` is the survivor (85 files, in CI, `from app.*`). The root `tests/` tree is dissolved file-by-file. Salvaged regressions become proper in-process tests next to their peers. BDD moves under `backend/tests/bdd/` with corrected path math and a README. `requirements-local.txt` and the broken local `.venv` are removed.

**Tech Stack:** pytest 9, FastAPI `TestClient`, SQLAlchemy (sqlite for tests), behave, the vendored `.ctk` kit.

**Spec:** `docs/superpowers/specs/2026-06-14-test-infra-consolidation-design.md`

**Run all backend commands with the working venv:** `backend/venv/bin/python -m pytest ...` (the homebrew `python3` and `backend/.venv` are missing `resend` and cannot import `app.main`).

---

## Pre-flight: branch

- [ ] **Step 1: Create a working branch** (we're on `main`, which auto-deploys; test moves touch the CI gate)

```bash
cd /Users/stuart.gano/Documents/wolf-goat-pig
git checkout -b chore/test-infra-consolidation
git status
```

Expected: on branch `chore/test-infra-consolidation`; the working tree still shows the pre-existing `M` files and untracked `.ctk/`, plus the spec/plan docs.

- [ ] **Step 2: Baseline the backend suite is green before changes**

Run: `cd backend && venv/bin/python -m pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic -q 2>&1 | tail -5`
Expected: all pass (~1315 passed). Record the number — it must not drop after this work (it will *rise* by the salvaged tests).

---

## Task 1: Salvage the course hole-update regression

The bug: `PUT /courses/{name}` with a partial `holes` list must update only the listed holes and **preserve** the rest — "updating a hole in the past must not erase future holes." Source: `tests/test_hole_update_fix.py`. No backend test covers this (`test_courses_router.py` has list/get/create/delete only). Place it next to the courses router tests.

**Files:**
- Modify: `backend/tests/unit/routers/test_courses_router.py` (append a `TestUpdateCoursePreservesHoles` class)

- [ ] **Step 1: Append the salvaged regression to the courses router tests**

Append to the end of `backend/tests/unit/routers/test_courses_router.py` (it already defines module-level `client = TestClient(app)`):

```python


class TestUpdateCoursePreservesHoles:
    """Regression (salvaged from root tests/test_hole_update_fix.py): a partial
    PUT /courses/{name} must update only the listed holes and preserve the rest.
    Bug it guards: 'updating a hole in the past erases all future holes.'"""

    _NAME = "WGP Hole-Update Regression Course"

    def _eighteen_holes(self):
        return [
            {
                "hole_number": i,
                "par": 4,
                "yards": 400,
                "handicap": i,
                "description": f"Hole {i}",
                "tee_box": "regular",
            }
            for i in range(1, 19)
        ]

    def _holes_via_db(self):
        from app.database import get_db
        from app import models

        db = next(get_db())
        course = (
            db.query(models.Course).filter(models.Course.name == self._NAME).first()
        )
        assert course is not None, "course was not created"
        return {
            h.hole_number: h
            for h in db.query(models.Hole)
            .filter(models.Hole.course_id == course.id)
            .all()
        }

    def test_partial_update_preserves_other_holes(self):
        # Clean slate in case a previous run left this course behind.
        client.delete(f"/courses/{self._NAME}")

        resp = client.post(
            "/courses",
            json={
                "name": self._NAME,
                "description": "regression fixture",
                "holes": self._eighteen_holes(),
            },
        )
        assert resp.status_code == 200
        assert len(self._holes_via_db()) == 18

        # Update ONLY hole 5.
        resp = client.put(
            f"/courses/{self._NAME}",
            json={
                "holes": [
                    {
                        "hole_number": 5,
                        "par": 3,
                        "yards": 180,
                        "handicap": 5,
                        "description": "Updated Hole 5 - now a par 3",
                        "tee_box": "regular",
                    }
                ]
            },
        )
        assert resp.status_code == 200

        holes = self._holes_via_db()
        # All 18 survive — this is the bug fix.
        assert len(holes) == 18, f"expected 18 holes, found {len(holes)}"
        # Hole 5 changed.
        assert holes[5].par == 3
        assert holes[5].yards == 180
        # Every other hole is untouched.
        for n in list(range(1, 5)) + list(range(6, 19)):
            assert holes[n].par == 4, f"hole {n} par changed unexpectedly"
            assert holes[n].yards == 400, f"hole {n} yards changed unexpectedly"

        client.delete(f"/courses/{self._NAME}")
```

- [ ] **Step 2: Run the salvaged test**

Run: `cd backend && venv/bin/python -m pytest tests/unit/routers/test_courses_router.py::TestUpdateCoursePreservesHoles -v`
Expected: PASS.

**If it FAILS:** do not edit the test to match. A failure means either the partial-update behavior regressed or the endpoint semantics changed since the original fix. Stop and report — read `backend/app/routers/courses.py:343` (`update_course`) to see whether it does a partial merge or a full replace, and surface the finding. The salvaged test encodes the intended behavior.

- [ ] **Step 3: Commit**

```bash
cd /Users/stuart.gano/Documents/wolf-goat-pig
git add backend/tests/unit/routers/test_courses_router.py
git commit -m "test(courses): salvage partial hole-update regression from root tests

Updating one hole via PUT /courses/{name} must preserve the others.
Ported from the legacy root tests/test_hole_update_fix.py as a proper
in-process TestClient test.

Co-authored-by: Isaac"
```

---

## Task 2: Salvage the sheet-sync partial-failure regression

The bug: `SheetIntegrationService.sync_sheet_data_to_database` uses a per-row savepoint (`begin_nested`) so one bad row must not abort the whole transaction — valid players still persist. Source: `tests/integration/test_sheet_sync_fix.py` (a print/`return`-based script, not a real pytest test). No backend test covers this. It drives the service directly, so it belongs in `backend/tests/unit/services/`.

**Files:**
- Create: `backend/tests/unit/services/test_sheet_integration_service.py`

- [ ] **Step 1: Create the service test**

Create `backend/tests/unit/services/test_sheet_integration_service.py`:

```python
"""Unit test for SheetIntegrationService transaction isolation.

Regression (salvaged from root tests/integration/test_sheet_sync_fix.py):
a single invalid row must not abort the whole sheet sync — valid players
on either side of the bad row still persist (per-row savepoints).
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, PlayerProfile
from app.services.sheet_integration_service import SheetIntegrationService

TEST_DATABASE_URL = "sqlite:///./test_sheet_integration.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_one_bad_row_does_not_abort_the_sync(db):
    sheet_data = [
        {
            "Player Name": "Sync Player 1",
            "Games Played": "10",
            "Games Won": "5",
            "Total Earnings": "$100.00",
        },
        {
            "Player Name": "Sync Player 2",
            "Games Played": "invalid_data",  # forces a row-level error
            "Games Won": "3",
            "Total Earnings": "$50.00",
        },
        {
            "Player Name": "Sync Player 3",
            "Games Played": "15",
            "Games Won": "8",
            "Total Earnings": "$200.00",
        },
    ]

    service = SheetIntegrationService(db)
    mappings = service.create_column_mappings(list(sheet_data[0].keys()))
    results = service.sync_sheet_data_to_database(sheet_data, mappings)

    # The bad row is reported, not swallowed silently...
    assert len(results["errors"]) >= 1
    # ...and the two valid players on either side of it still persist.
    assert db.query(PlayerProfile).filter_by(name="Sync Player 1").first() is not None
    assert db.query(PlayerProfile).filter_by(name="Sync Player 3").first() is not None
```

- [ ] **Step 2: Run the salvaged test**

Run: `cd backend && venv/bin/python -m pytest tests/unit/services/test_sheet_integration_service.py -v`
Expected: PASS.

**If it FAILS:** check whether `validate_sheet_row` actually rejects `"invalid_data"` for Games Played (it must produce a row error) and that `sync_sheet_data_to_database` keys match (`errors`, and persisted `PlayerProfile`). Read `backend/app/services/sheet_integration_service.py:258`. Report rather than weakening the assertions.

- [ ] **Step 3: Commit**

```bash
cd /Users/stuart.gano/Documents/wolf-goat-pig
git add backend/tests/unit/services/test_sheet_integration_service.py
git commit -m "test(sheet-sync): salvage partial-failure regression from root tests

One invalid row must not abort the whole sync; valid players still
persist (per-row savepoints). Ported from the legacy root
tests/integration/test_sheet_sync_fix.py as a real pytest service test.

Co-authored-by: Isaac"
```

---

## Task 3: Relocate the BDD suite under backend/

Move the runnable behave suite to `backend/tests/bdd/`, fix the repo-root path math, document it as non-CI, and repoint the runner script.

**Files:**
- Move: `tests/bdd/` → `backend/tests/bdd/` (4 files: `environment.py`, `behave/steps/game_rules_steps.py`, `behave/steps/utils/__init__.py`, `behave/features/game_rules_core.feature`)
- Modify: `backend/tests/bdd/environment.py` (path depth `parents[2]` → `parents[3]`)
- Modify: `scripts/testing/run_behave.sh` (path `tests/bdd/behave` → `backend/tests/bdd/behave`)
- Create: `backend/tests/bdd/README.md`

- [ ] **Step 1: Move the BDD tree with git (preserves history)**

```bash
cd /Users/stuart.gano/Documents/wolf-goat-pig
mkdir -p backend/tests/bdd
git add tests/bdd  # stage the pre-existing modifications so git mv is clean
git mv tests/bdd/environment.py            backend/tests/bdd/environment.py
git mv tests/bdd/behave                    backend/tests/bdd/behave
find backend/tests/bdd -type f | sort
```

Expected: `backend/tests/bdd/environment.py`, `backend/tests/bdd/behave/steps/game_rules_steps.py`, `backend/tests/bdd/behave/steps/utils/__init__.py`, `backend/tests/bdd/behave/features/game_rules_core.feature`.

- [ ] **Step 2: Fix the repo-root path depth in environment.py**

`environment.py` moved one directory deeper (`tests/bdd/` → `backend/tests/bdd/`), so the repo root is now 3 parents up, not 2. Use the Edit tool to change exactly this line:

```python
    repo_root = Path(__file__).resolve().parents[2]
```
to:
```python
    repo_root = Path(__file__).resolve().parents[3]
```

- [ ] **Step 3: Repoint the behave runner script**

Use the Edit tool on `scripts/testing/run_behave.sh` to change exactly:

```bash
echo "🚀 Running Behave against tests/bdd/behave"
behave tests/bdd/behave "$@"
```
to:
```bash
echo "🚀 Running Behave against backend/tests/bdd/behave"
behave backend/tests/bdd/behave "$@"
```

- [ ] **Step 4: Document the layer**

Create `backend/tests/bdd/README.md`:

```markdown
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
```

- [ ] **Step 5: Verify behave still discovers features + steps**

Run: `backend/venv/bin/python -m behave backend/tests/bdd/behave --dry-run 2>&1 | tail -15`
Expected: behave parses `game_rules_core.feature` and matches steps with **no undefined-step or import errors** (a `--dry-run` does not need a live backend). If `behave` isn't in the venv: `backend/venv/bin/pip install -r backend/requirements-testing.txt` first.

- [ ] **Step 6: Commit**

```bash
cd /Users/stuart.gano/Documents/wolf-goat-pig
git add backend/tests/bdd scripts/testing/run_behave.sh
git commit -m "test(bdd): relocate behave suite to backend/tests/bdd

Single test home. Fix repo-root path depth (parents[2]->[3]), repoint
run_behave.sh, and document it as an explicit non-CI e2e layer.

Co-authored-by: Isaac"
```

---

## Task 4: Delete the legacy smoke scripts, print-demos, and root conftest

These are live-server smoke scripts and print-demos with no real in-process assertions; their topics are already covered by backend router/engine tests. The root conftest goes too (its `.ctk` wiring is now redundant with backend's `pythonpath`).

**Files (delete):**
- `tests/test_monte_carlo_api.py`
- `tests/integration/test_monte_carlo.py`
- `tests/integration/test_deployment.py`
- `tests/integration/test_course_import.py`
- `tests/integration/functional_test_suite.py`
- `tests/integration/simple_course_test.py`
- `tests/integration/test_course_enhancements.py`
- `tests/integration/test_multi_hole_tracking.py`
- `tests/test_hole_update_fix.py` (salvaged in Task 1)
- `tests/integration/test_sheet_sync_fix.py` (salvaged in Task 2)
- `tests/conftest.py`

- [ ] **Step 1: Remove the files and the now-empty tree**

```bash
cd /Users/stuart.gano/Documents/wolf-goat-pig
git rm tests/test_monte_carlo_api.py \
       tests/test_hole_update_fix.py \
       tests/conftest.py \
       tests/integration/test_monte_carlo.py \
       tests/integration/test_deployment.py \
       tests/integration/test_course_import.py \
       tests/integration/functional_test_suite.py \
       tests/integration/simple_course_test.py \
       tests/integration/test_course_enhancements.py \
       tests/integration/test_multi_hole_tracking.py \
       tests/integration/test_sheet_sync_fix.py
# Remove any leftover empty dirs / caches the root tree carried.
rm -rf tests
git status --short tests 2>/dev/null
```

Expected: all listed files staged as deletions; the `tests/` directory no longer exists at the repo root.

- [ ] **Step 2: Confirm nothing references the deleted root suite**

Run:
```bash
cd /Users/stuart.gano/Documents/wolf-goat-pig
grep -rn "tests/integration/test_\|tests/test_monte_carlo\|tests/test_hole_update\|tests/conftest" \
  .github scripts docker-compose.yml backend/Dockerfile 2>/dev/null | grep -v node_modules
```
Expected: no output. (CI's `pytest tests/` runs from `backend/`, so it refers to `backend/tests`, not the root tree — confirm by reading `.github/workflows/backend-ci.yml` line ~84 if unsure.)

- [ ] **Step 3: Commit**

```bash
cd /Users/stuart.gano/Documents/wolf-goat-pig
git commit -m "test: remove legacy root tests/ tree

Live-server smoke scripts + print-demos with no in-process assertions;
topics already covered by backend router/engine tests. Real regressions
were salvaged (Tasks 1-2) and the BDD suite relocated (Task 3). Single
test home is now backend/tests/.

Co-authored-by: Isaac"
```

---

## Task 5: Collapse the requirements + venv story

`requirements-local.txt` only adds `httpx` (already in `requirements.txt`) — redundant. `backend/Dockerfile` references it and must be repointed first. Document the single venv setup.

**Files:**
- Modify: `backend/Dockerfile` (drop the `requirements-local.txt` reference)
- Delete: `backend/requirements-local.txt`
- Modify: `CLAUDE.md` (document the one venv/install)

- [ ] **Step 1: Inspect how the Dockerfile uses requirements-local.txt**

Run: `grep -n "requirements" backend/Dockerfile`
Expected: shows the `COPY`/`pip install` lines. Note whether `requirements-local.txt` is installed or only copied.

- [ ] **Step 2: Repoint the Dockerfile**

Use the Edit tool to remove the `requirements-local.txt` reference. If the line installs all three, e.g.:
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt -r requirements-local.txt
```
change it to:
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```
If `requirements-local.txt` is referenced on its own `COPY`/`RUN` line, delete that line. (Match the actual contents found in Step 1 — do not invent lines.)

- [ ] **Step 3: Delete the redundant requirements file**

```bash
cd /Users/stuart.gano/Documents/wolf-goat-pig
git rm backend/requirements-local.txt
```

- [ ] **Step 4: Document the single venv setup in CLAUDE.md**

In `CLAUDE.md`, under the `## Build & Test` section, use the Edit tool to insert this block immediately before the `# Backend` comment line in the build/test fence:

```bash
# Backend env (one venv — `backend/venv`; do NOT use backend/.venv):
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-testing.txt
```

- [ ] **Step 5: Verify the Docker build still resolves deps (build context only, no full image needed)**

Run: `grep -n "requirements" backend/Dockerfile`
Expected: only `requirements.txt` (and optionally `requirements-testing.txt`) remain — no `requirements-local.txt`.

- [ ] **Step 6: Commit**

```bash
cd /Users/stuart.gano/Documents/wolf-goat-pig
git add backend/Dockerfile CLAUDE.md
git commit -m "chore(deps): drop redundant requirements-local.txt; document one venv

requirements-local.txt only re-listed httpx (already in requirements.txt).
Repoint Dockerfile and document the single backend/venv setup.

Co-authored-by: Isaac"
```

---

## Task 6: Remove the broken local venv (manual, not committed)

`backend/.venv` (90 pkgs, missing `resend`, cannot import `app.main`) is gitignored — local only. This step is a local cleanup, nothing to commit.

- [ ] **Step 1: Remove it**

```bash
cd /Users/stuart.gano/Documents/wolf-goat-pig
rm -rf backend/.venv
ls -d backend/.venv 2>&1 | tail -1
```
Expected: `No such file or directory`. `backend/venv` remains the only venv.

---

## Task 7: Full verification and PR

- [ ] **Step 1: Run the whole backend suite (the CI gate, exact flags)**

Run:
```bash
cd backend && venv/bin/python -m pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic -q 2>&1 | tail -8
```
Expected: green, and the count is the Pre-flight baseline **+2** (the two salvaged tests). No collection errors.

- [ ] **Step 2: Confirm the `.ctk` single wiring point still resolves**

Run:
```bash
cd backend && venv/bin/python -m pytest tests/unit/routers/test_games_players_router.py -k persists -q 2>&1 | tail -3
```
Expected: PASS (4 passed) — `from ctk import ...` still resolves via backend `pythonpath`.

- [ ] **Step 3: Confirm the consolidation invariants**

Run:
```bash
cd /Users/stuart.gano/Documents/wolf-goat-pig
test ! -d tests && echo "OK: no repo-root tests/" || echo "FAIL: root tests/ still present"
test ! -e backend/requirements-local.txt && echo "OK: requirements-local gone" || echo "FAIL"
grep -rn "requirements-local" backend/Dockerfile && echo "FAIL: stale Dockerfile ref" || echo "OK: no Dockerfile ref"
test -d backend/tests/bdd/behave/features && echo "OK: BDD relocated" || echo "FAIL"
```
Expected: four `OK:` lines.

- [ ] **Step 4: Lint/format the changed backend test files (mirror CI)**

Run:
```bash
cd backend && ruff check tests/ && ruff format --check tests/ 2>&1 | tail -5
```
Expected: clean. If `ruff format --check` flags the new files, run `ruff format tests/` and amend the relevant commit.

- [ ] **Step 5: Push and open the PR**

```bash
cd /Users/stuart.gano/Documents/wolf-goat-pig
git push -u origin chore/test-infra-consolidation
gh pr create --title "chore: consolidate to one test infrastructure" --body "$(cat <<'EOF'
## Summary
Collapse the two divergent test trees into a single backend/-rooted suite.

- Salvage two real regressions from the legacy root tests/ into proper
  in-process tests (course partial hole-update; sheet-sync partial-failure).
- Relocate the behave BDD suite to backend/tests/bdd/ as a documented,
  explicitly non-CI e2e layer (fixed path math, repointed runner).
- Delete legacy live-server smoke scripts and print-demos (topics already
  covered by backend router/engine tests).
- Drop redundant requirements-local.txt (repoint Dockerfile); document the
  single backend/venv setup.

Spec: docs/superpowers/specs/2026-06-14-test-infra-consolidation-design.md

## Test plan
- [ ] backend suite green at baseline+2 (two salvaged tests)
- [ ] `from ctk import` still resolves (single wiring point)
- [ ] no repo-root tests/, no requirements-local.txt, BDD relocated
- [ ] ruff check + format clean

This pull request and its description were written by Isaac.
EOF
)"
```
Expected: PR created. CI (`backend-ci.yml`, `frontend-ci.yml`) runs and is green.

---

## Notes for the implementer

- **Never weaken a salvaged assertion to make it pass.** Tasks 1 and 2 each include an "If it FAILS" clause — a failure is a real finding about current behavior, to be reported, not papered over.
- **The `.ctk/` directory is untracked** and was added in prior work; it is intentionally kept and wired only via `backend/pyproject.toml`'s `pythonpath`. Do not delete it.
- **Pre-existing `M` files** in the working tree (service-worker.js, version.json, several test files, conftest.py) are unrelated to this work — leave them alone; commit only the files each task names.
