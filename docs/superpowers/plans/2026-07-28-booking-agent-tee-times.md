# Booking-agent Tee-Times Read API — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `POST /tee-times` on the booking agent so a caller can list a day's ForeTees slots and who is playing, under that member's credentials, via httpx scrape.

**Architecture:** New `booking-agent/app/tee_sheet.py` ports Wingpoint login + ForeTees SSO + `Member_sheet` parse from the FastAPI ForeTees service. `main.py` exposes Bearer-authed `POST /tee-times`. SPA and FastAPI list paths stay unchanged. No Computer Use / Playwright for reads.

**Tech Stack:** FastAPI, httpx, pydantic-settings, pytest, pytest-asyncio, respx (mocked httpx).

**Spec:** `docs/superpowers/specs/2026-07-28-booking-agent-tee-times-design.md`

## Global Constraints

- Per-user ForeTees identity only: request body must include `username` and `password` (same pattern as `/book`).
- Slot JSON field names must match FastAPI `_parse_tee_sheet`: `date`, `time`, `front_back`, `players` (`name`/`transport`), `open_slots`, `max_players`, `ttdata`, `jump`, `p5_allowed`.
- Auth failure / sheet failure → HTTP `502` with `{ "status": "failed", "error": "…" }` — never disguise as empty `slots`.
- Empty `slots` only when auth + fetch succeeded and the sheet has no `Member_slot` rows.
- Do not import `backend/` packages into booking-agent.
- Do not wire SPA or FastAPI to this endpoint in this plan.
- NEVER edit source containing `!` via shell heredoc/perl/zsh — use Edit/Write tools.
- Booking-agent tests: `cd booking-agent && python -m pytest tests/ -q` (after creating venv + deps).

---

## File Structure

- Create: `booking-agent/app/tee_sheet.py` — login/SSO, fetch sheet, parse slots, typed errors.
- Modify: `booking-agent/app/main.py` — `TeeTimesRequest` + `POST /tee-times`.
- Modify: `booking-agent/requirements.txt` — add `httpx`.
- Create: `booking-agent/requirements-testing.txt` — pytest stack for local/CI agent tests.
- Create: `booking-agent/tests/conftest.py`, `booking-agent/tests/test_tee_sheet_parse.py`, `booking-agent/tests/test_tee_times_endpoint.py`, `booking-agent/tests/fixtures/member_sheet_sample.html`.
- Modify: `booking-agent/README.md` — document `/tee-times`.
- Modify: `docs/architecture/COMPUTER_USE_BOOKING.md` — reads available on agent via httpx; SPA still uses FastAPI.

---

### Task 1: Parser unit tests + `parse_tee_sheet`

**Files:**
- Create: `booking-agent/tests/fixtures/member_sheet_sample.html`
- Create: `booking-agent/tests/conftest.py`
- Create: `booking-agent/tests/test_tee_sheet_parse.py`
- Create: `booking-agent/app/tee_sheet.py` (parser only first)
- Create: `booking-agent/requirements-testing.txt`
- Modify: `booking-agent/requirements.txt`

**Interfaces:**
- Produces: `parse_tee_sheet(html_content: str, date: str) -> list[dict[str, Any]]`

- [ ] **Step 1: Add dependencies**

Append to `booking-agent/requirements.txt`:

```
httpx>=0.27.0
```

Create `booking-agent/requirements-testing.txt`:

```
-r requirements.txt
pytest>=8.0.0
pytest-asyncio>=0.24.0
respx>=0.21.0
httpx>=0.27.0
```

- [ ] **Step 2: Write sample fixture HTML**

Create `booking-agent/tests/fixtures/member_sheet_sample.html` with one real-shaped row (escape quotes in `data-ftjson` as HTML entities are fine; use `&quot;` or keep JSON simple):

```html
<div class="rwdTr">
  <a class="teetime_button" data-ftjson="{&quot;type&quot;:&quot;Member_slot&quot;,&quot;time:0&quot;:&quot;11:00 AM&quot;,&quot;ttdata&quot;:&quot;abc123&quot;,&quot;jump&quot;:7,&quot;p5&quot;:&quot;No&quot;,&quot;wasP1&quot;:&quot;Jane D&quot;,&quot;wasP2&quot;:&quot;&quot;,&quot;wasP3&quot;:&quot;&quot;,&quot;wasP4&quot;:&quot;&quot;,&quot;wasP5&quot;:&quot;&quot;}">11:00 AM</a>
  <div class="rwdTd pgCol"><div><span>Jane D</span><span>WLK</span></div></div>
  <div class="slotCount openSlots3 maxPlayers4"></div>
</div>
<div class="rwdTr">
  <a class="teetime_button" data-ftjson="{&quot;type&quot;:&quot;Other&quot;,&quot;jump&quot;:8}">ignore</a>
</div>
```

- [ ] **Step 3: Write the failing parser test**

```python
# booking-agent/tests/test_tee_sheet_parse.py
from pathlib import Path

from app.tee_sheet import parse_tee_sheet

FIXTURE = Path(__file__).parent / "fixtures" / "member_sheet_sample.html"


def test_parse_tee_sheet_extracts_players_and_open_slots():
    html = FIXTURE.read_text()
    slots = parse_tee_sheet(html, "2026-07-28")
    assert len(slots) == 1
    slot = slots[0]
    assert slot["date"] == "2026-07-28"
    assert slot["time"] == "11:00 AM"
    assert slot["ttdata"] == "abc123"
    assert slot["jump"] == 7
    assert slot["p5_allowed"] is False
    assert slot["players"] == [{"name": "Jane D", "transport": "WLK"}]
    assert slot["max_players"] == 4
    assert slot["open_slots"] == 3
    assert slot["front_back"] == "F"


def test_parse_tee_sheet_skips_non_member_slot():
    html = '<a data-ftjson="{&quot;type&quot;:&quot;Event&quot;,&quot;jump&quot;:1}"></a>'
    assert parse_tee_sheet(html, "2026-07-28") == []
```

Create empty `booking-agent/tests/conftest.py` (and `booking-agent/tests/__init__.py` if needed for imports). Prefer running pytest with `cd booking-agent` and `pythonpath=.` or install the package; simplest: put this in `conftest.py`:

```python
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
```

- [ ] **Step 4: Run to verify fail**

```bash
cd booking-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-testing.txt
pytest tests/test_tee_sheet_parse.py -q
```

Expected: `ModuleNotFoundError: No module named 'app.tee_sheet'` (or import error for `parse_tee_sheet`).

- [ ] **Step 5: Implement `parse_tee_sheet`**

Create `booking-agent/app/tee_sheet.py` with parser logic ported from `backend/app/services/foretees_service.py` `_parse_tee_sheet` (lines ~750–858). Keep the same regexes and field mapping. Export only:

```python
def parse_tee_sheet(html_content: str, date: str) -> list[dict[str, Any]]:
    ...
```

When CSS open-slot class is present, prefer `open_slots` from the class; if absent, use `max_players - len(players)` with default `max_players=4` (match FastAPI behavior: FastAPI overwrites open_count from max−players even when CSS present — **copy FastAPI exactly**: it sets `open_count = max_players - len(players)` after reading max from CSS). Mirror FastAPI literally so shapes stay identical.

- [ ] **Step 6: Run tests — expect PASS**

```bash
cd booking-agent && source .venv/bin/activate && pytest tests/test_tee_sheet_parse.py -q
```

- [ ] **Step 7: Commit**

```bash
git add booking-agent/requirements.txt booking-agent/requirements-testing.txt \
  booking-agent/app/tee_sheet.py booking-agent/tests/
git commit -m "$(cat <<'EOF'
feat(booking-agent): parse ForeTees Member_sheet slots

Port the FastAPI tee-sheet HTML parser so the booking agent can list
day slots and players without Computer Use.
EOF
)"
```

---

### Task 2: ForeTees session + fetch with typed failures

**Files:**
- Modify: `booking-agent/app/tee_sheet.py`
- Modify: `booking-agent/tests/test_tee_sheet_parse.py` (or new `test_tee_sheet_fetch.py`)

**Interfaces:**
- Consumes: `parse_tee_sheet`, `Settings` URLs from `get_settings()`
- Produces:
  - `class ForeteesAuthError(Exception)`
  - `class ForeteesSheetError(Exception)`
  - `async def fetch_tee_times(username: str, password: str, date: str, *, settings: Settings | None = None) -> list[dict[str, Any]]`

- [ ] **Step 1: Write failing fetch tests with respx**

```python
# booking-agent/tests/test_tee_sheet_fetch.py
import httpx
import pytest
import respx

from app.config import Settings
from app.tee_sheet import ForeteesAuthError, ForeteesSheetError, fetch_tee_times

settings = Settings(
    wingpoint_base="https://www.wingpointgolf.com",
    login_page="/public/member-login-465.html",
    tee_time_page="/members/golf/make-a-tee-time-703.html",
    foretees_base="https://ftapp.example/v5/club",
)


@pytest.mark.asyncio
@respx.mock
async def test_fetch_tee_times_happy_path(tmp_path):
    from pathlib import Path

    html = (Path(__file__).parent / "fixtures" / "member_sheet_sample.html").read_text()
    respx.get("https://www.wingpointgolf.com/public/member-login-465.html").mock(
        return_value=httpx.Response(200, text="login")
    )
    respx.post("https://www.wingpointgolf.com/public/member-login-465.html").mock(
        return_value=httpx.Response(200, text="ok")
    )
    respx.get("https://www.wingpointgolf.com/members/golf/make-a-tee-time-703.html").mock(
        return_value=httpx.Response(
            200,
            text="var ftSSOKey = 'KEY'; var ftSSOIV = 'IV';",
        )
    )
    respx.get("https://ftapp.example/v5/club/Member_select").mock(
        return_value=httpx.Response(200, text="sso")
    )
    respx.get("https://ftapp.example/v5/club/Member_sheet").mock(
        return_value=httpx.Response(200, text=html)
    )

    slots = await fetch_tee_times("u", "p", "2026-07-28", settings=settings)
    assert len(slots) == 1
    assert slots[0]["time"] == "11:00 AM"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_tee_times_auth_fails_without_sso():
    respx.get("https://www.wingpointgolf.com/public/member-login-465.html").mock(
        return_value=httpx.Response(200, text="login")
    )
    respx.post("https://www.wingpointgolf.com/public/member-login-465.html").mock(
        return_value=httpx.Response(200, text="ok")
    )
    respx.get("https://www.wingpointgolf.com/members/golf/make-a-tee-time-703.html").mock(
        return_value=httpx.Response(200, text="no sso vars here")
    )
    with pytest.raises(ForeteesAuthError):
        await fetch_tee_times("u", "p", "2026-07-28", settings=settings)
```

- [ ] **Step 2: Run — expect FAIL** (`ForeteesAuthError` / `fetch_tee_times` missing)

- [ ] **Step 3: Implement session + fetch in `tee_sheet.py`**

Port the login sequence from `ForeteesService._ensure_session` / `get_tee_times`:

1. GET login page, POST `UserLOGIN` / `UserPWD` / `btnLogon=Log On` / `Action=Authenticate` / `DocID=465` / etc. (same fields as backend).
2. GET tee time page; regex `ftSSOKey\s*=\s*'([^']+)'` and `ftSSOIV`.
3. Missing SSO → raise `ForeteesAuthError`.
4. GET `{foretees_base}/Member_select?sso_uid=…&sso_iv=…`.
5. GET `{foretees_base}/Member_sheet?calDate=MM/DD/YYYY&course=&displayOpt=0` (convert `YYYY-MM-DD` → `%m/%d/%Y`).
6. Sheet HTTP errors → `ForeteesSheetError`.
7. Return `parse_tee_sheet(resp.text, date)`.

Use a single `async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:` per call (no shared session store).

Validate `date` as `%Y-%m-%d` before fetch; invalid → raise `ValueError` (endpoint maps to 400).

- [ ] **Step 4: Run fetch tests — expect PASS**

```bash
cd booking-agent && source .venv/bin/activate && pytest tests/test_tee_sheet_fetch.py -q
```

- [ ] **Step 5: Commit**

```bash
git add booking-agent/app/tee_sheet.py booking-agent/tests/test_tee_sheet_fetch.py
git commit -m "$(cat <<'EOF'
feat(booking-agent): fetch day sheet under member ForeTees login

httpx login + SSO + Member_sheet; auth/sheet failures are typed so the
API can return 502 instead of an empty list.
EOF
)"
```

---

### Task 3: `POST /tee-times` endpoint

**Files:**
- Modify: `booking-agent/app/main.py`
- Create: `booking-agent/tests/test_tee_times_endpoint.py`

**Interfaces:**
- Consumes: `fetch_tee_times`, `ForeteesAuthError`, `ForeteesSheetError`, `_check_auth`
- Produces: `POST /tee-times` → `{ status, date, slots }` or error bodies per spec

- [ ] **Step 1: Write failing endpoint tests**

```python
# booking-agent/tests/test_tee_times_endpoint.py
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.tee_sheet import ForeteesAuthError


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("BOOKING_SERVICE_SECRET", "test-secret")
    from app.config import get_settings

    get_settings.cache_clear()
    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()


def test_tee_times_unauthorized(client):
    resp = client.post("/tee-times", json={"username": "u", "password": "p", "date": "2026-07-28"})
    assert resp.status_code == 401


def test_tee_times_missing_creds(client):
    resp = client.post(
        "/tee-times",
        headers={"Authorization": "Bearer test-secret"},
        json={"username": "", "password": "p", "date": "2026-07-28"},
    )
    assert resp.status_code == 400


def test_tee_times_ok(client):
    slots = [
        {
            "date": "2026-07-28",
            "time": "11:00 AM",
            "front_back": "F",
            "players": [{"name": "Jane D", "transport": "WLK"}],
            "open_slots": 3,
            "max_players": 4,
            "ttdata": "abc",
            "jump": 7,
            "p5_allowed": False,
        }
    ]
    with patch("app.main.fetch_tee_times", new=AsyncMock(return_value=slots)):
        resp = client.post(
            "/tee-times",
            headers={"Authorization": "Bearer test-secret"},
            json={"username": "u", "password": "p", "date": "2026-07-28"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["date"] == "2026-07-28"
    assert body["slots"] == slots


def test_tee_times_auth_failure_is_502(client):
    with patch(
        "app.main.fetch_tee_times",
        new=AsyncMock(side_effect=ForeteesAuthError("no sso")),
    ):
        resp = client.post(
            "/tee-times",
            headers={"Authorization": "Bearer test-secret"},
            json={"username": "u", "password": "p", "date": "2026-07-28"},
        )
    assert resp.status_code == 502
    assert resp.json() == {"status": "failed", "error": "foretees_auth_failed"}
```

- [ ] **Step 2: Run — expect FAIL** (404 on `/tee-times`)

- [ ] **Step 3: Implement endpoint in `main.py`**

```python
class TeeTimesRequest(BaseModel):
    username: str
    password: str
    date: str


@app.post("/tee-times")
async def tee_times(
    body: TeeTimesRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _check_auth(authorization)
    if not body.username.strip() or not body.password:
        raise HTTPException(status_code=400, detail="username and password required")
    if not body.date.strip():
        raise HTTPException(status_code=400, detail="date required (YYYY-MM-DD)")
    try:
        slots = await fetch_tee_times(body.username.strip(), body.password, body.date.strip())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ForeteesAuthError:
        raise HTTPException(
            status_code=502,
            detail={"status": "failed", "error": "foretees_auth_failed"},
        ) from None
    except ForeteesSheetError:
        raise HTTPException(
            status_code=502,
            detail={"status": "failed", "error": "foretees_sheet_failed"},
        ) from None
    return {"status": "ok", "date": body.date.strip(), "slots": slots}
```

**Note:** FastAPI wraps `detail` dicts as `{"detail": {…}}`. Spec wants top-level `{status, error}` on 502. Prefer returning via:

```python
from fastapi.responses import JSONResponse

return JSONResponse(
    status_code=502,
    content={"status": "failed", "error": "foretees_auth_failed"},
)
```

for auth/sheet failures (and keep `HTTPException` for 400/401). Update the test to match whichever you implement — **must match the spec's top-level body**.

- [ ] **Step 4: Run all booking-agent tests — expect PASS**

```bash
cd booking-agent && source .venv/bin/activate && pytest tests/ -q
```

- [ ] **Step 5: Commit**

```bash
git add booking-agent/app/main.py booking-agent/tests/test_tee_times_endpoint.py
git commit -m "$(cat <<'EOF'
feat(booking-agent): expose POST /tee-times for day sheet reads

Bearer-authed, per-member ForeTees credentials; returns slots and
players without changing the SPA/FastAPI list path.
EOF
)"
```

---

### Task 4: Docs + architecture note

**Files:**
- Modify: `booking-agent/README.md`
- Modify: `docs/architecture/COMPUTER_USE_BOOKING.md`

- [ ] **Step 1: Update README endpoints list**

Add under Endpoints:

```markdown
- `POST /tee-times` — list day's slots + players (body: `username`, `password`, `date`; httpx scrape, not Computer Use)
```

Add a short example:

```bash
curl -sS -X POST "$BOOKING_URL/tee-times" \
  -H "Authorization: Bearer $BOOKING_SERVICE_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"username":"…","password":"…","date":"2026-07-28"}'
```

- [ ] **Step 2: Update architecture doc**

In `docs/architecture/COMPUTER_USE_BOOKING.md`:

1. Add `/tee-times` to the HTTP contract table (Purpose: list day sheet + players via httpx).
2. Replace the Non-goals bullet that says tee-sheet reads stay on FastAPI with:

```markdown
- SPA/FastAPI still own the product list path (`GET /api/foretees/tee-times`); booking-agent also exposes `POST /tee-times` (httpx) for direct callers. Computer Use is not used for reads.
```

- [ ] **Step 3: Commit**

```bash
git add booking-agent/README.md docs/architecture/COMPUTER_USE_BOOKING.md
git commit -m "$(cat <<'EOF'
docs(booking-agent): document POST /tee-times day sheet API
EOF
)"
```

---

### Task 5: Manual smoke (optional, post-deploy)

Not a code commit. After merge auto-deploys `wgp-booking`:

```bash
curl -sS -o /tmp/tt.json -w '%{http_code}\n' -X POST \
  "https://wgp-booking-i5v2shrpoa-uc.a.run.app/tee-times" \
  -H "Authorization: Bearer $BOOKING_SERVICE_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"username":"<member>","password":"<pass>","date":"2026-07-28"}'
# expect 200 + status ok, or 502 with foretees_auth_failed
# junk Bearer → 401
```

---

## Spec coverage checklist

| Spec requirement | Task |
|---|---|
| `POST /tee-times` + Bearer auth | Task 3 |
| Body username/password/date | Task 3 |
| httpx login + Member_sheet | Task 2 |
| Slot shape matches FastAPI | Task 1 |
| 502 auth/sheet (not empty list) | Tasks 2–3 |
| No SPA/FastAPI wiring | (explicit non-goal) |
| Docs update | Task 4 |
| Parser unit tests | Task 1 |
| Auth 401 / validation 400 | Task 3 |

## Placeholder / consistency self-review

- No TBD/TODO left in steps.
- `fetch_tee_times` / `ForeteesAuthError` / `ForeteesSheetError` / `parse_tee_sheet` names are consistent across tasks.
- 502 response uses top-level `{status, error}` via `JSONResponse` (called out so tests match spec, not FastAPI `detail` wrapping).
