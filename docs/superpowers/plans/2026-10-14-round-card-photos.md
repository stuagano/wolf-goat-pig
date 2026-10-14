# Round Card Photos Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Any finished round can carry its paper card photo; the round's players and admins can attach it and correct the numbers. Each round records who last edited its card.

**Architecture:**
- One new utility, `backend/app/utils/round_card.py`, holds three things: the "who may edit this round" rule, the FastAPI dependency built on it, and the audit stamp.
- A new small router, `backend/app/routers/game_card.py`, adds `PUT /games/{id}/scorecard-photo` and `GET /games/{id}/card`. `games.py` is already 1,181 lines, so it doesn't grow.
- The existing `PATCH /games/{id}/scorecard` gets the dependency.
- On the frontend, `CompletedRoundView` asks `GET /games/{id}/card` whether the viewer may edit and whether a photo exists, then shows an "Add the card photo" input and a "Card edited by" line.

**Tech Stack:** FastAPI, SQLAlchemy, Pillow, pytest (backend); React with Vite, vitest, and Testing Library (frontend); Auth0 bearer tokens via `useAuthenticatedFetch`.

**Spec:** `docs/superpowers/specs/2026-10-14-round-card-photos-design.md`

**Deviation from the spec (deliberate):**
- The spec gates the frontend by comparing the viewer's profile id to `players[].player_profile_id`. But live rounds don't store `player_profile_id` in `state["players"]`; it lives only on `GamePlayer` rows. That comparison would hide the button from real members.
- Instead, the server answers `can_edit` in `GET /games/{id}/card`, using the same rule that guards the writes.
- That endpoint needs sign-in, so the "Card edited by" line shows only to signed-in viewers. The photo itself stays public.

## Global Constraints

- Who may write: players in that round, plus admins. Anonymous callers get 401; signed-in non-members get 403.
- "Player in the round" means the signed-in profile's `id` equals a `player_profile_id`, either in `state["players"]` or on the round's `GamePlayer` rows, or the profile's `preferences["auth0_id"]` equals a `GamePlayer.user_id`. Admin is `is_admin_profile(profile)` from `app/utils/admin_auth.py`.
- `GET /games/{id}/scorecard-photo` stays public and unchanged.
- The photo `PUT` never touches `hole_history`, `standings`, or `hole_quarters`.
- Stored photo: a JPEG data URL, longest side at most 2000px, quality 85, EXIF-rotated, in `GameStateModel.scorecard_image`. Uploads over 20 MB are rejected.
- Audit fields: `state["card_edited_by"]` is `profile.name or profile.email`, and `state["card_edited_at"]` is a UTC ISO string. Only the last edit is kept.
- Copy: the button reads **"📷 Add the card photo"** and the line reads **"Card edited by {name} · {date}"**.
- Repo rules:
  - Never edit code containing `!` through shell heredocs; use the Edit and Write tools.
  - Restore `frontend/public/service-worker.js` and `frontend/public/version.json` after `npm run build`.
  - Commits end with `Co-authored-by: Isaac <no-reply@databricks.com>`.

## Review Focus

1. **Live-scored round, member who joined by Auth0 only.** Their `GamePlayer.user_id` matches but `player_profile_id` is null, so `can_edit` must be true. Pinned in Task 1 by `test_member_by_auth0_sub_may_edit`.
2. **Scanned round, which has no `GamePlayer` rows.** Membership comes from `state["players"][].player_profile_id`. Pinned in Task 1 by `test_member_by_state_profile_id_may_edit`.
3. **A photo that isn't an image.** A PDF or text file must return 400, not 500, and leave any existing photo alone. Pinned in Task 2 by `test_put_photo_rejects_non_image_and_keeps_old_photo`.
4. **A signed-out viewer opens a finished round.** The token fetch rejects, so no add button shows and nothing crashes. The existing 📷 button still works. Pinned in Task 3 by `hides add button when signed out`.
5. **Upload fails, for example a 403 or 413.** The user sees an error, and the add button stays so they can retry. Pinned in Task 3 by `shows an error when the upload fails`.

---

### Task 1: Membership rule, dependency, and lock on `PATCH /scorecard`

**Files:**
- Create: `backend/app/utils/round_card.py`
- Modify: `backend/app/routers/games.py:1121-1161` (`backfill_scorecard`)
- Modify: `backend/tests/unit/routers/test_scorecard_photo.py` (the existing PATCH test now needs a member)
- Create: `backend/tests/unit/routers/test_round_card_access.py`

**Interfaces:**
- Produces:
  - `can_edit_round(db: Session, game: models.GameStateModel, profile: Any) -> bool`
  - `require_round_member_or_admin(game_id: str, profile=Depends(get_current_user), db=Depends(get_db)) -> PlayerProfile`. It raises 404 when there's no round and 403 for a non-member; 401 comes from `HTTPBearer`.
  - `mark_card_edited(state: dict, profile: Any) -> None`
- Test helper: `profile(**kw)` builds a `SimpleNamespace` fake profile. Task 2 copies it.

- [ ] **Step 1: Write the failing tests**

`backend/tests/unit/routers/test_round_card_access.py`:

```python
"""Only the round's players and admins may change its card."""

import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import models
from app.database import SessionLocal, engine
from app.main import app
from app.services.auth_service import get_current_user

client = TestClient(app)

PER_HOLE = {"per_hole_quarters": [{"player_index": 0, "hole": 1, "quarters": 2}, {"player_index": 1, "hole": 1, "quarters": -2}]}


def profile(**kw):
    base = {"id": 9001, "name": "Stranger", "email": "stranger@test.com", "preferences": {}, "admin_granted": 0, "is_active": 1}
    return SimpleNamespace(**{**base, **kw})


@pytest.fixture
def as_profile():
    def _set(p):
        app.dependency_overrides[get_current_user] = lambda: p

    yield _set
    app.dependency_overrides.pop(get_current_user, None)


def make_round(state_players, game_players=()):
    """A completed round. state_players go in state; game_players become GamePlayer rows."""
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        gid = str(uuid.uuid4())
        db.add(models.GameStateModel(game_id=gid, game_status="completed", state={"players": state_players, "hole_history": []}))
        for slot, (profile_id, user_id) in enumerate(game_players):
            db.add(models.GamePlayer(game_id=gid, player_slot_id=f"p{slot}", player_name=f"P{slot}", player_profile_id=profile_id, user_id=user_id))
        db.commit()
        return gid
    finally:
        db.close()


def stored_state(gid):
    db = SessionLocal()
    try:
        return dict(db.query(models.GameStateModel).filter_by(game_id=gid).one().state)
    finally:
        db.close()


TWO = [{"id": "a", "name": "A", "player_profile_id": 501}, {"id": "b", "name": "B"}]


def test_member_by_state_profile_id_may_edit(as_profile):
    gid = make_round(TWO)
    as_profile(profile(id=501, name="Alice"))
    assert client.patch(f"/games/{gid}/scorecard", json=PER_HOLE).status_code == 200


def test_member_by_auth0_sub_may_edit(as_profile):
    gid = make_round([{"id": "p0", "name": "A"}, {"id": "p1", "name": "B"}], game_players=[(None, "auth0|alice"), (None, None)])
    as_profile(profile(preferences={"auth0_id": "auth0|alice"}))
    assert client.patch(f"/games/{gid}/scorecard", json=PER_HOLE).status_code == 200


def test_member_by_game_player_profile_id_may_edit(as_profile):
    gid = make_round([{"id": "p0", "name": "A"}, {"id": "p1", "name": "B"}], game_players=[(777, None), (None, None)])
    as_profile(profile(id=777))
    assert client.patch(f"/games/{gid}/scorecard", json=PER_HOLE).status_code == 200


def test_admin_may_edit_any_round(as_profile, monkeypatch):
    monkeypatch.setenv("SUPER_ADMIN_EMAILS", "boss@test.com")
    gid = make_round(TWO)
    as_profile(profile(email="boss@test.com"))
    assert client.patch(f"/games/{gid}/scorecard", json=PER_HOLE).status_code == 200


def test_signed_in_non_member_is_forbidden(as_profile):
    gid = make_round(TWO)
    as_profile(profile())
    assert client.patch(f"/games/{gid}/scorecard", json=PER_HOLE).status_code == 403


def test_anonymous_is_unauthorized():
    gid = make_round(TWO)
    assert client.patch(f"/games/{gid}/scorecard", json=PER_HOLE).status_code == 401


def test_patch_records_who_edited(as_profile):
    gid = make_round(TWO)
    as_profile(profile(id=501, name="Alice"))
    client.patch(f"/games/{gid}/scorecard", json=PER_HOLE)
    state = stored_state(gid)
    assert state["card_edited_by"] == "Alice"
    assert state["card_edited_at"].startswith("20")
```

In `backend/tests/unit/routers/test_scorecard_photo.py`, `test_patch_scorecard_recomputes_standings_from_new_per_hole` must now call as an admin. Add these imports at the top:

```python
from types import SimpleNamespace

from app.services.auth_service import get_current_user
```

Then add this as the first lines of that test, before `models.Base.metadata.create_all`:

```python
    monkeypatch.setenv("SUPER_ADMIN_EMAILS", "boss@test.com")
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, name="Boss", email="boss@test.com", preferences={}, admin_granted=0, is_active=1
    )
```

Change its signature to `def test_patch_scorecard_recomputes_standings_from_new_per_hole(monkeypatch):`. Finally, add `app.dependency_overrides.pop(get_current_user, None)` as the test's last line.

- [ ] **Step 2: Run the tests and confirm they fail**

Run (sandbox off): `cd backend && venv/bin/pytest tests/unit/routers/test_round_card_access.py -v`

Expected: the 403 and 401 tests fail because the route accepts anyone. `test_patch_records_who_edited` fails with `KeyError: 'card_edited_by'`.

- [ ] **Step 3: Implement `round_card.py`**

```python
"""Who may change a finished round's card: the players in that round, plus admins."""

from typing import Any

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..services.auth_service import get_current_user
from .admin_auth import is_admin_profile
from .time import utc_now


def can_edit_round(db: Session, game: models.GameStateModel, profile: Any) -> bool:
    """Admin, or a player in this round by profile id (state or GamePlayer) or Auth0 sub."""
    if is_admin_profile(profile):
        return True
    profile_id = getattr(profile, "id", None)
    auth0_id = (getattr(profile, "preferences", None) or {}).get("auth0_id")
    # Scanned rounds have no GamePlayer rows; their roster lives in state.
    if profile_id is not None and any(
        p.get("player_profile_id") == profile_id for p in (game.state or {}).get("players", [])
    ):
        return True
    rows = db.query(models.GamePlayer).filter(models.GamePlayer.game_id == game.game_id).all()
    return any(
        (profile_id is not None and r.player_profile_id == profile_id) or (auth0_id and r.user_id == auth0_id)
        for r in rows
    )


def require_round_member_or_admin(
    game_id: str,
    profile: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.PlayerProfile:
    game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Round not found")
    if not can_edit_round(db, game, profile):
        raise HTTPException(status_code=403, detail="Only players in this round or an admin can change its card")
    return profile


def mark_card_edited(state: dict, profile: Any) -> None:
    """Last edit only; full history is out of scope."""
    state["card_edited_by"] = getattr(profile, "name", None) or getattr(profile, "email", None)
    state["card_edited_at"] = utc_now().isoformat()
```

- [ ] **Step 4: Wire it into `backfill_scorecard`** in `backend/app/routers/games.py`

Add `from ..utils.round_card import mark_card_edited, require_round_member_or_admin` next to the `admin_auth` import. Change the signature:

```python
@router.patch("/{game_id}/scorecard")
async def backfill_scorecard(
    game_id: str,
    body: ScorecardBackfillRequest,
    editor: models.PlayerProfile = Depends(require_round_member_or_admin),
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
```

Then, right after `state["standings"] = standings`, add:

```python
    mark_card_edited(state, editor)
```

- [ ] **Step 5: Run the tests and confirm they pass**

Run (sandbox off): `cd backend && venv/bin/pytest tests/unit/routers/test_round_card_access.py tests/unit/routers/test_scorecard_photo.py -v`

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/utils/round_card.py backend/app/routers/games.py backend/tests/unit/routers/test_round_card_access.py backend/tests/unit/routers/test_scorecard_photo.py
git commit -m "feat(games): only the round's players and admins may edit its scorecard

Co-authored-by: Isaac <no-reply@databricks.com>"
```

---

### Task 2: `PUT /games/{id}/scorecard-photo` and `GET /games/{id}/card`

**Files:**
- Create: `backend/app/routers/game_card.py`
- Modify: `backend/app/main.py` (import `game_card` next to `games_players` at line 35; `app.include_router(game_card.router)` after line 344)
- Create: `backend/tests/unit/routers/test_game_card.py`
- Regenerate: the OpenAPI artifacts via `./scripts/sync_openapi.sh`

**Interfaces:**
- Consumes: `can_edit_round`, `require_round_member_or_admin`, and `mark_card_edited` from Task 1.
- Produces:
  - `PUT /games/{game_id}/scorecard-photo` takes multipart field `file` and returns `{"game_id", "card_edited_by", "card_edited_at"}`.
  - `GET /games/{game_id}/card` requires sign-in and returns `{"has_photo": bool, "can_edit": bool, "edited_by": str|None, "edited_at": str|None}`.

- [ ] **Step 1: Write the failing tests**

`backend/tests/unit/routers/test_game_card.py`:

```python
"""Attach a card photo to any finished round; numbers stay as they are."""

import uuid
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import models
from app.database import SessionLocal, engine
from app.main import app
from app.services.auth_service import get_current_user

client = TestClient(app)
HISTORY = [{"hole": 1, "points_delta": {"a": 2, "b": -2}}]


def profile(**kw):
    base = {"id": 9001, "name": "Stranger", "email": "stranger@test.com", "preferences": {}, "admin_granted": 0, "is_active": 1}
    return SimpleNamespace(**{**base, **kw})


MEMBER = profile(id=501, name="Alice")


@pytest.fixture
def as_profile():
    def _set(p):
        app.dependency_overrides[get_current_user] = lambda: p

    yield _set
    app.dependency_overrides.pop(get_current_user, None)


def make_round(image=None):
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        gid = str(uuid.uuid4())
        state = {"players": [{"id": "a", "name": "A", "player_profile_id": 501}, {"id": "b", "name": "B"}], "hole_history": HISTORY}
        db.add(models.GameStateModel(game_id=gid, game_status="completed", state=state, scorecard_image=image))
        db.commit()
        return gid
    finally:
        db.close()


def stored(gid):
    db = SessionLocal()
    try:
        g = db.query(models.GameStateModel).filter_by(game_id=gid).one()
        return g.scorecard_image, dict(g.state)
    finally:
        db.close()


def jpeg(w=3000, h=2000):
    buf = BytesIO()
    Image.new("RGB", (w, h), "white").save(buf, format="JPEG")
    return buf.getvalue()


def put(gid, data, name="card.jpg", ctype="image/jpeg"):
    return client.put(f"/games/{gid}/scorecard-photo", files={"file": (name, data, ctype)})


def test_put_photo_stores_downscaled_jpeg_and_leaves_numbers(as_profile):
    gid = make_round()
    as_profile(MEMBER)
    assert put(gid, jpeg()).status_code == 200
    image, state = stored(gid)
    assert image.startswith("data:image/jpeg;base64,")
    import base64

    img = Image.open(BytesIO(base64.b64decode(image.split(",", 1)[1])))
    assert max(img.size) == 2000
    assert state["hole_history"] == HISTORY
    assert state["card_edited_by"] == "Alice"


def test_put_photo_replaces_existing(as_profile):
    gid = make_round(image="data:image/jpeg;base64,b2xk")
    as_profile(MEMBER)
    assert put(gid, jpeg(100, 100)).status_code == 200
    assert stored(gid)[0] != "data:image/jpeg;base64,b2xk"


def test_put_photo_rejects_non_image_and_keeps_old_photo(as_profile):
    gid = make_round(image="data:image/jpeg;base64,b2xk")
    as_profile(MEMBER)
    assert put(gid, b"%PDF-1.4 not an image", "card.pdf", "application/pdf").status_code == 400
    assert stored(gid)[0] == "data:image/jpeg;base64,b2xk"


def test_put_photo_rejects_over_20mb(as_profile, monkeypatch):
    from app.routers import game_card

    monkeypatch.setattr(game_card, "CARD_MAX_UPLOAD_BYTES", 10)
    gid = make_round()
    as_profile(MEMBER)
    assert put(gid, jpeg(100, 100)).status_code == 413


def test_put_photo_forbidden_for_non_member(as_profile):
    gid = make_round()
    as_profile(profile())
    assert put(gid, jpeg(100, 100)).status_code == 403


def test_put_photo_unauthorized_when_signed_out():
    gid = make_round()
    assert put(gid, jpeg(100, 100)).status_code == 401


def test_card_reports_access_photo_and_last_edit(as_profile):
    gid = make_round()
    as_profile(MEMBER)
    assert client.get(f"/games/{gid}/card").json() == {"has_photo": False, "can_edit": True, "edited_by": None, "edited_at": None}
    put(gid, jpeg(100, 100))
    body = client.get(f"/games/{gid}/card").json()
    assert body["has_photo"] is True and body["edited_by"] == "Alice"
    as_profile(profile())
    assert client.get(f"/games/{gid}/card").json()["can_edit"] is False


def test_card_404_for_unknown_round(as_profile):
    as_profile(MEMBER)
    assert client.get("/games/nope/card").status_code == 404
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run (sandbox off): `cd backend && venv/bin/pytest tests/unit/routers/test_game_card.py -v`

Expected: FAIL. The PUT returns 405 because only GET exists on that path, and `/card` returns 404.

- [ ] **Step 3: Implement `backend/app/routers/game_card.py`**

```python
"""A finished round's paper card: attach the photo, and report who may edit it."""

import base64
from io import BytesIO
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, ImageOps
from sqlalchemy.orm import Session

from .. import database, models
from ..services.auth_service import get_current_user
from ..utils.round_card import can_edit_round, mark_card_edited, require_round_member_or_admin
from ..utils.time import utc_now

router = APIRouter(prefix="/games", tags=["games"])

CARD_MAX_UPLOAD_BYTES = 20 * 1024 * 1024
CARD_MAX_DIM = 2000  # big enough to read handwriting, small enough for the 2MB column budget


def _downscale_card(image_bytes: bytes) -> str:
    img = ImageOps.exif_transpose(Image.open(BytesIO(image_bytes))).convert("RGB")
    img.thumbnail((CARD_MAX_DIM, CARD_MAX_DIM), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


@router.put("/{game_id}/scorecard-photo")
async def put_scorecard_photo(
    game_id: str,
    file: UploadFile = File(...),
    editor: models.PlayerProfile = Depends(require_round_member_or_admin),
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """Attach or replace the round's card photo. Numbers are untouched."""
    image_bytes = await file.read()
    if len(image_bytes) > CARD_MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Photo too large. Maximum size is 20MB.")
    try:
        image = _downscale_card(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Could not read that file as a photo") from e

    game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).one()
    state = dict(game.state or {})
    mark_card_edited(state, editor)
    game.scorecard_image = image
    game.state = state  # reassign top-level so MutableDict marks dirty
    game.updated_at = utc_now().isoformat()
    db.commit()
    return {"game_id": game_id, "card_edited_by": state["card_edited_by"], "card_edited_at": state["card_edited_at"]}


@router.get("/{game_id}/card")
def get_card(
    game_id: str,
    profile: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """What the signed-in viewer may do with this round's card, and its last edit."""
    game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Round not found")
    state = game.state or {}
    return {
        "has_photo": bool(game.scorecard_image),
        "can_edit": can_edit_round(db, game, profile),
        "edited_by": state.get("card_edited_by"),
        "edited_at": state.get("card_edited_at"),
    }
```

Register it in `backend/app/main.py`. Add `game_card,` to the router import list that contains `games_players,` (line 35, keep it alphabetical), and add `app.include_router(game_card.router)` right after `app.include_router(games_players.router)`.

- [ ] **Step 4: Run the tests and confirm they pass**

Run (sandbox off): `cd backend && venv/bin/pytest tests/unit/routers/test_game_card.py tests/unit/routers/test_round_card_access.py -v`

Expected: all pass.

- [ ] **Step 5: Sync OpenAPI**

Run (sandbox off): `./scripts/sync_openapi.sh && cd backend && venv/bin/python scripts/export_openapi.py --check`

Expected: `--check` passes. If the worktree has no `frontend/node_modules`, run `cd frontend && npm ci` first.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/game_card.py backend/app/main.py backend/tests/unit/routers/test_game_card.py
git add -u  # regenerated OpenAPI artifacts
git commit -m "feat(games): attach a card photo to any round, report card access

Co-authored-by: Isaac <no-reply@databricks.com>"
```

---

### Task 3: Frontend: add the photo, see it while editing, show the last edit, send tokens

**Files:**
- Modify: `frontend/src/components/game/CompletedRoundView.jsx`
- Modify: `frontend/src/components/game/__tests__/CompletedRoundView.test.jsx`
- Modify: `frontend/src/components/game/scorekeeper/ScorekeeperBanners.jsx` (new `gameId` prop; photo button inside the edit banner)
- Modify: `frontend/src/components/game/SimpleScorekeeper.jsx:820-831` (pass `gameId={gameId}` to `ScorekeeperBanners`)
- Create: `frontend/src/components/game/scorekeeper/__tests__/ScorekeeperBanners.test.jsx`
- Modify: `frontend/src/components/game/ScorecardBackfill.jsx:155` (PATCH via `useAuthenticatedFetch`)
- Modify: `frontend/src/components/game/__tests__/ScorecardBackfill.test.jsx` (mock the hook)

**Interfaces:**
- Consumes:
  - `GET /games/{id}/card` returns `{has_photo, can_edit, edited_by, edited_at}`.
  - `PUT /games/{id}/scorecard-photo` takes multipart `file`.
  - `useAuthenticatedFetch()` from `frontend/src/hooks/useAuthenticatedFetch.js` returns `(url, options) => Promise<Response>`, with the bearer token added. It rejects when signed out.
- Produces: `ScorekeeperBanners` accepts an optional `gameId` prop.

- [ ] **Step 1: Write the failing CompletedRoundView tests**

Add these mocks to `CompletedRoundView.test.jsx`, below the existing `vi.mock` calls:

```jsx
const authFetch = vi.fn();
vi.mock('../../../hooks/useAuthenticatedFetch', () => ({ useAuthenticatedFetch: () => authFetch }));

const card = (body) => Promise.resolve({ ok: true, json: async () => body });
const NO_PHOTO = { has_photo: false, can_edit: true, edited_by: null, edited_at: null };
```

`vi.resetAllMocks()` in `beforeEach` clears `authFetch`, so each existing test must not crash when it returns `undefined`. Add `authFetch.mockReturnValue(card({ has_photo: true, can_edit: false }));` as the line after `vi.resetAllMocks();`.

Add these tests inside the `describe`:

```jsx
  test('a member sees "Add the card photo" when the round has no photo, and the upload sends the file', async () => {
    authFetch.mockReturnValueOnce(card(NO_PHOTO)).mockReturnValueOnce(Promise.resolve({ ok: true, json: async () => ({}) }));
    render(<CompletedRoundView {...baseProps} gameId="g1" onMarkedComplete={vi.fn()} onEditScores={vi.fn()} />);

    const input = await screen.findByLabelText(/add the card photo/i);
    const file = new File(['x'], 'card.jpg', { type: 'image/jpeg' });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() =>
      expect(authFetch).toHaveBeenCalledWith('http://test-api/games/g1/scorecard-photo', expect.objectContaining({ method: 'PUT' })),
    );
    const body = authFetch.mock.calls.find(([, o]) => o?.method === 'PUT')[1].body;
    expect(body.get('file')).toBe(file);
  });

  test('hides add button when the viewer may not edit', async () => {
    authFetch.mockReturnValueOnce(card({ ...NO_PHOTO, can_edit: false }));
    render(<CompletedRoundView {...baseProps} gameId="g1" onMarkedComplete={vi.fn()} onEditScores={vi.fn()} />);
    await waitFor(() => expect(authFetch).toHaveBeenCalled());
    expect(screen.queryByLabelText(/add the card photo/i)).toBeNull();
  });

  test('hides add button when signed out', async () => {
    authFetch.mockReturnValueOnce(Promise.reject(new Error('Login required')));
    render(<CompletedRoundView {...baseProps} gameId="g1" onMarkedComplete={vi.fn()} onEditScores={vi.fn()} />);
    await waitFor(() => expect(authFetch).toHaveBeenCalled());
    expect(screen.queryByLabelText(/add the card photo/i)).toBeNull();
    expect(screen.getByText('photo:g1')).toBeTruthy();
  });

  test('shows an error when the upload fails', async () => {
    authFetch.mockReturnValueOnce(card(NO_PHOTO)).mockReturnValueOnce(Promise.resolve({ ok: false, status: 403 }));
    render(<CompletedRoundView {...baseProps} gameId="g1" onMarkedComplete={vi.fn()} onEditScores={vi.fn()} />);
    fireEvent.change(await screen.findByLabelText(/add the card photo/i), {
      target: { files: [new File(['x'], 'card.jpg', { type: 'image/jpeg' })] },
    });
    expect(await screen.findByRole('alert')).toHaveTextContent('403');
    expect(screen.getByLabelText(/add the card photo/i)).toBeTruthy();
  });

  test('shows who last edited the card', async () => {
    authFetch.mockReturnValueOnce(card({ has_photo: true, can_edit: false, edited_by: 'Alice', edited_at: '2026-10-14T18:00:00' }));
    render(<CompletedRoundView {...baseProps} gameId="g1" onMarkedComplete={vi.fn()} onEditScores={vi.fn()} />);
    expect(await screen.findByText(/Card edited by Alice ·/)).toBeTruthy();
  });
```

If `toHaveTextContent` isn't registered in this repo's vitest setup, use `expect(screen.getByRole('alert').textContent).toContain('403')` instead.

- [ ] **Step 2: Run them and confirm they fail**

Run: `cd frontend && npx vitest run src/components/game/__tests__/CompletedRoundView.test.jsx`

Expected: the new tests fail because there is no "Add the card photo" label and no "Card edited by" text.

- [ ] **Step 3: Implement in `CompletedRoundView.jsx`**

Change the imports to:

```jsx
import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import GameCompletionView from "./GameCompletionView";
import ScorecardPhotoButton from "./ScorecardPhotoButton";
import { apiConfig } from "../../config/api.config";
import { fetchJson } from "../../services/fetchJson";
import { useAuthenticatedFetch } from "../../hooks/useAuthenticatedFetch";
```

Inside the component, before `handleMarkComplete`, add:

```jsx
  const authenticatedFetch = useAuthenticatedFetch();
  // { has_photo, can_edit, edited_by, edited_at } — null when signed out or unknown.
  const [card, setCard] = useState(null);
  // Bumped after an upload: re-reads /card and remounts the photo button.
  const [photoVersion, setPhotoVersion] = useState(0);
  const [uploadError, setUploadError] = useState(null);

  useEffect(() => {
    if (!gameId) return;
    authenticatedFetch(`${API_URL}/games/${gameId}/card`)
      .then((res) => (res.ok ? res.json() : null))
      .then(setCard)
      .catch(() => setCard(null)); // signed out: view-only
  }, [gameId, authenticatedFetch, photoVersion]);

  const handleCardPhoto = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const body = new FormData();
    body.append("file", file);
    setUploadError(null);
    try {
      const res = await authenticatedFetch(`${API_URL}/games/${gameId}/scorecard-photo`, { method: "PUT", body });
      if (!res.ok) throw new Error(`Upload failed (${res.status})`);
      setPhotoVersion((v) => v + 1);
    } catch (error) {
      setUploadError(error.message);
    }
  };
```

Replace `{gameId && <ScorecardPhotoButton gameId={gameId} />}` with:

```jsx
      {gameId && <ScorecardPhotoButton key={photoVersion} gameId={gameId} />}
      {card?.can_edit && !card.has_photo && (
        <label
          style={{
            display: "inline-block",
            padding: "12px 24px",
            fontSize: "16px",
            fontWeight: "bold",
            borderRadius: "8px",
            border: "2px solid #1976d2",
            background: "white",
            color: "#1976d2",
            cursor: "pointer",
          }}
        >
          📷 Add the card photo
          <input type="file" accept="image/*" hidden onChange={handleCardPhoto} />
        </label>
      )}
      {uploadError && (
        <p role="alert" style={{ color: "#b91c1c" }}>
          {uploadError}
        </p>
      )}
      {card?.edited_by && (
        <p style={{ color: "#6b7280", fontSize: "14px" }}>
          Card edited by {card.edited_by} · {new Date(card.edited_at).toLocaleDateString()}
        </p>
      )}
```

- [ ] **Step 4: Run them and confirm they pass**

Run: `cd frontend && npx vitest run src/components/game/__tests__/CompletedRoundView.test.jsx`

Expected: all pass.

- [ ] **Step 5: Failing test for the photo in edit mode**

`frontend/src/components/game/scorekeeper/__tests__/ScorekeeperBanners.test.jsx`:

```jsx
import React from 'react';
import { describe, test, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ScorekeeperBanners from '../ScorekeeperBanners';

vi.mock('../../ScorecardPhotoButton', () => ({
  default: ({ gameId }) => <div>photo:{gameId}</div>,
}));

const props = {
  courseDataLoading: false,
  courseDataError: null,
  rotationError: null,
  achievementCheckFailed: false,
  setAchievementCheckFailed: vi.fn(),
  setIsEditingCompleteGame: vi.fn(),
  editingHole: null,
  setCurrentHole: vi.fn(),
  resetHole: vi.fn(),
  holeHistory: [],
  gameId: 'g1',
};

describe('ScorekeeperBanners', () => {
  test('editing a finished round shows the card photo button', () => {
    render(<ScorekeeperBanners {...props} isEditingCompleteGame />);
    expect(screen.getByText('photo:g1')).toBeTruthy();
  });

  test('live scoring does not', () => {
    render(<ScorekeeperBanners {...props} isEditingCompleteGame={false} />);
    expect(screen.queryByText('photo:g1')).toBeNull();
  });
});
```

Run: `cd frontend && npx vitest run src/components/game/scorekeeper/__tests__/ScorekeeperBanners.test.jsx`

Expected: the first test fails. Check the propTypes at `ScorekeeperBanners.jsx:~305` and pass any other required prop it lists.

- [ ] **Step 6: Implement the photo in edit mode**

In `ScorekeeperBanners.jsx`:
- Add `import ScorecardPhotoButton from "../ScorecardPhotoButton";`.
- Add `gameId,` to the destructured props.
- Add `gameId: PropTypes.string,` to `propTypes`.
- Inside the `{isEditingCompleteGame && (` banner, put the photo button right after the "Click on any hole in the scorecard below to edit it" `<div>`'s closing tag, inside the left-hand `<div>`:

```jsx
            {gameId && (
              <div style={{ marginTop: "8px" }}>
                <ScorecardPhotoButton gameId={gameId} />
              </div>
            )}
```

In `SimpleScorekeeper.jsx`, add `gameId={gameId}` to the `<ScorekeeperBanners` props (around line 820).

Run: `cd frontend && npx vitest run src/components/game/scorekeeper/__tests__/ScorekeeperBanners.test.jsx`

Expected: PASS.

- [ ] **Step 7: Make ScorecardBackfill send the token**

`PATCH /scorecard` is locked by Task 1, so plain `fetch` now gets 401.

In `ScorecardBackfill.jsx`:
- Add `import { useAuthenticatedFetch } from '../../hooks/useAuthenticatedFetch';`.
- At the top of the component body, add `const authenticatedFetch = useAuthenticatedFetch();`.
- Change the PATCH call's `fetch(` to `authenticatedFetch(`, keeping its options.

In `ScorecardBackfill.test.jsx`, add the following mock below the existing mocks. It routes through the test's global `fetch` mock, so existing assertions keep working:

```jsx
vi.mock('../../../hooks/useAuthenticatedFetch', () => ({
  useAuthenticatedFetch: () => (url, options = {}) =>
    global.fetch(url, { ...options, headers: { ...options.headers, Authorization: 'Bearer test-token' } }),
}));
```

Add one assertion to the existing test that checks the PATCH call. Find it with `grep -n "PATCH" frontend/src/components/game/__tests__/ScorecardBackfill.test.jsx`:

```jsx
    expect(global.fetch.mock.calls.find(([, o]) => o?.method === 'PATCH')[1].headers.Authorization).toBe('Bearer test-token');
```

If the existing test asserts the exact headers object with `toHaveBeenCalledWith`, wrap it in `expect.objectContaining`.

Run: `cd frontend && npx vitest run src/components/game/__tests__/ScorecardBackfill.test.jsx`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/game/CompletedRoundView.jsx frontend/src/components/game/__tests__/CompletedRoundView.test.jsx \
  frontend/src/components/game/scorekeeper/ScorekeeperBanners.jsx frontend/src/components/game/scorekeeper/__tests__/ScorekeeperBanners.test.jsx \
  frontend/src/components/game/SimpleScorekeeper.jsx frontend/src/components/game/ScorecardBackfill.jsx \
  frontend/src/components/game/__tests__/ScorecardBackfill.test.jsx
git commit -m "feat(rounds): add the card photo to a finished round, see it while editing

Co-authored-by: Isaac <no-reply@databricks.com>"
```

---

### Task 4: Full gate, caps, PR

**Files:** `.ctk/ledger.json` (after the caps re-proof), plus any formatting fixes.

- [ ] **Step 1: Run the backend gate** (sandbox off, from the worktree, with the `backend/venv` symlink in place)

```bash
cd backend && venv/bin/ruff check app/ tests/ && venv/bin/ruff format --check app/ tests/ \
  && venv/bin/python scripts/export_openapi.py --check \
  && venv/bin/pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic
```

Expected: exit 0. If formatting fails, run `ruff format app/ tests/` and rerun.

- [ ] **Step 2: Run the frontend gate**

```bash
cd frontend && npm run check:lockfile && npm run typecheck && npx vitest run && npm run build
git checkout -- frontend/public/service-worker.js frontend/public/version.json
```

Expected: exit 0.

- [ ] **Step 3: Re-prove caps**

Run: `PYTHONPATH=.ctk backend/venv/bin/python -m caps verify --capability game-state-db-authoritative`. Also re-prove any other capability the Stop hook names for the touched files, such as `api-surface-no-drift`.

Expected: proven. Commit the ledger with the message `chore(caps): re-prove after round card photos`, ending with the co-author line.

- [ ] **Step 4: Push and open the PR**

Print the Isaac Review tip once, then:

```bash
git push -u origin stuagano/round-card-photos
gh pr create --title "feat: card photos on any round, editable by its players and admins" --body "<summary + test plan; ends with: This pull request and its description were written by Isaac.>"
```

Merge only on the user's approval. After the merge, check `/health` on production and confirm that `PUT /games/x/scorecard-photo` without a token returns 401.
