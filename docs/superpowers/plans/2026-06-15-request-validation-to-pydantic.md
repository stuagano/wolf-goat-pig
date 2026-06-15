# Request-Shape Validation → Pydantic Models — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move ~13 request-shape validation checks from `backend/app/routers/` handlers onto the Pydantic request models FastAPI already parses, so malformed requests are rejected with 422 before handler logic runs.

**Architecture:** Add a shared `non_blank` string validator helper. For endpoints that already have a request model, attach the constraint. For endpoints with raw `dict` bodies, introduce a typed `BaseModel` next to the router and replace the `dict` parameter. Business-state checks (need the loaded game/DB) and parse/file/external-error 400s stay in the handlers untouched.

**Tech Stack:** FastAPI, Pydantic v2 (`Field`, `Annotated` + `AfterValidator`), pytest + `fastapi.testclient.TestClient`.

**Spec:** `docs/superpowers/specs/2026-06-15-request-validation-to-pydantic-design.md`

**Key facts the implementer must know:**
- Pydantic body validation runs **before** the handler executes. So a bad body returns 422 even for a nonexistent game (the 422 precedes the handler's 404 lookup and any `require_admin` call). Tests exploit this — they need no DB fixtures.
- The 400→422 change is intentional and safe: the frontend treats all 4xx identically and reads `.detail`, which `main.py`'s `RequestValidationError` handler populates for 422.
- Preserve exact behavior. Use `min_length=1` (not `non_blank`) for fields whose current check is `if not x` — those accept whitespace (`" "` is truthy). Use `non_blank` only for the name fields whose handlers explicitly `.strip()` then check.
- Run backend from `backend/` with `backend/venv` active. Full gate before any push:
  `ruff check app/ tests/ && ruff format --check app/ tests/ && pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic`

---

## File Structure

- **Create** `backend/app/routers/_validators.py` — shared `non_blank` function + `NonBlankStr` annotated type. One responsibility: reusable field validation primitives.
- **Modify** `backend/app/routers/games_players.py` — `UpdatePlayerNameRequest.name` → `NonBlankStr`; delete dead count check in `create_custom_game`; new `UpdateHandicapRequest` for `update_player_handicap`.
- **Modify** `backend/app/routers/tee_sheet.py` — `SignupRequest.name` → `NonBlankStr`.
- **Modify** `backend/app/routers/games.py` — new `SetTeeOrderRequest` for `set_tee_order`.
- **Modify** `backend/app/routers/email_routes.py` — new `TestEmailRequest` for `send_test_email`.
- **Modify** `backend/app/routers/admin_oauth.py` — new `OAuth2TestEmailRequest` for `test_oauth2_email`.
- **Modify** `backend/app/routers/admin.py` — new `AdminTestEmailRequest` for `test_admin_email`.
- **Modify** `backend/app/routers/sheet_integration.py` — new `CsvUrlRequest` (sync + fetch) and `CompareSheetRequest` (compare).
- **Test files** (all exist): `tests/unit/routers/test_validators.py` (new), `test_games_players_router.py`, `test_create_custom_game.py`, `test_signups_router.py` (tee-sheet lives here? verify — see Task 4), `test_games_router.py`, `test_email_routes_router.py`, `test_admin_oauth_router.py`, `test_admin_router.py`, `test_sheet_integration_router.py`.

---

## Task 1: Shared `non_blank` validator helper

**Files:**
- Create: `backend/app/routers/_validators.py`
- Test: `backend/tests/unit/routers/test_validators.py` (create)

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/routers/test_validators.py`:

```python
"""Unit tests for shared router request-validation helpers."""

import pytest

from app.routers._validators import non_blank


def test_non_blank_strips_surrounding_whitespace():
    assert non_blank("  hello  ") == "hello"


def test_non_blank_returns_unchanged_when_clean():
    assert non_blank("hello") == "hello"


def test_non_blank_rejects_empty_string():
    with pytest.raises(ValueError):
        non_blank("")


def test_non_blank_rejects_whitespace_only():
    with pytest.raises(ValueError):
        non_blank("   ")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/unit/routers/test_validators.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.routers._validators'`

- [ ] **Step 3: Write minimal implementation**

Create `backend/app/routers/_validators.py`:

```python
"""Reusable Pydantic field-validation primitives for router request models."""

from typing import Annotated

from pydantic import AfterValidator


def non_blank(v: str) -> str:
    """Strip surrounding whitespace and reject empty/whitespace-only strings.

    Raised ValueError is wrapped by Pydantic into a 422 response.
    """
    v = v.strip()
    if not v:
        raise ValueError("must not be blank")
    return v


# A `str` that is stripped and guaranteed non-empty after validation.
NonBlankStr = Annotated[str, AfterValidator(non_blank)]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/unit/routers/test_validators.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/_validators.py backend/tests/unit/routers/test_validators.py
git commit -m "feat(validation): add shared non_blank request-field validator"
```

---

## Task 2: `update_player_name` — non-blank via model

**Files:**
- Modify: `backend/app/routers/games_players.py` (`UpdatePlayerNameRequest` at line 57; handler at line 473-483)
- Test: `backend/tests/unit/routers/test_games_players_router.py`

Current model: `class UpdatePlayerNameRequest(BaseModel): name: str = Field(..., min_length=2, max_length=50)`
Current handler opens with `new_name = name_update.name.strip()` then `if not new_name: raise HTTPException(status_code=400, detail="Name cannot be blank")`.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/unit/routers/test_games_players_router.py`:

```python
class TestUpdatePlayerNameValidation:
    """Request-shape validation for PATCH /games/{id}/players/{pid}/name."""

    def test_whitespace_only_name_returns_422(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        resp = client.patch(
            "/games/nonexistent/players/p1/name", json={"name": "  "}
        )
        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_valid_name_passes_validation_then_404s(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        resp = client.patch(
            "/games/nonexistent/players/p1/name", json={"name": "Valid Name"}
        )
        # Passes body validation, then fails the DB player lookup.
        assert resp.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/unit/routers/test_games_players_router.py::TestUpdatePlayerNameValidation -v`
Expected: FAIL — `test_whitespace_only_name_returns_422` gets 400 (current handler raises `HTTPException(400, "Name cannot be blank")`), not 422.

- [ ] **Step 3: Write minimal implementation**

In `backend/app/routers/games_players.py`, add the import near the top (with the other relative imports):

```python
from ._validators import NonBlankStr
```

Change the model:

```python
class UpdatePlayerNameRequest(BaseModel):
    name: NonBlankStr = Field(..., min_length=2, max_length=50)
```

In the handler, the name is now already stripped and non-blank, so remove the manual check. Replace:

```python
    new_name = name_update.name.strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="Name cannot be blank")
```

with:

```python
    new_name = name_update.name
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/unit/routers/test_games_players_router.py::TestUpdatePlayerNameValidation -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/games_players.py backend/tests/unit/routers/test_games_players_router.py
git commit -m "refactor(validation): move player-name non-blank check to Pydantic model"
```

---

## Task 3: `create_custom_game` — delete dead count check

**Files:**
- Modify: `backend/app/routers/games_players.py` (handler at line 162-170)
- Test: `backend/tests/unit/routers/test_create_custom_game.py`

`CreateCustomGameRequest.players` already declares `Field(min_length=4, max_length=6)`, so a wrong player count is rejected with 422 by Pydantic before the handler runs. The handler's `if len(body.players) not in (4, 5, 6): raise HTTPException(400, ...)` is therefore unreachable dead code. This task adds a characterization test (passes before and after) and removes the dead check.

- [ ] **Step 1: Write the characterization test**

Append to `backend/tests/unit/routers/test_create_custom_game.py` (if the file has no TestClient yet, add the imports at top of the new class as shown):

```python
class TestCreateCustomGamePlayerCount:
    """The 4-6 player bound is enforced by the Pydantic model (422)."""

    def _client(self):
        from fastapi.testclient import TestClient

        from app.main import app

        return TestClient(app)

    def test_three_players_rejected_with_422(self):
        client = self._client()
        players = [
            {"name": f"P{i}", "handicap": 10, "is_ghost": False} for i in range(3)
        ]
        resp = client.post("/games/create-custom", json={"players": players})
        assert resp.status_code == 422

    def test_seven_players_rejected_with_422(self):
        client = self._client()
        players = [
            {"name": f"P{i}", "handicap": 10, "is_ghost": False} for i in range(7)
        ]
        resp = client.post("/games/create-custom", json={"players": players})
        assert resp.status_code == 422
```

- [ ] **Step 2: Run test to verify it already passes (characterization)**

Run: `cd backend && pytest tests/unit/routers/test_create_custom_game.py::TestCreateCustomGamePlayerCount -v`
Expected: PASS — the model's `min_length/max_length` already produces 422. (This confirms the handler check is redundant.)

- [ ] **Step 3: Remove the dead check**

In `backend/app/routers/games_players.py` `create_custom_game`, delete:

```python
    if len(body.players) not in (4, 5, 6):
        raise HTTPException(status_code=400, detail="Wolf Goat Pig requires 4, 5, or 6 players")
```

- [ ] **Step 4: Run test to verify it still passes**

Run: `cd backend && pytest tests/unit/routers/test_create_custom_game.py -v`
Expected: PASS (the 422 behavior is unchanged; it came from the model all along).

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/games_players.py backend/tests/unit/routers/test_create_custom_game.py
git commit -m "refactor(validation): drop unreachable player-count check (model enforces 4-6)"
```

---

## Task 4: `signup_for_tee_sheet` — non-blank name via model

**Files:**
- Modify: `backend/app/routers/tee_sheet.py` (`SignupRequest` at line 124; handler at line 130-134)
- Test: `backend/tests/unit/routers/test_tee_sheet_router.py` (create — no tee-sheet test exists yet)

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/routers/test_tee_sheet_router.py`:

```python
"""Unit tests for tee_sheet router — request-shape validation."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestTeeSheetSignupValidation:
    def test_whitespace_only_name_returns_422(self):
        resp = client.post(
            "/tee-sheet/signup", json={"date": "2026-06-20", "name": "  "}
        )
        assert resp.status_code == 422
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/unit/routers/test_tee_sheet_router.py -v`
Expected: FAIL — current handler returns 400 ("Name is required").

- [ ] **Step 3: Write minimal implementation**

In `backend/app/routers/tee_sheet.py`, add the import near the top:

```python
from ._validators import NonBlankStr
```

Change the model:

```python
class SignupRequest(BaseModel):
    date: str
    name: NonBlankStr
```

In the handler, replace:

```python
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
```

with:

```python
    name = request.name
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/unit/routers/test_tee_sheet_router.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/tee_sheet.py backend/tests/unit/routers/test_tee_sheet_router.py
git commit -m "refactor(validation): move tee-sheet signup name check to Pydantic model"
```

---

## Task 5: `update_player_handicap` — typed model replaces dict body

**Files:**
- Modify: `backend/app/routers/games_players.py` (handler at line 586-622)
- Test: `backend/tests/unit/routers/test_games_players_router.py`

Current signature: `handicap_update: dict`. Current checks: `None → 400 "Handicap not provided"`, non-numeric `→ 400 "Invalid handicap value"`, range `< 0 or > 54 → 400`. A new model collapses all three into framework validation. The business-state check at line 622 (`game_status not in ["setup","lobby"]`) and the 404 lookup STAY.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/unit/routers/test_games_players_router.py`:

```python
class TestUpdateHandicapValidation:
    """Request-shape validation for PATCH /games/{id}/players/{pid}/handicap."""

    def _client(self):
        from fastapi.testclient import TestClient

        from app.main import app

        return TestClient(app)

    def test_missing_handicap_returns_422(self):
        resp = self._client().patch(
            "/games/nonexistent/players/p1/handicap", json={}
        )
        assert resp.status_code == 422

    def test_non_numeric_handicap_returns_422(self):
        resp = self._client().patch(
            "/games/nonexistent/players/p1/handicap", json={"handicap": "abc"}
        )
        assert resp.status_code == 422

    def test_out_of_range_handicap_returns_422(self):
        resp = self._client().patch(
            "/games/nonexistent/players/p1/handicap", json={"handicap": 99}
        )
        assert resp.status_code == 422

    def test_negative_handicap_returns_422(self):
        resp = self._client().patch(
            "/games/nonexistent/players/p1/handicap", json={"handicap": -1}
        )
        assert resp.status_code == 422

    def test_valid_handicap_passes_validation_then_404s(self):
        resp = self._client().patch(
            "/games/nonexistent/players/p1/handicap", json={"handicap": 18}
        )
        # Passes body validation, then fails the DB game lookup.
        assert resp.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/unit/routers/test_games_players_router.py::TestUpdateHandicapValidation -v`
Expected: FAIL — current handler returns 400 for the missing/non-numeric/out-of-range cases (not 422).

- [ ] **Step 3: Write minimal implementation**

In `backend/app/routers/games_players.py`, add a model alongside the others near the top (after `UpdatePlayerNameRequest`):

```python
class UpdateHandicapRequest(BaseModel):
    handicap: float = Field(..., ge=0, le=54)
```

Change the handler signature parameter from:

```python
    handicap_update: dict,
```

to:

```python
    handicap_update: UpdateHandicapRequest,
```

Replace the opening of the `try` block:

```python
    try:
        new_handicap = handicap_update.get("handicap")
        if new_handicap is None:
            raise HTTPException(status_code=400, detail="Handicap not provided")

        try:
            new_handicap = float(new_handicap)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid handicap value")

        if new_handicap < 0 or new_handicap > 54:
            raise HTTPException(status_code=400, detail="Handicap must be between 0 and 54")

        # Get game from database
```

with:

```python
    try:
        new_handicap = handicap_update.handicap

        # Get game from database
```

Leave everything below (the 404 lookup, the `game_status not in ["setup", "lobby"]` check, and the DB update) unchanged.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/unit/routers/test_games_players_router.py::TestUpdateHandicapValidation -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/games_players.py backend/tests/unit/routers/test_games_players_router.py
git commit -m "refactor(validation): type handicap-update body with Pydantic model"
```

---

## Task 6: `set_tee_order` — typed model for player_order presence

**Files:**
- Modify: `backend/app/routers/games.py` (handler at line 399-411)
- Test: `backend/tests/unit/routers/test_games_router.py`

Only the presence check (`if not player_order → 400 "player_order is required"`) moves. The count-mismatch check and the per-id `Invalid player_slot_id` check are business-state (need the DB roster) and STAY.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/unit/routers/test_games_router.py`:

```python
class TestSetTeeOrderValidation:
    def _client(self):
        from fastapi.testclient import TestClient

        from app.main import app

        return TestClient(app)

    def test_missing_player_order_returns_422(self):
        resp = self._client().patch("/games/nonexistent/tee-order", json={})
        assert resp.status_code == 422

    def test_empty_player_order_returns_422(self):
        resp = self._client().patch(
            "/games/nonexistent/tee-order", json={"player_order": []}
        )
        assert resp.status_code == 422
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/unit/routers/test_games_router.py::TestSetTeeOrderValidation -v`
Expected: FAIL — current handler returns 404 (game lookup runs first) or 400, not 422. (Note: the current handler does the game lookup BEFORE the player_order check, so an empty order on a nonexistent game currently 404s. After the change, body validation precedes the handler so it 422s.)

- [ ] **Step 3: Write minimal implementation**

In `backend/app/routers/games.py`, add a model near the top (after the router definition, before the routes), and import `BaseModel`/`Field` if not already imported (check the import block — add `from pydantic import BaseModel, Field` if absent):

```python
class SetTeeOrderRequest(BaseModel):
    player_order: list[str] = Field(..., min_length=1)
```

Change the handler signature from:

```python
async def set_tee_order(
    game_id: str, request: dict[str, Any], db: Session = Depends(database.get_db)
) -> dict[str, Any]:
```

to:

```python
async def set_tee_order(
    game_id: str, request: SetTeeOrderRequest, db: Session = Depends(database.get_db)
) -> dict[str, Any]:
```

Replace:

```python
        player_order = request.get("player_order", [])
        if not player_order:
            raise HTTPException(status_code=400, detail="player_order is required")
```

with:

```python
        player_order = request.player_order
```

Leave the count-mismatch check and the `Invalid player_slot_id` loop unchanged.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/unit/routers/test_games_router.py::TestSetTeeOrderValidation -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/games.py backend/tests/unit/routers/test_games_router.py
git commit -m "refactor(validation): type set-tee-order body; player_order presence via model"
```

---

## Task 7: Email test endpoints — typed models (`send_test_email`, `test_oauth2_email`, `test_admin_email`)

**Files:**
- Modify: `backend/app/routers/email_routes.py` (handler at line 20-33)
- Modify: `backend/app/routers/admin_oauth.py` (handler at line 250-257)
- Modify: `backend/app/routers/admin.py` (handler at line 86-95)
- Test: `test_email_routes_router.py`, `test_admin_oauth_router.py`, `test_admin_router.py`

All three use `min_length=1` (not `non_blank`) to preserve the exact `if not x` semantics (whitespace stays accepted). Body validation precedes the handler, so the 422 fires before `require_admin` on the admin endpoints.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/unit/routers/test_email_routes_router.py`:

```python
class TestSendTestEmailValidation:
    def test_missing_to_email_returns_422(self):
        from fastapi.testclient import TestClient

        from app.main import app

        resp = TestClient(app).post("/email/send-test", json={})
        assert resp.status_code == 422
```

Append to `backend/tests/unit/routers/test_admin_oauth_router.py`:

```python
class TestOAuth2TestEmailValidation:
    def test_missing_test_email_returns_422(self):
        from fastapi.testclient import TestClient

        from app.main import app

        resp = TestClient(app).post("/admin/oauth2-test-email", json={})
        assert resp.status_code == 422
```

Append to `backend/tests/unit/routers/test_admin_router.py`:

```python
class TestAdminTestEmailValidation:
    def test_missing_test_email_returns_422(self):
        from fastapi.testclient import TestClient

        from app.main import app

        resp = TestClient(app).post("/admin/test-email", json={})
        assert resp.status_code == 422
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/unit/routers/test_email_routes_router.py::TestSendTestEmailValidation tests/unit/routers/test_admin_oauth_router.py::TestOAuth2TestEmailValidation tests/unit/routers/test_admin_router.py::TestAdminTestEmailValidation -v`
Expected: FAIL — current handlers return 400/503/403 depending on path, not 422.

- [ ] **Step 3a: `email_routes.py`**

Add `from pydantic import BaseModel, Field` to the imports, then add the model after `router = APIRouter(...)`:

```python
class TestEmailRequest(BaseModel):
    to_email: str = Field(..., min_length=1)
    player_name: str = "Test Player"
    signup_date: str = "Tomorrow"
```

Change the signature from `async def send_test_email(email_data: dict):  # type: ignore` to:

```python
async def send_test_email(email_data: TestEmailRequest):
```

Replace:

```python
        to_email = email_data.get("to_email")
        if not to_email:
            raise HTTPException(status_code=400, detail="to_email is required")

        success = email_service.send_signup_confirmation(
            to_email=to_email,
            player_name=email_data.get("player_name", "Test Player"),
            signup_date=email_data.get("signup_date", "Tomorrow"),
        )
```

with:

```python
        to_email = email_data.to_email

        success = email_service.send_signup_confirmation(
            to_email=to_email,
            player_name=email_data.player_name,
            signup_date=email_data.signup_date,
        )
```

- [ ] **Step 3b: `admin_oauth.py`**

Add `from pydantic import BaseModel, Field` to the imports (check it's not already there), then add the model near the top:

```python
class OAuth2TestEmailRequest(BaseModel):
    test_email: str = Field(..., min_length=1)
```

Change `async def test_oauth2_email(request: dict[str, Any], x_admin_email: str = Header(None)):  # type: ignore` to:

```python
async def test_oauth2_email(request: OAuth2TestEmailRequest, x_admin_email: str = Header(None)):  # type: ignore
```

Replace:

```python
        test_email = request.get("test_email")
        if not test_email:
            raise HTTPException(status_code=400, detail="Test email address required")
```

with:

```python
        test_email = request.test_email
```

- [ ] **Step 3c: `admin.py`**

Add `from pydantic import BaseModel, Field` to the imports (check it's not already there), then add the model near the top:

```python
class AdminTestEmailRequest(BaseModel):
    test_email: str = Field(..., min_length=1)
    config: dict[str, Any] = Field(default_factory=dict)
```

Change `async def test_admin_email(request: dict[str, Any], x_admin_email: str = Header(None)):  # type: ignore` to:

```python
async def test_admin_email(request: AdminTestEmailRequest, x_admin_email: str = Header(None)):  # type: ignore
```

Replace:

```python
        test_email = request.get("test_email")
        config = request.get("config", {})

        if not test_email:
            raise HTTPException(status_code=400, detail="Test email address required")
```

with:

```python
        test_email = request.test_email
        config = request.config
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/unit/routers/test_email_routes_router.py::TestSendTestEmailValidation tests/unit/routers/test_admin_oauth_router.py::TestOAuth2TestEmailValidation tests/unit/routers/test_admin_router.py::TestAdminTestEmailValidation -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/email_routes.py backend/app/routers/admin_oauth.py backend/app/routers/admin.py backend/tests/unit/routers/test_email_routes_router.py backend/tests/unit/routers/test_admin_oauth_router.py backend/tests/unit/routers/test_admin_router.py
git commit -m "refactor(validation): type email-test request bodies with Pydantic models"
```

---

## Task 8: `sheet_integration` — CsvUrlRequest + CompareSheetRequest

**Files:**
- Modify: `backend/app/routers/sheet_integration.py` (`sync_wgp_sheet_data` line 224, `fetch_google_sheet` line 567, `compare_sheet_to_db_data` line 620)
- Test: `backend/tests/unit/routers/test_sheet_integration_router.py`

Only the request-presence checks move: `csv_url` (sync + fetch) and `sheet_data` (compare). The downstream "Empty sheet data", "Could not find valid headers", and fetch-failure 400s validate fetched content / network and STAY.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/unit/routers/test_sheet_integration_router.py`:

```python
class TestSheetIntegrationBodyValidation:
    def _client(self):
        from fastapi.testclient import TestClient

        from app.main import app

        return TestClient(app)

    def test_sync_missing_csv_url_returns_422(self):
        resp = self._client().post("/sync-wgp-sheet", json={})
        assert resp.status_code == 422

    def test_fetch_missing_csv_url_returns_422(self):
        resp = self._client().post("/fetch-google-sheet", json={})
        assert resp.status_code == 422

    def test_compare_missing_sheet_data_returns_422(self):
        resp = self._client().post("/compare-data", json={})
        assert resp.status_code == 422
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/unit/routers/test_sheet_integration_router.py::TestSheetIntegrationBodyValidation -v`
Expected: FAIL — current handlers return 400 (or pass the rate-limit then 400), not 422.

- [ ] **Step 3: Write minimal implementation**

In `backend/app/routers/sheet_integration.py`, add `from pydantic import BaseModel, Field` to the imports, then add models after the imports:

```python
class CsvUrlRequest(BaseModel):
    csv_url: str = Field(..., min_length=1)


class CompareSheetRequest(BaseModel):
    sheet_data: list[dict[str, Any]] = Field(..., min_length=1)
```

`sync_wgp_sheet_data` — change `request: dict[str, str],` to `request: CsvUrlRequest,`. Replace:

```python
        csv_url = request.get("csv_url")
        if not csv_url:
            raise HTTPException(status_code=400, detail="CSV URL is required")
```

with:

```python
        csv_url = request.csv_url
```

`fetch_google_sheet` — change `async def fetch_google_sheet(request: dict[str, str]) -> dict[str, Any]:` to `async def fetch_google_sheet(request: CsvUrlRequest) -> dict[str, Any]:`. Replace:

```python
        csv_url = request.get("csv_url")
        if not csv_url:
            raise HTTPException(status_code=400, detail="CSV URL is required")
```

with:

```python
        csv_url = request.csv_url
```

`compare_sheet_to_db_data` — change `async def compare_sheet_to_db_data(request: dict, db: Session = Depends(get_db)) -> dict[str, Any]:` to `async def compare_sheet_to_db_data(request: CompareSheetRequest, db: Session = Depends(get_db)) -> dict[str, Any]:`. Replace:

```python
        sheet_data = request.get("sheet_data", [])
        if not sheet_data:
            raise HTTPException(status_code=400, detail="Sheet data is required")
```

with:

```python
        sheet_data = request.sheet_data
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/unit/routers/test_sheet_integration_router.py::TestSheetIntegrationBodyValidation -v`
Expected: PASS (3 passed)

Note: `sync_wgp_sheet_data` is rate-limited (once/hour). Body validation runs before the handler (and before the rate limiter), so the 422 test is unaffected by rate-limit state.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/sheet_integration.py backend/tests/unit/routers/test_sheet_integration_router.py
git commit -m "refactor(validation): type sheet-integration request bodies with Pydantic models"
```

---

## Task 9: Full gate + business-state guard

**Files:** none (verification only)

- [ ] **Step 1: Confirm a sampling of business-state checks still return their original status**

Add a regression guard so a future over-migration can't silently flip these to 422. Append to `backend/tests/unit/routers/test_games_router.py`:

```python
class TestBusinessStateStays400Not422:
    """Guard: state checks that need the loaded game must NOT become 422."""

    def test_join_nonexistent_game_is_404_not_422(self):
        from fastapi.testclient import TestClient

        from app.main import app

        # Well-formed JoinGameRequest body (player_name required) to a
        # nonexistent join code → fails on game lookup (404), not shape.
        resp = TestClient(app).post(
            "/games/join/ZZZZZZ", json={"player_name": "Tester"}
        )
        assert resp.status_code == 404
        assert resp.status_code != 422
```

The assertion is the point: a well-formed request must not 422 — it reaches the handler and fails the business-state lookup.

- [ ] **Step 2: Run the new guard**

Run: `cd backend && pytest tests/unit/routers/test_games_router.py::TestBusinessStateStays400Not422 -v`
Expected: PASS

- [ ] **Step 3: Run the full backend gate**

Run:
```bash
cd backend && ruff check app/ tests/ && ruff format --check app/ tests/ \
  && pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic
```
Expected: ruff clean, all tests pass. If `ruff format --check` flags the new code, run `ruff format app/ tests/` and re-commit.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/unit/routers/test_games_router.py
git commit -m "test(validation): guard business-state checks against accidental 422 migration"
```

---

## Self-Review notes

- **Spec coverage:** Group A (3 endpoints) → Tasks 2-4. Group B (8 endpoints) → Tasks 5-8 (handicap, set_tee_order, 3 email endpoints, 3 sheet endpoints). Shared helper → Task 1. Business-state guard → Task 9. All in-scope checks covered.
- **Out-of-scope items** (legacy_scoring, the 3 unchecked email endpoints, parse/file/external 400s, business-state checks) are deliberately untouched — no tasks, by design.
- **Type consistency:** `NonBlankStr`/`non_blank` defined in Task 1, used in Tasks 2 & 4. New model names are unique per router: `UpdateHandicapRequest`, `SetTeeOrderRequest`, `TestEmailRequest`, `OAuth2TestEmailRequest`, `AdminTestEmailRequest`, `CsvUrlRequest`, `CompareSheetRequest`.
- **Behavior preservation:** `min_length=1` for `if not x` presence checks (whitespace-accepting), `non_blank` only for the two name fields whose handlers strip-then-check.
