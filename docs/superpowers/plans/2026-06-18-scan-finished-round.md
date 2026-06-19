# Scan a Finished Round — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a standalone "scan a finished round" path so a completed Wolf Goat Pig scorecard photo can be recorded as a round (mapped to roster players) without going through the live game/join-code flow.

**Architecture:** A new `POST /games/from-scorecard` endpoint builds a *completed* `GameStateModel` (players + per-hole `points_delta`) from scan output and persists `GameRecord`/`GamePlayerResult` via a helper extracted from the existing `/{game_id}/complete`. The frontend `/scorecard-scan` page gains a "new round" mode that, after scanning, lets the user map each scanned name to a roster player and save through the new endpoint.

**Tech Stack:** FastAPI + SQLAlchemy (backend), React + Vitest (frontend), Groq Vision (existing scan).

## Global Constraints

- Players per round must be 4, 5, or 6 (copied from `/games/create`).
- Backend persistence must work on both SQLite (tests/dev) and PostgreSQL (prod): the `jsonb` cast in raw-SQL inserts is Postgres-only and must be applied conditionally on `db.bind.dialect.name == "postgresql"`.
- Non-zero-sum holes are **warned, not rejected** — never block save on them.
- Course defaults to `"Wing Point"`, date (`played_at`) defaults to today (`YYYY-MM-DD`).
- A scanned name with no roster match is allowed ("keep as typed", `player_profile_id = null`).
- No GHIN posting on the new-round path.
- Pre-push gate: frontend `npm run typecheck && npx vitest run && npm run build`; backend `ruff check app/ tests/ && ruff format --check app/ tests/ && pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic`.

---

## File Structure

**Backend**
- Create `backend/app/services/completed_game_service.py` — pure `build_hole_history(...)`; dialect-aware `persist_completed_game(db, game)` (extracted from `mark_game_complete`).
- Modify `backend/app/routers/games.py` — `mark_game_complete` calls the helper; add `POST /from-scorecard` + its Pydantic request models.
- Create `backend/tests/unit/services/test_completed_game_service.py`
- Create `backend/tests/unit/routers/test_scorecard_round.py`

**Frontend**
- Modify `frontend/src/components/game/ScorecardReview.jsx` — add `mode`, player-mapping dropdowns, date field, warn-not-block on unbalanced, new `onConfirm` payload in new-round mode.
- Modify `frontend/src/components/game/ScorecardPhoto.jsx` — add `mode` prop, new-round save → `/games/from-scorecard`, skip GHIN, fix stale copy.
- Modify `frontend/src/pages/ScorecardScanPage.jsx` — two-action landing (new round vs. attach), pass roster + mode.
- Create `frontend/src/components/game/__tests__/ScorecardReview.newround.test.jsx`
- Create `frontend/src/components/game/__tests__/ScorecardPhoto.newround.test.jsx`

---

## Task 1: Pure `build_hole_history` helper

**Files:**
- Create: `backend/app/services/completed_game_service.py`
- Test: `backend/tests/unit/services/test_completed_game_service.py`

**Interfaces:**
- Produces: `build_hole_history(players: list[dict], per_hole_quarters: list[dict]) -> tuple[list[dict], dict]`
  - `players`: `[{"id": "p1", "name": "John", "player_profile_id": int | None}, ...]`
  - `per_hole_quarters`: `[{"player_index": 0, "hole": 1, "quarters": 2}, ...]`
  - returns `(hole_history, standings)` where `hole_history` is `[{"hole": 1, "points_delta": {"p1": 2, ...}}, ...]` for holes present, and `standings` is `{"p1": <sum of deltas>, ...}`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/unit/services/test_completed_game_service.py
from app.services.completed_game_service import build_hole_history


def test_build_hole_history_maps_indices_to_player_ids_and_sums_standings():
    players = [
        {"id": "p1", "name": "John", "player_profile_id": 1},
        {"id": "p2", "name": "Mary", "player_profile_id": None},
    ]
    per_hole = [
        {"player_index": 0, "hole": 1, "quarters": 2},
        {"player_index": 1, "hole": 1, "quarters": -2},
        {"player_index": 0, "hole": 2, "quarters": -1},
        {"player_index": 1, "hole": 2, "quarters": 1},
    ]
    hole_history, standings = build_hole_history(players, per_hole)

    assert hole_history == [
        {"hole": 1, "points_delta": {"p1": 2, "p2": -2}},
        {"hole": 2, "points_delta": {"p1": -1, "p2": 1}},
    ]
    assert standings == {"p1": 1, "p2": -1}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/unit/services/test_completed_game_service.py::test_build_hole_history_maps_indices_to_player_ids_and_sums_standings -v`
Expected: FAIL with `ModuleNotFoundError`/`ImportError` (function not defined).

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/services/completed_game_service.py
"""Build + persist a completed Wolf Goat Pig game.

Shared by the live game-completion endpoint and the scorecard-scan
"record a finished round" endpoint so both produce identical
GameRecord / GamePlayerResult rows.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def build_hole_history(
    players: list[dict[str, Any]],
    per_hole_quarters: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    """Convert per-(index, hole) quarter deltas into hole_history + standings.

    player_index refers to the position of the player in `players`.
    """
    id_by_index = {i: p["id"] for i, p in enumerate(players)}
    holes: dict[int, dict[str, float]] = {}
    for entry in per_hole_quarters:
        pid = id_by_index.get(entry["player_index"])
        if pid is None:
            continue
        holes.setdefault(entry["hole"], {})[pid] = entry["quarters"]

    hole_history = [
        {"hole": h, "points_delta": holes[h]} for h in sorted(holes)
    ]

    standings: dict[str, float] = {}
    for entry in hole_history:
        for pid, q in entry["points_delta"].items():
            standings[pid] = standings.get(pid, 0) + q
    return hole_history, standings
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/unit/services/test_completed_game_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/completed_game_service.py backend/tests/unit/services/test_completed_game_service.py
git commit -m "feat(backend): build_hole_history helper for completed-game persistence"
```

---

## Task 2: Extract dialect-aware `persist_completed_game` and reuse it in `/complete`

**Files:**
- Modify: `backend/app/services/completed_game_service.py`
- Modify: `backend/app/routers/games.py` (`mark_game_complete`, the block currently at ~lines 783–892)
- Test: `backend/tests/unit/services/test_completed_game_service.py`

**Interfaces:**
- Produces: `persist_completed_game(db: Session, game: GameStateModel) -> int`
  - Reads `game.state` (`players`, `hole_history`, `hole_quarters`, `standings`), writes a `GameRecord` (if absent) + one `GamePlayerResult` per player, returns `results_created`.
  - Idempotent: skips a `GamePlayerResult` that already exists for `(game_record_id, player_name)`.
  - Dialect-aware: only wraps JSON params in `CAST(... AS jsonb)` on PostgreSQL.

**Background:** The current insert uses `CAST(:hs AS jsonb)` unconditionally. On SQLite `jsonb` has no affinity and corrupts the JSON, so the helper must branch on dialect. This is exactly the existing logic from `mark_game_complete`, lifted into the helper.

- [ ] **Step 1: Write the failing test (runs on SQLite)**

```python
# append to backend/tests/unit/services/test_completed_game_service.py
import json
import uuid

from app import models
from app.database import SessionLocal, engine
from app.services.completed_game_service import build_hole_history, persist_completed_game


def _session():
    models.Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_persist_completed_game_writes_record_and_results_on_sqlite():
    db = _session()
    try:
        players = [
            {"id": "p1", "name": "Alice", "player_profile_id": None, "handicap": 10},
            {"id": "p2", "name": "Bob", "player_profile_id": None, "handicap": 8},
            {"id": "p3", "name": "Cara", "player_profile_id": None, "handicap": 12},
            {"id": "p4", "name": "Dan", "player_profile_id": None, "handicap": 6},
        ]
        per_hole = []
        for h in range(1, 19):
            per_hole += [
                {"player_index": 0, "hole": h, "quarters": 1},
                {"player_index": 1, "hole": h, "quarters": 1},
                {"player_index": 2, "hole": h, "quarters": -1},
                {"player_index": 3, "hole": h, "quarters": -1},
            ]
        hole_history, standings = build_hole_history(players, per_hole)
        game_id = str(uuid.uuid4())
        game = models.GameStateModel(
            game_id=game_id,
            game_status="completed",
            state={
                "players": players,
                "hole_history": hole_history,
                "hole_quarters": {str(h): {} for h in range(1, 19)},
                "standings": standings,
                "course_name": "Wing Point",
            },
            created_at="2026-06-18T00:00:00",
            updated_at="2026-06-18T00:00:00",
        )
        db.add(game)
        db.commit()

        created = persist_completed_game(db, game)
        assert created == 4

        rec = db.query(models.GameRecord).filter(models.GameRecord.game_id == game_id).first()
        assert rec is not None
        assert rec.player_count == 4

        rows = db.execute(
            text("SELECT player_name, total_earnings, final_position, hole_scores "
                 "FROM game_player_results WHERE game_record_id = :rid ORDER BY final_position"),
            {"rid": rec.id},
        ).fetchall()
        assert len(rows) == 4
        # Alice/Bob each +18, ranked above Cara/Dan at -18
        top = rows[0]
        assert top.total_earnings == 18
        # hole_scores must round-trip as JSON, not be corrupted to 0
        assert json.loads(top.hole_scores)[0]["hole"] == 1
    finally:
        db.rollback()
        db.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/unit/services/test_completed_game_service.py::test_persist_completed_game_writes_record_and_results_on_sqlite -v`
Expected: FAIL with `ImportError` (`persist_completed_game` not defined).

- [ ] **Step 3: Implement `persist_completed_game`**

Add to `backend/app/services/completed_game_service.py` (import models lazily to avoid a circular import with the router):

```python
def persist_completed_game(db: Session, game: Any) -> int:
    """Write GameRecord + GamePlayerResult rows for a completed game.

    `game` is a GameStateModel whose `state` already contains players,
    hole_history, hole_quarters and standings. Idempotent on
    (game_record_id, player_name). Returns the number of results created.
    """
    from app import models  # local import: router imports this module
    from app.utils.time import utc_now  # match existing helper used in games.py

    state = game.state or {}
    players = state.get("players", [])
    hole_history = state.get("hole_history", [])
    hole_quarters = state.get("hole_quarters", {})

    standings = state.get("standings", {})
    if not standings and hole_history:
        for entry in hole_history:
            for pid, q in entry.get("points_delta", {}).items():
                standings[pid] = standings.get(pid, 0) + q

    now = utc_now().isoformat()
    is_pg = db.bind.dialect.name == "postgresql"
    hs_expr = "CAST(:hs AS jsonb)" if is_pg else ":hs"
    pm_expr = "CAST(:pm AS jsonb)" if is_pg else ":pm"

    record = db.query(models.GameRecord).filter(models.GameRecord.game_id == game.game_id).first()
    if not record:
        record = models.GameRecord(
            game_id=game.game_id,
            course_name=state.get("course_name", "Wing Point"),
            game_mode="wolf_goat_pig",
            player_count=len(players),
            total_holes_played=len(hole_quarters) or len(hole_history),
            created_at=game.created_at or now,
            completed_at=now,
            final_scores=standings,
        )
        db.add(record)
        db.flush()
    record_id = record.id

    player_hole_data: dict[str, list] = {}
    for entry in hole_history:
        for pid, quarters in entry.get("points_delta", {}).items():
            player_hole_data.setdefault(pid, []).append({
                "hole": entry.get("hole"),
                "quarters": quarters,
                "gross_score": (entry.get("gross_scores") or {}).get(pid),
                "teams": entry.get("teams"),
                "wager": entry.get("wager"),
                "phase": entry.get("phase"),
            })

    sorted_players = sorted(players, key=lambda p: standings.get(p.get("id"), 0), reverse=True)
    results_created = 0
    for rank, player in enumerate(sorted_players, 1):
        pid = player.get("id")
        player_name = player.get("name", "Unknown")
        total_earnings = standings.get(pid, 0)
        holes_data = player_hole_data.get(pid, [])
        holes_won = sum(1 for h in holes_data if h.get("quarters", 0) > 0)

        exists = db.execute(
            text("SELECT 1 FROM game_player_results WHERE game_record_id = :rid AND player_name = :pn LIMIT 1"),
            {"rid": record_id, "pn": player_name},
        ).first()
        if exists:
            continue

        perf = json.dumps({
            "handicap": player.get("handicap"),
            "holes_played": len(holes_data),
            "avg_quarters_per_hole": round(total_earnings / max(len(holes_data), 1), 2),
        })
        db.execute(
            text(f"""
                INSERT INTO game_player_results
                    (game_record_id, player_profile_id, player_name,
                     final_position, total_earnings, holes_won,
                     hole_scores, performance_metrics, created_at)
                VALUES
                    (:rid, :pid, :pname, :pos, :earn, :hw,
                     {hs_expr}, {pm_expr}, :cat)
            """),
            {
                "rid": record_id,
                "pid": player.get("player_profile_id"),
                "pname": player_name,
                "pos": rank,
                "earn": total_earnings,
                "hw": holes_won,
                "hs": json.dumps(holes_data),
                "pm": perf,
                "cat": now,
            },
        )
        results_created += 1

    db.commit()
    logger.info("Persisted completed game %s: %d results", game.game_id, results_created)
    return results_created
```

Verify the `utc_now` import path matches `games.py` (search `from .* import utc_now` in `backend/app/routers/games.py` and reuse the same module path).

- [ ] **Step 4: Run the service test to verify it passes**

Run: `cd backend && pytest tests/unit/services/test_completed_game_service.py -v`
Expected: PASS (both tests).

- [ ] **Step 5: Refactor `mark_game_complete` to call the helper**

In `backend/app/routers/games.py`, inside `mark_game_complete`, replace the persistence block (from `now = utc_now().isoformat()` / `existing_record = ...` through `results_created = ...` and the achievements call) so that after it sets `game.game_status="completed"`, updates `state`, and `flag_modified(game, "state")`, it does:

```python
        from ..services.completed_game_service import persist_completed_game

        results_created = persist_completed_game(db, game)
        _check_game_achievements(db, game_id, db.query(models.GameRecord)
                                .filter(models.GameRecord.game_id == game_id).first().id)
```

Keep the existing `return {...}` and the surrounding `try/except`. Remove the now-duplicated inline persistence code. Do NOT change the early-return behavior for already-completed games.

- [ ] **Step 6: Run existing completion tests to verify no regression**

Run: `cd backend && pytest tests/unit/routers/test_games_holes_router.py tests/unit/routers/test_leaderboard_router.py -v`
Expected: PASS (no behavior change for `/complete`).

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/completed_game_service.py backend/app/routers/games.py backend/tests/unit/services/test_completed_game_service.py
git commit -m "refactor(backend): extract dialect-aware persist_completed_game; reuse in /complete"
```

---

## Task 3: `POST /games/from-scorecard` endpoint

**Files:**
- Modify: `backend/app/routers/games.py` (add models + route near `/create`, ~line 138)
- Test: `backend/tests/unit/routers/test_scorecard_round.py`

**Interfaces:**
- Consumes: `build_hole_history`, `persist_completed_game` (Task 1–2).
- Produces: `POST /games/from-scorecard` → `{"game_id": str, "status": "completed", "warnings": {...}}`.
  - Request body (Pydantic): `ScorecardRoundRequest`:
    - `players: list[ScorecardRoundPlayer]` where `ScorecardRoundPlayer = {name: str, player_profile_id: int | None = None}`
    - `per_hole_quarters: list[ScorecardRoundHoleQuarter]` where each = `{player_index: int, hole: int, quarters: float}`
    - `course_name: str | None = None`
    - `played_at: str | None = None`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/unit/routers/test_scorecard_round.py
from fastapi.testclient import TestClient

from app import models
from app.database import SessionLocal, engine
from app.main import app

client = TestClient(app)


def _per_hole_4p():
    out = []
    for h in range(1, 19):
        out += [
            {"player_index": 0, "hole": h, "quarters": 1},
            {"player_index": 1, "hole": h, "quarters": 1},
            {"player_index": 2, "hole": h, "quarters": -1},
            {"player_index": 3, "hole": h, "quarters": -1},
        ]
    return out


def test_from_scorecard_creates_completed_round_and_results():
    models.Base.metadata.create_all(bind=engine)
    body = {
        "players": [
            {"name": "Alice"}, {"name": "Bob"}, {"name": "Cara"}, {"name": "Dan"},
        ],
        "per_hole_quarters": _per_hole_4p(),
        "course_name": "Wing Point",
        "played_at": "2026-06-18",
    }
    resp = client.post("/games/from-scorecard", json=body)
    assert resp.status_code == 200, resp.text
    game_id = resp.json()["game_id"]

    db = SessionLocal()
    try:
        game = db.query(models.GameStateModel).filter_by(game_id=game_id).first()
        assert game.game_status == "completed"
        rec = db.query(models.GameRecord).filter_by(game_id=game_id).first()
        assert rec is not None and rec.player_count == 4
    finally:
        db.close()


def test_from_scorecard_rejects_wrong_player_count():
    body = {"players": [{"name": "A"}, {"name": "B"}, {"name": "C"}],
            "per_hole_quarters": []}
    resp = client.post("/games/from-scorecard", json=body)
    assert resp.status_code == 400


def test_from_scorecard_allows_non_zero_sum_hole():
    pq = _per_hole_4p()
    pq[0]["quarters"] = 5  # break hole 1 zero-sum
    body = {"players": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}],
            "per_hole_quarters": pq}
    resp = client.post("/games/from-scorecard", json=body)
    assert resp.status_code == 200
    assert 1 in {int(h) for h in resp.json().get("warnings", {})}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/unit/routers/test_scorecard_round.py -v`
Expected: FAIL with 404 (route not defined).

- [ ] **Step 3: Implement the endpoint**

In `backend/app/routers/games.py`, add Pydantic models near the top imports/models and the route after `/create`:

```python
from pydantic import BaseModel  # if not already imported


class ScorecardRoundPlayer(BaseModel):
    name: str
    player_profile_id: int | None = None


class ScorecardRoundHoleQuarter(BaseModel):
    player_index: int
    hole: int
    quarters: float


class ScorecardRoundRequest(BaseModel):
    players: list[ScorecardRoundPlayer]
    per_hole_quarters: list[ScorecardRoundHoleQuarter]
    course_name: str | None = None
    played_at: str | None = None


@router.post("/from-scorecard")
async def create_round_from_scorecard(
    body: ScorecardRoundRequest,
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """Record a completed round straight from a scanned scorecard.

    Builds a completed game (players + per-hole quarters) and persists the
    same GameRecord/GamePlayerResult rows a live-scored game would, so a
    scanned round shows up in standings/history identically.
    """
    import uuid

    from ..services.completed_game_service import build_hole_history, persist_completed_game

    if len(body.players) not in (4, 5, 6):
        raise HTTPException(status_code=400, detail="Wolf Goat Pig requires 4, 5, or 6 players")

    # Assign stable ids; resolve profile from canonical legacy_name when absent.
    players: list[dict[str, Any]] = []
    for i, p in enumerate(body.players):
        profile_id = p.player_profile_id
        if profile_id is None:
            prof = (
                db.query(models.PlayerProfile)
                .filter(models.PlayerProfile.legacy_name == p.name)
                .first()
            )
            profile_id = prof.id if prof else None
        players.append({
            "id": f"p{i + 1}",
            "name": p.name,
            "player_profile_id": profile_id,
            "handicap": 18.0,
        })

    per_hole = [q.model_dump() for q in body.per_hole_quarters]
    hole_history, standings = build_hole_history(players, per_hole)

    # Warn (do not reject) on holes whose deltas don't sum to zero.
    warnings: dict[str, float] = {}
    for entry in hole_history:
        s = sum(entry["points_delta"].values())
        if abs(s) > 0.001:
            warnings[str(entry["hole"])] = s

    try:
        now = utc_now().isoformat()
        created_at = (body.played_at + "T12:00:00") if body.played_at else now
        game_id = str(uuid.uuid4())
        game = models.GameStateModel(
            game_id=game_id,
            game_status="completed",
            state={
                "game_status": "completed",
                "course_name": body.course_name or "Wing Point",
                "player_count": len(players),
                "players": players,
                "hole_history": hole_history,
                "hole_quarters": {str(e["hole"]): e["points_delta"] for e in hole_history},
                "standings": standings,
                "source": "scorecard_scan",
            },
            created_at=created_at,
            updated_at=now,
        )
        db.add(game)
        db.flush()
        persist_completed_game(db, game)
        return {"game_id": game_id, "status": "completed", "warnings": warnings}
    except Exception as e:
        db.rollback()
        logger.error(f"from-scorecard failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record round: {e!s}")
```

Confirm `logger`, `utc_now`, `database`, `models`, `HTTPException`, `Depends` are already imported in `games.py` (they are, used elsewhere in the file). Add `from pydantic import BaseModel` only if not present.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/unit/routers/test_scorecard_round.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Lint + commit**

```bash
cd backend && ruff check app/ tests/ && ruff format app/routers/games.py app/services/completed_game_service.py tests/unit/routers/test_scorecard_round.py
git add backend/app/routers/games.py backend/tests/unit/routers/test_scorecard_round.py
git commit -m "feat(backend): POST /games/from-scorecard records a round from a scanned scorecard"
```

---

## Task 4: `ScorecardReview` new-round mode (player mapping + date + warn-not-block)

**Files:**
- Modify: `frontend/src/components/game/ScorecardReview.jsx`
- Test: `frontend/src/components/game/__tests__/ScorecardReview.newround.test.jsx`

**Interfaces:**
- Consumes: roster names via prop `rosterNames: string[]` (fetched by the page).
- Produces: when `mode === "new-round"`, `onConfirm({ players: [{name, player_profile_id: null}], per_hole_quarters: [{player_index, hole, quarters}], played_at: "YYYY-MM-DD" })`. When `mode` is omitted/`"attach"`, keep today's `onConfirm(quartersByHole)` (name-keyed) behavior unchanged.
- New props: `mode = "attach"`, `rosterNames = []`.

**Behavior changes for new-round mode only:**
- Render a mapping `<select>` per extracted player, options = `rosterNames` plus a "Keep as typed (unlinked)" option; default selection = the closest roster name by case-insensitive substring/`startsWith` match, else "keep as typed".
- Render a date `<input type="date">` defaulting to today (`new Date().toISOString().slice(0,10)`).
- `canConfirm` requires `allFilled` but does NOT require zero-sum (unbalanced holes show the existing warning banner but Save stays enabled). In attach mode, keep the existing `allFilled && unbalancedHoles.length === 0`.

- [ ] **Step 1: Write the failing test**

```jsx
// frontend/src/components/game/__tests__/ScorecardReview.newround.test.jsx
import React from 'react';
import { describe, test, expect, vi } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import ScorecardReview from '../ScorecardReview';

const extraction = {
  players: [{ name: 'Jon', confidence: 0.9 }, { name: 'Mary', confidence: 0.9 }],
  running_totals: (() => {
    const t = [];
    for (let h = 1; h <= 18; h++) {
      t.push({ player_index: 0, hole: h, value: h, confidence: 1 });
      t.push({ player_index: 1, hole: h, value: -h, confidence: 1 });
    }
    return t;
  })(),
};

test('new-round mode maps names to roster and confirms profile-less payload', () => {
  const onConfirm = vi.fn();
  render(
    <ScorecardReview
      extraction={extraction}
      players={[]}
      mode="new-round"
      rosterNames={['Jon Smith', 'Mary Jones']}
      onConfirm={onConfirm}
      onCancel={() => {}}
    />,
  );
  // default fuzzy match selects "Jon Smith" for "Jon"
  const selects = screen.getAllByRole('combobox');
  expect(selects[0].value).toBe('Jon Smith');

  fireEvent.click(screen.getByRole('button', { name: /confirm/i }));
  expect(onConfirm).toHaveBeenCalledTimes(1);
  const arg = onConfirm.mock.calls[0][0];
  expect(arg.players[0]).toEqual({ name: 'Jon Smith', player_profile_id: null });
  expect(arg.per_hole_quarters.find(q => q.player_index === 0 && q.hole === 1).quarters).toBe(1);
  expect(arg.played_at).toMatch(/^\d{4}-\d{2}-\d{2}$/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/components/game/__tests__/ScorecardReview.newround.test.jsx`
Expected: FAIL (no combobox / wrong onConfirm shape).

- [ ] **Step 3: Implement new-round mode**

In `ScorecardReview.jsx`:
1. Add props `mode = 'attach'`, `rosterNames = []`. Add `const isNewRound = mode === 'new-round';`.
2. Add a fuzzy default + mapping state:

```jsx
const bestRosterMatch = (name) => {
  const lower = (name || '').toLowerCase();
  return (
    rosterNames.find(r => r.toLowerCase() === lower) ||
    rosterNames.find(r => r.toLowerCase().startsWith(lower)) ||
    rosterNames.find(r => r.toLowerCase().includes(lower)) ||
    '__unlinked__'
  );
};
const [mapping, setMapping] = useState(() =>
  extractedPlayers.map(ep => bestRosterMatch(ep.name)),
);
const [playedAt, setPlayedAt] = useState(() => new Date().toISOString().slice(0, 10));
```

3. Render (only when `isNewRound`) above the table: a mapping row per player (`<select role="combobox">` with `rosterNames` options + a `value="__unlinked__"` "Keep as typed (unlinked)" option) and a `<input type="date" value={playedAt} ...>`.
4. Change `canConfirm`: `const canConfirm = allFilled && (isNewRound || unbalancedHoles.length === 0);`
5. Branch `handleConfirm`:

```jsx
const handleConfirm = () => {
  if (isNewRound) {
    const perHole = [];
    for (let pi = 0; pi < extractedPlayers.length; pi++) {
      for (let h = 1; h <= 18; h++) {
        perHole.push({ player_index: pi, hole: h, quarters: allDeltas[pi]?.[h] ?? 0 });
      }
    }
    onConfirm({
      players: extractedPlayers.map((ep, pi) => ({
        name: mapping[pi] === '__unlinked__' ? ep.name : mapping[pi],
        player_profile_id: null,
      })),
      per_hole_quarters: perHole,
      played_at: playedAt,
    });
    return;
  }
  // existing attach-mode payload (unchanged)
  const quartersByHole = {};
  /* ...existing code... */
  onConfirm(quartersByHole);
};
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/components/game/__tests__/ScorecardReview.newround.test.jsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/game/ScorecardReview.jsx frontend/src/components/game/__tests__/ScorecardReview.newround.test.jsx
git commit -m "feat(frontend): ScorecardReview new-round mode (roster mapping, date, warn-not-block)"
```

---

## Task 5: `ScorecardPhoto` new-round save path

**Files:**
- Modify: `frontend/src/components/game/ScorecardPhoto.jsx`
- Test: `frontend/src/components/game/__tests__/ScorecardPhoto.newround.test.jsx`

**Interfaces:**
- Consumes: `ScorecardReview` `mode`/`rosterNames`/new `onConfirm` payload (Task 4).
- New props: `mode = 'attach'`, `rosterNames = []`. In `'new-round'` mode `gameId` is unused.
- Produces: on confirm in new-round mode, `POST {API_URL}/games/from-scorecard` with `{ players, per_hole_quarters, played_at, course_name: 'Wing Point' }`; on success calls `onSaved(result)` (no GHIN modal).

- [ ] **Step 1: Write the failing test**

```jsx
// frontend/src/components/game/__tests__/ScorecardPhoto.newround.test.jsx
import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import ScorecardPhoto from '../ScorecardPhoto';

// Render directly into review by mocking ScorecardCapture to immediately
// hand back a file is overkill — instead drive handleConfirm via the review.
vi.mock('../ScorecardReview', () => ({
  default: ({ onConfirm }) => (
    <button onClick={() => onConfirm({
      players: [{ name: 'Jon Smith', player_profile_id: null }],
      per_hole_quarters: [{ player_index: 0, hole: 1, quarters: 1 }],
      played_at: '2026-06-18',
    })}>confirm</button>
  ),
}));
vi.mock('../ScorecardCapture', () => ({ default: () => <div /> }));
vi.mock('../GHINPostModal', () => ({ default: () => <div data-testid="ghin" /> }));

beforeEach(() => {
  global.fetch = vi.fn(async () => ({ ok: true, json: async () => ({ game_id: 'g1', status: 'completed' }) }));
});

test('new-round confirm POSTs to /games/from-scorecard and skips GHIN', async () => {
  const onSaved = vi.fn();
  render(
    <ScorecardPhoto mode="new-round" rosterNames={['Jon Smith']} players={[]} onSaved={onSaved} onCancel={() => {}} />,
  );
  // force into review stage
  // (ScorecardPhoto starts at 'capture'; expose review via initialStage prop — see Step 3)
  screen.getByText('confirm').click();
  await waitFor(() => expect(onSaved).toHaveBeenCalled());
  const [url, opts] = global.fetch.mock.calls[0];
  expect(url).toMatch(/\/games\/from-scorecard$/);
  expect(JSON.parse(opts.body).course_name).toBe('Wing Point');
  expect(screen.queryByTestId('ghin')).toBeNull();
});
```

> Note: ScorecardPhoto starts in `capture` stage. To make the review reachable in test without simulating a camera file, add an optional `initialStage` + `initialExtraction` prop (default `undefined`) used only to seed state; the mock review renders whenever `stage === 'review'`. Set them in the test render. Keep production behavior unchanged when the props are absent.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/components/game/__tests__/ScorecardPhoto.newround.test.jsx`
Expected: FAIL (posts to `/games/{id}/scores` or GHIN shows / review not reachable).

- [ ] **Step 3: Implement**

In `ScorecardPhoto.jsx`:
1. Add props `mode = 'attach'`, `rosterNames = []`, and test-seam props `initialStage`, `initialExtraction`. Initialize `useState(initialStage || 'capture')` and `useState(initialExtraction || null)`.
2. Pass `mode` and `rosterNames` to `<ScorecardReview ... mode={mode} rosterNames={rosterNames} />`.
3. Branch `handleConfirm`:

```jsx
const handleConfirm = async (payload) => {
  setStage('saving');
  setErrorMsg(null);
  try {
    if (mode === 'new-round') {
      const res = await fetch(`${API_URL}/games/from-scorecard`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...payload, course_name: 'Wing Point' }),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail || `Save failed: ${res.status}`);
      }
      const data = await res.json();
      onSaved(data);   // skip GHIN on this path
      return;
    }
    // existing attach-mode save to /games/{id}/scores (unchanged)
    /* ...existing holeQuarters → /games/${gameId}/scores ... */
  } catch (err) {
    setErrorMsg(err.message || 'Failed to save quarters');
    setStage('error');
  }
};
```

4. Fix stale copy: in the `processing` stage replace "Gemini is extracting the values." with "Reading the scorecard. This takes a few seconds."

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/components/game/__tests__/ScorecardPhoto.newround.test.jsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/game/ScorecardPhoto.jsx frontend/src/components/game/__tests__/ScorecardPhoto.newround.test.jsx
git commit -m "feat(frontend): ScorecardPhoto new-round save via /games/from-scorecard (no GHIN)"
```

---

## Task 6: `ScorecardScanPage` two-action landing + roster fetch

**Files:**
- Modify: `frontend/src/pages/ScorecardScanPage.jsx`

**Interfaces:**
- Consumes: `ScorecardPhoto` `mode`/`rosterNames` (Task 5).
- Behavior: landing shows two primary actions — **"Scan a finished round"** (sets `mode='new-round'`, renders `ScorecardPhoto` with no game, `rosterNames` fetched from `/legacy-players`) and **"Add to an active game"** (the existing game-picker flow, `mode='attach'`). On new-round save, show the existing success screen with a "Home" button (no "View Game" requirement, since a new game_id is returned — link to `/game/{game_id}` using the returned id).

- [ ] **Step 1: Add roster fetch + mode state**

Add near the existing `useState`s:

```jsx
const [mode, setMode] = useState(null); // null = landing, 'new-round', 'attach'
const [rosterNames, setRosterNames] = useState([]);

useEffect(() => {
  fetch(`${API_URL}/legacy-players`)
    .then(r => (r.ok ? r.json() : { players: [] }))
    .then(d => setRosterNames(d.players || []))
    .catch(() => {});
}, []);
```

- [ ] **Step 2: Render the landing choices**

Before the existing game-picker return, when `mode === null` render two buttons:
- "📷 Scan a finished round" → `onClick={() => setMode('new-round')}`
- "➕ Add to an active game" → `onClick={() => setMode('attach')}` (falls through to existing picker UI, which should now render only when `mode === 'attach'`).

- [ ] **Step 3: Render new-round mode**

When `mode === 'new-round'` and not `saved`, render:

```jsx
<ScorecardPhoto
  mode="new-round"
  rosterNames={rosterNames}
  players={[]}
  onSaved={(result) => { setSavedGameId(result?.game_id || null); setSaved(true); }}
  onCancel={() => setMode(null)}
/>
```

Add `const [savedGameId, setSavedGameId] = useState(null);` and in the success screen use `savedGameId || selectedGame?.game_id` for the "View Game" link. Keep the existing `selectedGame` attach flow rendering only when `mode === 'attach'`.

- [ ] **Step 4: Manual verification**

Run: `cd frontend && npx vitest run` then `npm run build`. Verify no import/lint errors. (Behavioral UI verified in Task 7.)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/ScorecardScanPage.jsx
git commit -m "feat(frontend): scorecard-scan landing offers 'scan a finished round' vs 'add to active game'"
```

---

## Task 7: Full gate + manual smoke

**Files:** none (verification only)

- [ ] **Step 1: Backend gate**

Run: `cd backend && ruff check app/ tests/ && ruff format --check app/ tests/ && pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic -q`
Expected: all pass.

- [ ] **Step 2: Frontend gate**

Run: `cd frontend && npm run typecheck && npx vitest run && npm run build`
Expected: all pass.

- [ ] **Step 3: Commit any formatting fixes, then hand off for push**

The user pushes (push to `main` auto-deploys). After deploy, smoke test: `/scorecard-scan` → "Scan a finished round" → photo → map names → confirm (try an intentionally unbalanced hole to confirm it warns but still saves) → verify the round appears under the game/standings.

---

## Self-Review

- **Spec coverage:** Two-action landing (Task 6) ✓; scan unchanged ✓; player mapping w/ fuzzy default + "keep as typed" (Task 4) ✓; editable date / Wing Point default (Tasks 4–5, endpoint) ✓; warn-not-block zero-sum (Task 4 UI + Task 3 endpoint) ✓; `/games/from-scorecard` + shared persist helper (Tasks 1–3) ✓; profile resolution from `legacy_name` (Task 3) ✓; skip GHIN (Task 5) ✓; standings/history parity via shared helper (Task 2) ✓; tests backend+frontend ✓.
- **Type consistency:** `build_hole_history(players, per_hole_quarters) -> (hole_history, standings)` used identically in Tasks 1/2/3; `persist_completed_game(db, game) -> int` used in Tasks 2/3; new-round `onConfirm({players, per_hole_quarters, played_at})` produced in Task 4, consumed in Task 5; endpoint payload adds `course_name` in Task 5, matches `ScorecardRoundRequest` in Task 3.
- **Placeholders:** none — every code step has real code; "...existing code..." markers refer to clearly-identified unchanged blocks in the named file.
- **Risk noted:** `utc_now` import path must match `games.py` (Task 2 Step 3 calls this out). Confirm `from pydantic import BaseModel` presence in `games.py` (Task 3 Step 3).
