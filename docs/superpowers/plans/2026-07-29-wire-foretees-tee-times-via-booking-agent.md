# Wire FastAPI Tee-Times via Booking Agent — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `GET /api/foretees/tee-times` proxy to booking-agent `POST /tee-times` using per-user ForeTees credentials only, with real HTTP errors instead of empty lists on failure.

**Architecture:** Router requires profile ForeTees username + decrypted password (no env singleton). `ForeteesService` gains a typed booking-agent list client with a ~60s timeout; success returns agent `slots` unchanged into existing `ApiResponse`. SPA stays on the same GET.

**Tech Stack:** FastAPI, httpx, pytest, unittest.mock / respx-style mocks as already used in ForeTees tests.

**Spec:** `docs/superpowers/specs/2026-07-29-wire-foretees-tee-times-via-booking-agent-design.md`

## Global Constraints

- Per-user ForeTees credentials only for listing — no `FORETEES_USERNAME` / env singleton fallback on this endpoint.
- SPA contract unchanged: `GET /api/foretees/tee-times?date=YYYY-MM-DD` → `ApiResponse.success` with slot list.
- Slot field names unchanged (`date`, `time`, `front_back`, `players`, `open_slots`, `max_players`, `ttdata`, `jump`, `p5_allowed`).
- Auth/sheet/transport failures → HTTP `400`/`502` — never disguise as empty `data: []`. Empty list only when agent returns `{status: "ok", slots: []}`.
- Read timeout ~60s total (not the 300s Computer Use book timeout).
- Do not change SPA. Do not proxy `/bookings` in this plan. Do not dual-path behind a feature flag.
- NEVER edit source containing `!` via shell heredoc/perl/zsh — use Edit/Write tools.
- Backend gate: `cd backend && source venv/bin/activate && env -u DATABASE_URL ruff check app/ tests/ && env -u DATABASE_URL ruff format --check app/ tests/ && env -u DATABASE_URL pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic -q`

---

## File Structure

- Modify: `backend/app/services/foretees_service.py` — typed list proxy + stop in-process scrape in `get_tee_times`.
- Modify: `backend/app/routers/foretees.py` — per-user creds gate for `get_tee_times`; map typed errors to HTTP.
- Modify: `backend/tests/unit/routers/test_foretees_router.py` — update tee-times tests for new behavior.
- Create: `backend/tests/unit/services/test_foretees_tee_times_proxy.py` — service-level booking-agent client tests.
- Modify: `docs/architecture/COMPUTER_USE_BOOKING.md` — note FastAPI list path now proxies to agent.

---

### Task 1: Service — typed booking-agent tee-times client

**Files:**
- Modify: `backend/app/services/foretees_service.py`
- Create: `backend/tests/unit/services/test_foretees_tee_times_proxy.py`

**Interfaces:**
- Produces:
  - `class ForeteesTeeTimesError(Exception)` with attributes `code: str` (`foretees_auth_failed` | `foretees_sheet_failed` | `booking_service_auth` | `booking_service_unavailable` | `booking_service_timeout`) and `message: str`
  - `async def fetch_tee_times_via_booking_agent(username: str, password: str, date: str) -> list[dict[str, Any]]` (module-level or static/method on `ForeteesService` — prefer **module-level async function** in the same file for easy patching, OR instance method that does not need a ForeteesService session)
  - Prefer: `async def fetch_tee_times_via_booking_agent(...)` as a **module-level** function in `foretees_service.py` so the router can call it without constructing a scrape session.

- [ ] **Step 1: Write failing service tests**

```python
# backend/tests/unit/services/test_foretees_tee_times_proxy.py
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.foretees_service import (
    ForeteesTeeTimesError,
    fetch_tee_times_via_booking_agent,
)


@pytest.mark.asyncio
async def test_happy_path_returns_slots(monkeypatch):
    monkeypatch.setenv("BOOKING_SERVICE_URL", "https://booking.test")
    monkeypatch.setenv("BOOKING_SERVICE_SECRET", "sec")

    slots = [{"time": "08:00 AM", "players": [], "open_slots": 4, "max_players": 4}]
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.json.return_value = {"status": "ok", "date": "2026-07-29", "slots": slots}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=MagicMock(status_code=200))
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("app.services.foretees_service.httpx.AsyncClient", return_value=mock_client):
        result = await fetch_tee_times_via_booking_agent("u", "p", "2026-07-29")
    assert result == slots
    mock_client.post.assert_awaited()
    args, kwargs = mock_client.post.await_args
    assert args[0] == "https://booking.test/tee-times"
    assert kwargs["json"] == {"username": "u", "password": "p", "date": "2026-07-29"}
    assert kwargs["headers"]["Authorization"] == "Bearer sec"


@pytest.mark.asyncio
async def test_agent_auth_failed_raises(monkeypatch):
    monkeypatch.setenv("BOOKING_SERVICE_URL", "https://booking.test")
    monkeypatch.setenv("BOOKING_SERVICE_SECRET", "sec")
    mock_resp = MagicMock()
    mock_resp.status_code = 502
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.json.return_value = {"status": "failed", "error": "foretees_auth_failed"}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=MagicMock(status_code=200))
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("app.services.foretees_service.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(ForeteesTeeTimesError) as exc:
            await fetch_tee_times_via_booking_agent("u", "p", "2026-07-29")
    assert exc.value.code == "foretees_auth_failed"


@pytest.mark.asyncio
async def test_booking_service_401_raises(monkeypatch):
    monkeypatch.setenv("BOOKING_SERVICE_URL", "https://booking.test")
    monkeypatch.setenv("BOOKING_SERVICE_SECRET", "bad")
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.json.return_value = {"detail": "Unauthorized"}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=MagicMock(status_code=200))
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("app.services.foretees_service.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(ForeteesTeeTimesError) as exc:
            await fetch_tee_times_via_booking_agent("u", "p", "2026-07-29")
    assert exc.value.code == "booking_service_auth"


@pytest.mark.asyncio
async def test_timeout_raises(monkeypatch):
    monkeypatch.setenv("BOOKING_SERVICE_URL", "https://booking.test")
    monkeypatch.setenv("BOOKING_SERVICE_SECRET", "sec")
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=MagicMock(status_code=200))
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    with patch("app.services.foretees_service.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(ForeteesTeeTimesError) as exc:
            await fetch_tee_times_via_booking_agent("u", "p", "2026-07-29")
    assert exc.value.code == "booking_service_timeout"
```

- [ ] **Step 2: Run — expect FAIL** (`ImportError` for `ForeteesTeeTimesError` / `fetch_tee_times_via_booking_agent`)

```bash
cd backend && source venv/bin/activate && env -u DATABASE_URL pytest tests/unit/services/test_foretees_tee_times_proxy.py -q
```

- [ ] **Step 3: Implement module-level client in `foretees_service.py`**

Add near `_call_booking_service` (do not break book/cancel):

```python
class ForeteesTeeTimesError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


async def fetch_tee_times_via_booking_agent(
    username: str, password: str, date: str
) -> list[dict[str, Any]]:
    booking_url = os.getenv("BOOKING_SERVICE_URL", "http://localhost:8080").rstrip("/")
    booking_secret = os.getenv("BOOKING_SERVICE_SECRET", "")
    headers = {"Content-Type": "application/json"}
    if booking_secret:
        headers["Authorization"] = f"Bearer {booking_secret}"

    timeout = httpx.Timeout(60.0, connect=30.0)
    payload = {"username": username, "password": password, "date": date}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                await client.get(f"{booking_url}/health")
            except Exception:
                logger.warning("Booking service health check failed for tee-times, trying anyway")
            resp = await client.post(f"{booking_url}/tee-times", json=payload, headers=headers)
    except httpx.TimeoutException as exc:
        raise ForeteesTeeTimesError(
            "booking_service_timeout",
            "Tee times request timed out — try again shortly.",
        ) from exc
    except Exception as exc:
        raise ForeteesTeeTimesError(
            "booking_service_unavailable",
            f"Booking service error: {exc}",
        ) from exc

    if resp.status_code == 401:
        raise ForeteesTeeTimesError(
            "booking_service_auth",
            "Booking service auth failed — check BOOKING_SERVICE_SECRET",
        )
    if resp.status_code == 502:
        body: dict[str, Any] = {}
        try:
            if "json" in resp.headers.get("content-type", ""):
                body = resp.json()
        except Exception:
            body = {}
        err = body.get("error") or "foretees_sheet_failed"
        if err == "foretees_auth_failed":
            raise ForeteesTeeTimesError(
                "foretees_auth_failed",
                "ForeTees login failed for your saved credentials.",
            )
        raise ForeteesTeeTimesError(
            "foretees_sheet_failed",
            "Could not load the ForeTees tee sheet.",
        )
    if resp.status_code != 200 or "json" not in resp.headers.get("content-type", ""):
        raise ForeteesTeeTimesError(
            "booking_service_unavailable",
            f"Booking service unavailable (HTTP {resp.status_code}).",
        )

    data = resp.json()
    if data.get("status") != "ok":
        raise ForeteesTeeTimesError(
            "booking_service_unavailable",
            "Booking service returned an unexpected tee-times response.",
        )
    slots = data.get("slots")
    if not isinstance(slots, list):
        raise ForeteesTeeTimesError(
            "booking_service_unavailable",
            "Booking service returned malformed tee-times slots.",
        )
    return slots
```

Optional: change instance method `ForeteesService.get_tee_times` to raise `NotImplementedError` or delegate — **do not leave the old scrape as the live path**. Prefer deleting the scrape body from `get_tee_times` and making callers use `fetch_tee_times_via_booking_agent` only (router Task 2). If other callers of `get_tee_times` exist, grep and update them.

```bash
rg -n "get_tee_times" backend/
```

- [ ] **Step 4: Run service tests — expect PASS**

```bash
cd backend && source venv/bin/activate && env -u DATABASE_URL pytest tests/unit/services/test_foretees_tee_times_proxy.py -q
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/foretees_service.py backend/tests/unit/services/test_foretees_tee_times_proxy.py
git commit -m "$(cat <<'EOF'
feat(foretees): fetch day sheet via booking-agent tee-times API

Replace silent empty-list failures with typed errors and a dedicated
~60s proxy to wgp-booking POST /tee-times.
EOF
)"
```

---

### Task 2: Router — per-user gate + map errors

**Files:**
- Modify: `backend/app/routers/foretees.py` (`get_tee_times`)
- Modify: `backend/tests/unit/routers/test_foretees_router.py` (`TestGetTeeTimes`)

**Interfaces:**
- Consumes: `fetch_tee_times_via_booking_agent`, `ForeteesTeeTimesError`, `decrypt`
- Produces: updated `GET /api/foretees/tee-times` behavior per spec table

- [ ] **Step 1: Rewrite failing/updated router tests**

Replace `TestGetTeeTimes` cases that patch `_get_user_service` for listing with:

```python
class TestGetTeeTimes:
    def setup_method(self):
        _clear_overrides()

    def teardown_method(self):
        _clear_overrides()

    def test_returns_401_without_auth(self):
        resp = client.get("/api/foretees/tee-times", params={"date": "2025-06-01"})
        assert resp.status_code in (401, 403)

    def test_returns_400_without_profile_credentials(self):
        _override_current_user(_fake_player(foretees_username=None, foretees_password_encrypted=None))
        resp = client.get("/api/foretees/tee-times", params={"date": "2025-06-01"})
        assert resp.status_code == 400
        assert "credential" in resp.json()["detail"].lower()

    @patch("app.routers.foretees.decrypt", return_value="plain-pass")
    @patch("app.routers.foretees.fetch_tee_times_via_booking_agent", new_callable=AsyncMock)
    def test_returns_200_with_slots(self, mock_fetch, _decrypt):
        _override_current_user(
            _fake_player(foretees_username="1453-smith", foretees_password_encrypted="enc")
        )
        mock_fetch.return_value = [{"time": "08:00 AM"}]
        resp = client.get("/api/foretees/tee-times", params={"date": "2025-06-01"})
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1
        mock_fetch.assert_awaited_once_with("1453-smith", "plain-pass", "2025-06-01")

    @patch("app.routers.foretees.decrypt", return_value="plain-pass")
    @patch("app.routers.foretees.fetch_tee_times_via_booking_agent", new_callable=AsyncMock)
    def test_returns_502_on_foretees_auth_failed(self, mock_fetch, _decrypt):
        from app.services.foretees_service import ForeteesTeeTimesError

        _override_current_user(
            _fake_player(foretees_username="1453-smith", foretees_password_encrypted="enc")
        )
        mock_fetch.side_effect = ForeteesTeeTimesError(
            "foretees_auth_failed", "ForeTees login failed for your saved credentials."
        )
        resp = client.get("/api/foretees/tee-times", params={"date": "2025-06-01"})
        assert resp.status_code == 502
        assert "ForeTees" in resp.json()["detail"] or "login" in resp.json()["detail"].lower()

    @patch("app.routers.foretees.os.getenv", side_effect=lambda k, d=None: d)
    def test_returns_200_disabled_when_foretees_flag_off(self, _getenv):
        # Keep existing disabled behavior if FORETEES_ENABLED gates the router.
        # If disabled is currently checked via service.config.enabled from _get_user_service,
        # implement disabled check via os.getenv("FORETEES_ENABLED") == "true" on this endpoint
        # OR keep reading get_foretees_service().config.enabled without using its scrape.
        ...
```

**Disabled behavior:** Preserve `FORETEES_ENABLED=false` → `200` + `data=[]`. Implement by checking env / singleton config **without** requiring per-user creds when disabled:

```python
if not get_foretees_service().config.enabled:
    return ApiResponse.success(data=[], message="ForeTees integration is disabled")
```

Run that check **before** the per-user creds gate.

Also keep `test_returns_422_without_date`.

- [ ] **Step 2: Run router tee-times tests — expect FAIL** on new expectations

```bash
cd backend && source venv/bin/activate && env -u DATABASE_URL pytest tests/unit/routers/test_foretees_router.py::TestGetTeeTimes -q
```

- [ ] **Step 3: Implement router `get_tee_times`**

Replace body of `get_tee_times` approximately with:

```python
@router.get("/tee-times")
@handle_api_errors(operation_name="get tee times")
async def get_tee_times(
    date: str,
    current_user: models.PlayerProfile = Depends(get_current_user),
) -> dict[str, Any]:
    if not get_foretees_service().config.enabled:
        return ApiResponse.success(data=[], message="ForeTees integration is disabled")

    if not current_user.foretees_username or not current_user.foretees_password_encrypted:
        raise HTTPException(
            status_code=400,
            detail="Configure your ForeTees credentials in Account before viewing tee times.",
        )

    try:
        password = decrypt(current_user.foretees_password_encrypted)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not read saved ForeTees credentials — please re-save them in Account.",
        ) from None

    try:
        slots = await fetch_tee_times_via_booking_agent(
            current_user.foretees_username, password, date
        )
    except ForeteesTeeTimesError as exc:
        status = 502
        raise HTTPException(status_code=status, detail=exc.message) from exc

    return ApiResponse.success(
        data=slots,
        message=f"Found {len(slots)} tee time slots for {date}",
    )
```

Add imports: `HTTPException` (if missing), `fetch_tee_times_via_booking_agent`, `ForeteesTeeTimesError`, keep `decrypt`.

Do **not** call `_get_user_service` / `service.close()` on this endpoint anymore.

- [ ] **Step 4: Run focused + related ForeTees router tests — expect PASS**

```bash
cd backend && source venv/bin/activate && env -u DATABASE_URL pytest tests/unit/routers/test_foretees_router.py -q
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/foretees.py backend/tests/unit/routers/test_foretees_router.py
git commit -m "$(cat <<'EOF'
feat(foretees): proxy tee-times list through booking agent

Require per-user ForeTees credentials and surface agent auth/sheet
failures as 502 instead of an empty day sheet.
EOF
)"
```

---

### Task 3: Docs + full backend gate

**Files:**
- Modify: `docs/architecture/COMPUTER_USE_BOOKING.md`
- Optionally note in `docs/superpowers/specs/2026-07-29-wire-foretees-tee-times-via-booking-agent-design.md` status → Implemented (only if you normally stamp specs; otherwise skip).

- [ ] **Step 1: Update architecture doc**

In the architecture / HTTP contract section, clarify:

```markdown
SPA → FastAPI `GET /api/foretees/tee-times` → booking-agent `POST /tee-times` (httpx, per-user creds).
Book/cancel remain Computer Use on the agent; list is not Computer Use.
```

Adjust any bullet that still says list reads stay only on FastAPI/httpx in-process.

- [ ] **Step 2: Run full backend gate**

```bash
cd backend && source venv/bin/activate && env -u DATABASE_URL ruff check app/ tests/ && env -u DATABASE_URL ruff format --check app/ tests/ && env -u DATABASE_URL pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic -q
```

Expected: all pass (or only pre-existing unrelated failures — do not merge if new failures).

- [ ] **Step 3: Commit docs**

```bash
git add docs/architecture/COMPUTER_USE_BOOKING.md
git commit -m "$(cat <<'EOF'
docs(foretees): list path proxies to booking-agent tee-times
EOF
)"
```

---

### Task 4: Manual smoke (after merge/deploy)

Not a code commit. After API Cloud Run deploys:

1. Member **without** ForeTees creds → tee sheet API `400` with configure message.
2. Member **with** creds → day sheet populates in SPA.
3. Junk / wrong ForeTees password saved → `502` login failed (not empty grid pretending success).

---

## Spec coverage checklist

| Spec requirement | Task |
|---|---|
| Replace FastAPI scrape for list | 1–2 |
| Per-user creds only | 2 |
| SPA GET unchanged | 2 (contract) |
| Empty list only on ok+empty slots | 1–2 |
| 400 missing creds / decrypt | 2 |
| 502 agent auth/sheet/transport | 1–2 |
| ~60s read timeout | 1 |
| Docs | 3 |
| No `/bookings` / no flag / no SPA change | (non-goals) |

## Placeholder / consistency self-review

- Function name `fetch_tee_times_via_booking_agent` and `ForeteesTeeTimesError.code` values are consistent across tasks.
- Disabled-integration path checked before creds gate.
- Book/cancel `_call_booking_service` left intact.
