# Persist Scorecard Photo + Backfill Per-Hole — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Save the scanned scorecard photo with the round and let users re-open it on any device to backfill the per-hole quarters, without changing the already-correct settle-up totals.

**Architecture:** Store a downscaled JPEG as base64 in a new `scorecard_image` column on `game_state`. `/games/from-scorecard` accepts an optional `image_base64`; `GET /games/{id}/scorecard-photo` serves it; `PATCH /games/{id}/scorecard` recomputes hole_history+standings from new per-hole and re-persists. Frontend sends the photo on save, shows a "📷 Photo" button (reusing the Part-A `ScorecardPhotoZoom` overlay) on the completed-round view (`SimpleScorekeeperPage`), and a "Fill in holes" editor that reuses the `ScorecardReview` grid.

**Tech Stack:** FastAPI + SQLAlchemy + Postgres/SQLite, React/Vitest, Pillow not needed (downscale is client-side canvas).

## Global Constraints

- Table is `game_state` (`GameStateModel.__tablename__`); `state` is a `MutableDict` JSON column (top-level reassignment required to mark dirty).
- New Postgres migration = a `*_postgres.sql` file in `backend/migrations/` (applied once at startup by `migrations_runner`; "already exists" tolerated). SQLite dev uses `create_all`.
- `image_base64` capped at ~2 MB; oversize/garbled → ignored, round still saves.
- Standings = sum of per-hole quarters (`build_hole_history` / `persist_completed_game` in `completed_game_service`). Backfill recompute MUST keep this identity; "locked totals" is a frontend warning only.
- Backend gate: `cd backend && venv/bin/python -m ruff check app/ tests/ && venv/bin/python -m ruff format --check app/ tests/ && venv/bin/python -m pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic`. Frontend gate: `cd frontend && npm run typecheck && npx vitest run && npm run build`. NEVER edit code containing `!` via shell heredoc/sed (zsh mangles it) — use Edit/Write.

---

## File Structure

- Modify `backend/app/models.py` — add `scorecard_image` column to `GameStateModel`.
- Create `backend/migrations/add_scorecard_image_postgres.sql`.
- Modify `backend/app/routers/games.py` — `image_base64` on `ScorecardRoundRequest` + store it; `GET /{id}/scorecard-photo`; `PATCH /{id}/scorecard`.
- Modify `backend/tests/unit/routers/test_scorecard_round.py` (and a new `test_scorecard_photo.py`) — endpoint tests.
- Modify `frontend/src/utils/scorecardImage.js` — add `downscaleToBase64`.
- Modify `frontend/src/components/game/ScorecardPhoto.jsx` — retain downscaled base64; send `image_base64` on the from-scorecard save.
- Modify `frontend/src/pages/SimpleScorekeeperPage.jsx` — "📷 Photo" button + "Fill in holes" editor entry (completed rounds).
- Create `frontend/src/components/game/ScorecardBackfill.jsx` — the fill-in editor (loads current per-hole, photo zoom, locked-total warn, PATCH save).
- Tests alongside each frontend unit.

---

## Task 1: `scorecard_image` column + migration

**Files:**
- Modify: `backend/app/models.py` (GameStateModel)
- Create: `backend/migrations/add_scorecard_image_postgres.sql`
- Test: `backend/tests/unit/test_models_scorecard_image.py`

**Interfaces:**
- Produces: `GameStateModel.scorecard_image: str | None` (Text column).

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/unit/test_models_scorecard_image.py
from app import models
from app.database import SessionLocal, engine


def test_game_state_has_scorecard_image_column():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        g = models.GameStateModel(game_id="img-col-test", game_status="completed", state={}, scorecard_image="data:image/jpeg;base64,AAAA")
        db.add(g)
        db.commit()
        row = db.query(models.GameStateModel).filter_by(game_id="img-col-test").first()
        assert row.scorecard_image == "data:image/jpeg;base64,AAAA"
    finally:
        db.query(models.GameStateModel).filter_by(game_id="img-col-test").delete()
        db.commit()
        db.close()
```

- [ ] **Step 2: Run to verify it fails** — `cd backend && venv/bin/python -m pytest tests/unit/test_models_scorecard_image.py -q` → FAIL (`'scorecard_image' is an invalid keyword argument` / column missing). The dev DB auto-heals via `ctk.dbreset` at session start; if run in isolation, `rm backend/wolf_goat_pig.db` first.

- [ ] **Step 3: Add the column.** In `backend/app/models.py`, in `GameStateModel` (after the `state` column), add — ensure `Text` is imported from sqlalchemy:

```python
    scorecard_image = Column(Text, nullable=True)  # downscaled JPEG as base64/data-URL for later per-hole backfill
```

- [ ] **Step 4: Create the Postgres migration** `backend/migrations/add_scorecard_image_postgres.sql`:

```sql
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS scorecard_image TEXT;
```

- [ ] **Step 5: Run to verify it passes** — `cd backend && venv/bin/python -m pytest tests/unit/test_models_scorecard_image.py -q` → PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/models.py backend/migrations/add_scorecard_image_postgres.sql backend/tests/unit/test_models_scorecard_image.py
git commit -m "feat(scorecard): scorecard_image column on game_state (+ pg migration)"
```

---

## Task 2: `/from-scorecard` accepts + stores `image_base64`

**Files:**
- Modify: `backend/app/routers/games.py` (`ScorecardRoundRequest`, `create_round_from_scorecard`)
- Test: `backend/tests/unit/routers/test_scorecard_round.py`

**Interfaces:**
- Consumes: `GameStateModel.scorecard_image` (Task 1).
- Produces: `ScorecardRoundRequest.image_base64: str | None`; the round row's `scorecard_image` is set when a valid, under-size image is sent.

- [ ] **Step 1: Write the failing test** (append to `test_scorecard_round.py`):

```python
def test_from_scorecard_stores_image_base64():
    models.Base.metadata.create_all(bind=engine)
    body = {
        "players": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}],
        "per_hole_quarters": _per_hole_4p(),
        "image_base64": "data:image/jpeg;base64,SGVsbG8=",
    }
    game_id = client.post("/games/from-scorecard", json=body).json()["game_id"]
    db = SessionLocal()
    try:
        row = db.query(models.GameStateModel).filter_by(game_id=game_id).first()
        assert row.scorecard_image == "data:image/jpeg;base64,SGVsbG8="
    finally:
        db.close()


def test_from_scorecard_ignores_oversize_image_but_still_saves():
    models.Base.metadata.create_all(bind=engine)
    body = {
        "players": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}],
        "per_hole_quarters": _per_hole_4p(),
        "image_base64": "x" * (2_000_001),  # over the 2MB ceiling
    }
    resp = client.post("/games/from-scorecard", json=body)
    assert resp.status_code == 200  # round still saved
    row = SessionLocal().query(models.GameStateModel).filter_by(game_id=resp.json()["game_id"]).first()
    assert row.scorecard_image is None
```

- [ ] **Step 2: Run to verify it fails** — `cd backend && venv/bin/python -m pytest tests/unit/routers/test_scorecard_round.py -k image -q` → FAIL.

- [ ] **Step 3: Implement.** In `ScorecardRoundRequest` add the field:

```python
    image_base64: str | None = None
```

In `create_round_from_scorecard`, after `game = models.GameStateModel(...)` is constructed (before/after `db.add(game)` but before commit), set the image when valid:

```python
        # Attach the photo for later per-hole backfill (best-effort; oversize ignored).
        if body.image_base64 and len(body.image_base64) <= 2_000_000:
            game.scorecard_image = body.image_base64
```

(Place this between `game = models.GameStateModel(...)` and `db.add(game)`.)

- [ ] **Step 4: Run to verify it passes** — `cd backend && venv/bin/python -m pytest tests/unit/routers/test_scorecard_round.py -q` → PASS (all, including the two new).

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/games.py backend/tests/unit/routers/test_scorecard_round.py
git commit -m "feat(scorecard): from-scorecard stores optional image_base64"
```

---

## Task 3: `GET /games/{id}/scorecard-photo`

**Files:**
- Modify: `backend/app/routers/games.py`
- Test: `backend/tests/unit/routers/test_scorecard_photo.py` (new)

**Interfaces:**
- Consumes: `GameStateModel.scorecard_image`.
- Produces: `GET /games/{game_id}/scorecard-photo` → `200` image bytes (`Response(content=..., media_type=...)`) or `404`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/unit/routers/test_scorecard_photo.py
import base64
from fastapi.testclient import TestClient
from app import models
from app.database import SessionLocal, engine
from app.main import app

client = TestClient(app)


def _make_round_with_image(image_b64: str | None) -> str:
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        g = models.GameStateModel(game_id=f"photo-{image_b64 is not None}", game_status="completed", state={}, scorecard_image=image_b64)
        db.merge(g)
        db.commit()
        return g.game_id
    finally:
        db.close()


def test_get_scorecard_photo_returns_image_bytes():
    raw = b"\xff\xd8\xff\xe0jpegbytes"
    gid = _make_round_with_image("data:image/jpeg;base64," + base64.b64encode(raw).decode())
    resp = client.get(f"/games/{gid}/scorecard-photo")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/")
    assert resp.content == raw


def test_get_scorecard_photo_404_when_none():
    gid = _make_round_with_image(None)
    assert client.get(f"/games/{gid}/scorecard-photo").status_code == 404
```

- [ ] **Step 2: Run to verify it fails** — `cd backend && venv/bin/python -m pytest tests/unit/routers/test_scorecard_photo.py -q` → FAIL (404 route missing).

- [ ] **Step 3: Implement.** Add to `backend/app/routers/games.py` (ensure `from fastapi import Response` is imported; `import base64`):

```python
@router.get("/{game_id}/scorecard-photo")
async def get_scorecard_photo(game_id: str, db: Session = Depends(database.get_db)) -> Response:
    """Return the stored scorecard photo for a scanned round (for later per-hole backfill)."""
    game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()
    if not game or not game.scorecard_image:
        raise HTTPException(status_code=404, detail="No scorecard photo for this round")
    raw = game.scorecard_image
    media_type = "image/jpeg"
    if raw.startswith("data:"):
        header, _, b64 = raw.partition(",")
        media_type = header[5:].split(";", 1)[0] or media_type
    else:
        b64 = raw
    try:
        content = base64.b64decode(b64)
    except Exception:
        raise HTTPException(status_code=404, detail="Stored photo is unreadable")
    return Response(content=content, media_type=media_type)
```

- [ ] **Step 4: Run to verify it passes** — `cd backend && venv/bin/python -m pytest tests/unit/routers/test_scorecard_photo.py -q` → PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/games.py backend/tests/unit/routers/test_scorecard_photo.py
git commit -m "feat(scorecard): GET /games/{id}/scorecard-photo serves the stored image"
```

---

## Task 4: `PATCH /games/{id}/scorecard` — backfill per-hole + recompute

**Files:**
- Modify: `backend/app/routers/games.py`
- Test: `backend/tests/unit/routers/test_scorecard_photo.py`

**Interfaces:**
- Consumes: `build_hole_history`, `persist_completed_game` (completed_game_service); `ScorecardRoundHoleQuarter`.
- Produces: `PATCH /games/{game_id}/scorecard` body `{ per_hole_quarters: [{player_index, hole, quarters}] }` → recomputes `hole_history`+`standings` on the round's state, refreshes `GamePlayerResult`s, returns `{ game_id, standings }`. 404 if round missing.

- [ ] **Step 1: Write the failing test**

```python
def test_patch_scorecard_recomputes_standings_from_new_per_hole():
    # create a round (totals-only: A +8 on hole 18, B -8)
    models.Base.metadata.create_all(bind=engine)
    create = client.post("/games/from-scorecard", json={
        "players": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}],
        "per_hole_quarters": [{"player_index": i, "hole": 18, "quarters": q} for i, q in enumerate([8, -8, 4, -4])],
    })
    gid = create.json()["game_id"]
    # backfill: spread A's +8 across holes 1 and 2 (sum still 8) — standings unchanged
    patch = client.patch(f"/games/{gid}/scorecard", json={"per_hole_quarters": [
        {"player_index": 0, "hole": 1, "quarters": 5}, {"player_index": 0, "hole": 2, "quarters": 3},
        {"player_index": 1, "hole": 1, "quarters": -5}, {"player_index": 1, "hole": 2, "quarters": -3},
        {"player_index": 2, "hole": 1, "quarters": 4}, {"player_index": 3, "hole": 1, "quarters": -4},
    ]})
    assert patch.status_code == 200, patch.text
    db = SessionLocal()
    try:
        state = db.query(models.GameStateModel).filter_by(game_id=gid).first().state
        # hole_history now has holes 1 and 2 (not just 18)
        assert {e["hole"] for e in state["hole_history"]} == {1, 2}
        # standings preserved: A total +8
        assert state["standings"]["p1"] == 8
    finally:
        db.close()


def test_patch_scorecard_404_for_missing_round():
    assert client.patch("/games/nope/scorecard", json={"per_hole_quarters": []}).status_code == 404
```

- [ ] **Step 2: Run to verify it fails** — `cd backend && venv/bin/python -m pytest tests/unit/routers/test_scorecard_photo.py -k patch -q` → FAIL.

- [ ] **Step 3: Implement.** Add to `backend/app/routers/games.py`:

```python
class ScorecardBackfillRequest(BaseModel):
    per_hole_quarters: list[ScorecardRoundHoleQuarter]


@router.patch("/{game_id}/scorecard")
async def backfill_scorecard(
    game_id: str,
    body: ScorecardBackfillRequest,
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """Backfill the per-hole quarters of a scanned round and recompute standings.
    Standings come out as the sum of the submitted per-hole (settle-up identity)."""
    from ..services.completed_game_service import build_hole_history, persist_completed_game

    game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Round not found")
    state = dict(game.state or {})
    players = state.get("players", [])
    n = len(players)
    for q in body.per_hole_quarters:
        if not (0 <= q.player_index < n) or not (1 <= q.hole <= 18):
            raise HTTPException(status_code=400, detail="Invalid per_hole_quarters entry")

    per_hole = [q.model_dump() for q in body.per_hole_quarters]
    hole_history, standings = build_hole_history(players, per_hole)
    state["hole_history"] = hole_history
    state["hole_quarters"] = {str(e["hole"]): e["points_delta"] for e in hole_history}
    state["standings"] = standings
    game.state = state  # reassign top-level so MutableDict marks dirty
    game.updated_at = utc_now().isoformat()

    # Rebuild GamePlayerResult rows for this round so /details reflects the backfill.
    record = db.query(models.GameRecord).filter(models.GameRecord.game_id == game_id).first()
    if record:
        db.query(models.GamePlayerResult).filter(models.GamePlayerResult.game_record_id == record.id).delete()
        db.flush()
    persist_completed_game(db, game)
    db.commit()
    return {"game_id": game_id, "standings": standings}
```

- [ ] **Step 4: Run to verify it passes** — `cd backend && venv/bin/python -m pytest tests/unit/routers/test_scorecard_photo.py -q` → PASS. Then full backend gate (ruff + full pytest) green (only the documented Mac-SOCKS local failure).

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/games.py backend/tests/unit/routers/test_scorecard_photo.py
git commit -m "feat(scorecard): PATCH /games/{id}/scorecard backfills per-hole + recomputes standings"
```

---

## Task 5: Frontend — downscale to base64 + send on save

**Files:**
- Modify: `frontend/src/utils/scorecardImage.js` (add `downscaleToBase64`)
- Modify: `frontend/src/components/game/ScorecardPhoto.jsx`
- Test: `frontend/src/utils/__tests__/scorecardImage.test.js` (or new), `frontend/src/components/game/__tests__/ScorecardPhoto.players.test.jsx`

**Interfaces:**
- Produces: `downscaleToBase64(file, maxDim=1200): Promise<string|null>` (a `data:image/jpeg;base64,...` string, or null on failure). `ScorecardPhoto` retains it from capture and includes `image_base64` in the `/games/from-scorecard` POST.

- [ ] **Step 1: Write the failing test** (util):

```js
// frontend/src/utils/__tests__/scorecardImage.test.js
import { test, expect, vi } from 'vitest';
import { downscaleToBase64 } from '../scorecardImage';

test('downscaleToBase64 returns null when canvas/bitmap unavailable (jsdom)', async () => {
  // jsdom has no real canvas encoding; the helper must degrade to null, not throw.
  const file = new File([new Uint8Array([1, 2, 3])], 'c.jpg', { type: 'image/jpeg' });
  const out = await downscaleToBase64(file, 1200);
  expect(out === null || typeof out === 'string').toBe(true);
});
```

- [ ] **Step 2: Run to verify it fails** — `cd frontend && npx vitest run src/utils/__tests__/scorecardImage.test.js` → FAIL (export missing).

- [ ] **Step 3: Implement `downscaleToBase64`** in `frontend/src/utils/scorecardImage.js` (mirror `preprocessScorecardImage`'s createImageBitmap+canvas, output a data URL; return null on any failure):

```js
export async function downscaleToBase64(file, maxDim = 1200) {
  if (!file || typeof createImageBitmap !== 'function') return null;
  try {
    let bitmap;
    try {
      bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
    } catch {
      bitmap = await createImageBitmap(file);
    }
    let { width, height } = bitmap;
    const longest = Math.max(width, height);
    if (longest > maxDim) {
      const scale = maxDim / longest;
      width = Math.round(width * scale);
      height = Math.round(height * scale);
    }
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    if (!ctx) { bitmap.close?.(); return null; }
    ctx.drawImage(bitmap, 0, 0, width, height);
    bitmap.close?.();
    const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
    return dataUrl && dataUrl.startsWith('data:image') ? dataUrl : null;
  } catch {
    return null;
  }
}
```

- [ ] **Step 4: Wire into `ScorecardPhoto.jsx`.** Add `import { preprocessScorecardImage, downscaleToBase64 } from '../../utils/scorecardImage';` (extend existing import). Add a ref `const photoB64Ref = useRef(null);`. In `handleCapture`, after retaining the object URL, also compute the base64 (best-effort, non-blocking):

```js
    downscaleToBase64(file, 1200).then((b64) => { photoB64Ref.current = b64; }).catch(() => {});
```

In `handleConfirm`'s `mode === 'new-round'` branch, include the image in the POST body:

```js
        body: JSON.stringify({ ...payload, course_name: 'Wing Point', image_base64: photoB64Ref.current || undefined }),
```

- [ ] **Step 5: Add the save-includes-image assertion** to `ScorecardPhoto.players.test.jsx` — mock `downscaleToBase64` to resolve `'data:image/jpeg;base64,QQ=='` and assert the from-scorecard POST body contains `image_base64`. (Mock `../../utils/scorecardImage` to provide both `preprocessScorecardImage` and `downscaleToBase64`.)

- [ ] **Step 6: Run + commit** — `cd frontend && npx vitest run src/utils src/components/game/__tests__/ScorecardPhoto.players.test.jsx && npm run typecheck` → green.

```bash
git add frontend/src/utils/scorecardImage.js frontend/src/components/game/ScorecardPhoto.jsx frontend/src/utils/__tests__/scorecardImage.test.js frontend/src/components/game/__tests__/ScorecardPhoto.players.test.jsx
git commit -m "feat(scorecard): send downscaled photo (image_base64) on from-scorecard save"
```

---

## Task 6: Frontend — "📷 Photo" on the completed round view

**Files:**
- Modify: `frontend/src/pages/SimpleScorekeeperPage.jsx`
- Test: a focused test for the photo button (mock fetch of `/scorecard-photo`)

**Interfaces:**
- Consumes: `GET /games/{id}/scorecard-photo` (Task 3), `ScorecardPhotoZoom` (Part A).
- Produces: on a completed round, a "📷 Photo" button that opens `ScorecardPhotoZoom` with the photo URL (object URL from the fetched blob, or the `/scorecard-photo` URL directly).

- [ ] **Step 1:** Read `SimpleScorekeeperPage.jsx` to find where a completed game renders its summary (the `game_status === 'completed'` branch). Identify the gameId + how it knows the round is from a scan (state.source === 'scorecard_scan', or just: try the photo URL and show the button only if the image exists — a `HEAD`/`GET` 200).

- [ ] **Step 2: Write the failing test** — render the completed view with a gameId; mock `fetch('/games/<id>/scorecard-photo')` → 200 image; assert a "Photo" button appears and clicking it renders `ScorecardPhotoZoom` (img alt "scorecard"). With a 404 photo, no button.

- [ ] **Step 3: Implement.** In the completed-round render, add state `const [photoOpen, setPhotoOpen] = useState(false)` and `const [hasPhoto, setHasPhoto] = useState(false)`; on mount for a completed scan round, `fetch(\`${API_URL}/games/${gameId}/scorecard-photo\`, { method: 'GET' })` and set `hasPhoto = res.ok`. Render a "📷 Photo" button when `hasPhoto`; clicking sets `photoOpen`. Render `{photoOpen && <ScorecardPhotoZoom src={\`${API_URL}/games/${gameId}/scorecard-photo\`} onClose={() => setPhotoOpen(false)} />}` (the `<img>` loads straight from the GET endpoint — no object URL needed). Import `ScorecardPhotoZoom`.

- [ ] **Step 4: Run + commit** — `cd frontend && npx vitest run <the new test> && npm run typecheck` → green.

```bash
git add frontend/src/pages/SimpleScorekeeperPage.jsx frontend/src/pages/__tests__/<new test>
git commit -m "feat(scorecard): Photo button on the completed round view (reuses zoom overlay)"
```

---

## Task 7: Frontend — "Fill in holes" backfill editor

**Files:**
- Create: `frontend/src/components/game/ScorecardBackfill.jsx`
- Modify: `frontend/src/pages/SimpleScorekeeperPage.jsx` (entry point)
- Test: `frontend/src/components/game/__tests__/ScorecardBackfill.test.jsx`

**Interfaces:**
- Consumes: `PATCH /games/{id}/scorecard` (Task 4), `ScorecardPhotoZoom` (Part A).
- Produces: `ScorecardBackfill` component (props: `gameId`, `players` [{id,name}], `holeHistory`, `standings`, `photoUrl`, `onSaved`, `onCancel`). Renders the per-hole running-total grid (one editable row per player × 18 holes), pre-filled by converting the round's current `hole_history` deltas to running totals; shows each player's **locked final total** with a warn if the entered per-hole doesn't reach it; a "📷 Photo" button (ScorecardPhotoZoom); Save → builds `per_hole_quarters` deltas and `PATCH`es.

- [ ] **Step 1: Write the failing test** (the core money path): render `ScorecardBackfill` with two players and a locked standings `{p1: 6, p2: -6}`; type running totals so p1 reaches 6 / p2 reaches -6 across holes; mock `fetch` PATCH; click Save; assert the PATCH body `per_hole_quarters` sums to the locked totals per player and `onSaved` is called. A second test: entering totals that DON'T reach the locked value shows a warning (text match) but Save is still allowed.

```jsx
// sketch — fill in real values in the test
// expect(JSON.parse(fetch.mock.calls[0][1].body).per_hole_quarters
//   .filter(q => q.player_index === 0).reduce((a, q) => a + q.quarters, 0)).toBe(6);
```

- [ ] **Step 2: Run to verify it fails** — component missing.

- [ ] **Step 3: Implement `ScorecardBackfill.jsx`.** Reuse the running-total→delta logic from `ScorecardReview` (`computeDeltas`) — extract it to `frontend/src/utils/quarters.js` as `computeHoleDeltas(runningTotals)` if shared cleanly, else duplicate the small function with a comment. Grid: editable running-total inputs per (player, hole); compute deltas; build `per_hole_quarters = [{player_index, hole, quarters}]` for nonzero deltas; compare each player's final running total to `standings[playerId]` and render an amber warn line per mismatch (non-blocking); Save PATCHes `${API_URL}/games/${gameId}/scorecard`. Include a "📷 Photo" button → `ScorecardPhotoZoom` with `photoUrl`.

- [ ] **Step 4: Wire the entry point** in `SimpleScorekeeperPage.jsx`: on a completed scan round, a "Fill in holes" button that mounts `ScorecardBackfill` (passing gameId, players, holeHistory, standings from the loaded state, and the photo URL). On `onSaved`, reload the round state.

- [ ] **Step 5: Run + full frontend gate + commit**

```bash
cd frontend && npm run typecheck && npx vitest run && npm run build
git add frontend/src/components/game/ScorecardBackfill.jsx frontend/src/pages/SimpleScorekeeperPage.jsx frontend/src/components/game/__tests__/ScorecardBackfill.test.jsx frontend/src/utils/quarters.js
git commit -m "feat(scorecard): Fill-in-holes backfill editor (locked totals, PATCH save)"
```

---

## Self-Review

- **Spec coverage:** storage column (T1) ✓; `image_base64` save (T2) ✓; serve GET (T3) ✓; PATCH backfill + recompute (T4) ✓; frontend send-on-save (T5) ✓; Photo button on completed view (T6) ✓; Fill-in editor with locked-total warn + PATCH (T7) ✓; migration (T1) ✓; standings=sum identity preserved (T4 recompute + test) ✓.
- **Type consistency:** `scorecard_image` column (T1) used by T2/T3; `image_base64` field (T2) sent by T5; `GET .../scorecard-photo` (T3) consumed by T6/T7; `PATCH .../scorecard` body `{per_hole_quarters:[{player_index,hole,quarters}]}` (T4) called by T7; `ScorecardPhotoZoom` (Part A, already merged) reused by T6/T7; `build_hole_history`/`persist_completed_game` reused by T4.
- **Placeholder scan:** backend tasks carry complete code; T6/T7 frontend tasks carry concrete steps + the key assertions, with `SimpleScorekeeperPage` structure to be read in-task (Step 1) since its completed-branch layout must be inspected before wiring — flagged explicitly rather than guessed.
- **Risk noted:** `persist_completed_game` is idempotent-on-(record,player); T4 deletes existing `GamePlayerResult`s before re-persist so a backfill actually refreshes them. Confirm `Text` and `Response` imports exist before re-adding.
