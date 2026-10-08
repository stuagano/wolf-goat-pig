# Manage Admins In-App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Admins can grant/revoke admin on linked player profiles from the admin page, with `SUPER_ADMIN_EMAILS` as a permanent floor; three still-open admin-like endpoints get locked down; admin capabilities are documented.

**Architecture:** A stored `is_admin` flag on `player_profiles` is read by the single decision point `require_admin` (`backend/app/utils/admin_auth.py`) alongside the env allowlist, so all existing gated routes inherit it. A small `admin_grants` router (mounted under `/players/admin`) lists/grants/revokes; a new React tab drives it.

**Tech Stack:** FastAPI, SQLAlchemy, Postgres (startup SQL migrations) / SQLite (tests), React + Vitest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-08-manage-admins-design.md`

## Global Constraints

- One admin level. Env floor: emails in `SUPER_ADMIN_EMAILS` are always admins and can't be revoked via API/UI.
- The flag only counts on **exactly one active** profile linked to the login's Auth0 subject (`preferences.auth0_id`). Ambiguous or inactive → not admin. No email fallback for the flag.
- Only active profiles with a linked Auth0 login can be granted (else 400). A non-env admin can't revoke themselves (400).
- `is_admin` column uses `Integer` 0/1, matching `is_active` / `is_ai` on the same model (spec says boolean; integer is the established convention on this table).
- Run commands from the worktree root `/Users/stuart.gano/Documents/wolf-goat-pig/.worktrees/manage-admins`. Python: `backend/venv/bin/python` (symlink the main checkout's venv once: `ln -s /Users/stuart.gano/Documents/wolf-goat-pig/backend/venv backend/venv`; same for `frontend/node_modules`). Never commit those symlinks.
- Never edit code containing `!` via shell heredocs (zsh mangles it). Use Edit/Write.
- Commit messages: `<type>: <description>` and end with `Co-authored-by: Isaac <no-reply@databricks.com>`.

## Review Focus

- Admin whose login matches two profiles (a stray duplicate) → denied, not silently granted via whichever row comes first. Test in Task 1.
- Revoked admin with an open browser session → next API call is 403 (no caching of admin status). Test in Task 1.
- Granting a profile that was later retired → retire clears the flag, so it can't resurface on reactivation. Test in Task 2.
- Cron hitting `/callouts/run` after deploy without the GitHub secret → 503, Sunday emails stop. Covered by rollout step in Task 3 (secret added *before* merge) and a 503 test.
- Env admin removed from `SUPER_ADMIN_EMAILS` but still flagged in DB → still admin via flag (expected; documented in Task 5).

---

### Task 1: `is_admin` column + effective-admin check

**Files:**
- Modify: `backend/app/models.py` (PlayerProfile, after `is_ai` at ~line 243)
- Create: `backend/migrations/add_profile_admin_flag_postgres.sql`
- Modify: `backend/app/utils/admin_auth.py`
- Modify: `backend/app/routers/players.py:212-215` (`/me` role fields)
- Modify: `backend/app/schemas/players.py:92` (role Literal)
- Modify: `frontend/src/hooks/usePlayerProfile.js:191`, `frontend/src/components/ui/Navigation.jsx:37-39`
- Test: `backend/tests/unit/utils/test_admin_auth_profile_flag.py`

**Interfaces:**
- Produces: `admin_auth.admin_role(db: Session, auth0_user: dict) -> Literal["super_admin","admin","normal"]`; `admin_auth.is_profile_admin(db: Session, auth0_sub: str | None) -> bool`; `require_admin(auth0_user=Depends(get_current_auth0_user), db=Depends(get_db)) -> dict` (same object as `require_super_admin`). Model columns `PlayerProfile.is_admin` (int), `admin_granted_by` (str|None), `admin_granted_at` (str|None).

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/unit/utils/test_admin_auth_profile_flag.py` (create `backend/tests/unit/utils/__init__.py` only if sibling test dirs have one — check `ls backend/tests/unit/routers/__init__.py`):

```python
"""Effective admin = env allowlist OR a flagged, active, uniquely-linked profile."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import PlayerProfile
from app.services.auth_service import get_current_auth0_user


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setattr("app.services.auth_service._send_welcome_email", lambda *args: None)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    with sessions() as db:
        db.add_all(
            [
                PlayerProfile(id=1, name="Flagged", email="flagged@example.com", is_admin=1,
                              preferences={"auth0_id": "auth0|flagged"}, created_at="2026-01-01"),
                PlayerProfile(id=2, name="Plain", email="plain@example.com",
                              preferences={"auth0_id": "auth0|plain"}, created_at="2026-01-01"),
                PlayerProfile(id=3, name="Retired", email=None, is_admin=1, is_active=0,
                              preferences={"auth0_id": "auth0|retired"}, created_at="2026-01-01"),
            ]
        )
        db.commit()

    def database():
        with sessions() as db:
            yield db

    monkeypatch.setenv("SUPER_ADMIN_EMAILS", "env@example.com")
    app.dependency_overrides[get_db] = database
    yield TestClient(app), sessions
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_auth0_user, None)
    engine.dispose()


def login(sub, email):
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": sub, "email": email}


ADMIN_ONLY = "/players/admin/account-links?query=xx"


def test_env_admin_passes_without_profile(env):
    client, _ = env
    login("auth0|nobody", "env@example.com")
    assert client.get(ADMIN_ONLY).status_code == 200


def test_flagged_linked_profile_passes(env):
    client, _ = env
    login("auth0|flagged", "flagged@example.com")
    assert client.get(ADMIN_ONLY).status_code == 200


def test_unflagged_profile_is_forbidden(env):
    client, _ = env
    login("auth0|plain", "plain@example.com")
    assert client.get(ADMIN_ONLY).status_code == 403


def test_flagged_but_inactive_is_forbidden(env):
    client, _ = env
    login("auth0|retired", "retired@example.com")
    assert client.get(ADMIN_ONLY).status_code == 403


def test_subject_matching_two_profiles_is_forbidden(env):
    client, sessions = env
    with sessions() as db:
        db.add(PlayerProfile(id=4, name="Dupe", is_admin=1, preferences={"auth0_id": "auth0|flagged"},
                             created_at="2026-01-01"))
        db.commit()
    login("auth0|flagged", "flagged@example.com")
    assert client.get(ADMIN_ONLY).status_code == 403


def test_revoke_takes_effect_on_next_request(env):
    client, sessions = env
    login("auth0|flagged", "flagged@example.com")
    assert client.get(ADMIN_ONLY).status_code == 200
    with sessions() as db:
        db.get(PlayerProfile, 1).is_admin = 0
        db.commit()
    assert client.get(ADMIN_ONLY).status_code == 403


def test_me_reports_admin_role_for_flagged_profile(env):
    client, _ = env
    login("auth0|flagged", "flagged@example.com")
    body = client.get("/players/me").json()
    assert (body["role"], body["is_admin"], body["is_super_admin"]) == ("admin", True, False)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && venv/bin/python -m pytest tests/unit/utils/test_admin_auth_profile_flag.py -q -p no:warnings`
Expected: FAIL — `TypeError: 'is_admin' is an invalid keyword argument for PlayerProfile`.

- [ ] **Step 3: Add the columns and migration**

In `backend/app/models.py`, directly after `is_ai = Column(Integer, default=0)` in `PlayerProfile`:

```python
    # In-app admin grant (in addition to the SUPER_ADMIN_EMAILS env floor).
    # Only honored on an active profile uniquely linked to the login's Auth0 ID.
    is_admin = Column(Integer, default=0, nullable=False)
    admin_granted_by = Column(String, nullable=True)  # email of the granting admin
    admin_granted_at = Column(String, nullable=True)  # ISO timestamp
```

Create `backend/migrations/add_profile_admin_flag_postgres.sql`:

```sql
ALTER TABLE player_profiles ADD COLUMN IF NOT EXISTS is_admin INTEGER NOT NULL DEFAULT 0;
ALTER TABLE player_profiles ADD COLUMN IF NOT EXISTS admin_granted_by VARCHAR;
ALTER TABLE player_profiles ADD COLUMN IF NOT EXISTS admin_granted_at VARCHAR;
```

- [ ] **Step 4: Implement effective admin in `admin_auth.py`**

Replace the `require_super_admin` function and the trailing alias with:

```python
def is_profile_admin(db: Session, auth0_sub: str | None) -> bool:
    """True only for exactly one active, flagged profile linked to this Auth0 subject."""
    if not auth0_sub:
        return False
    matches = (
        db.query(PlayerProfile)
        .filter(PlayerProfile.preferences["auth0_id"].as_string() == auth0_sub)
        .limit(2)
        .all()
    )
    return len(matches) == 1 and bool(matches[0].is_active) and bool(matches[0].is_admin)


def admin_role(db: Session, auth0_user: dict[str, Any]) -> Literal["super_admin", "admin", "normal"]:
    """Env allowlist first (no DB hit), then the stored profile flag."""
    if is_super_admin_email(auth0_user.get("email")):
        return "super_admin"
    if is_profile_admin(db, auth0_user.get("sub")):
        return "admin"
    return "normal"


def require_admin(
    auth0_user: dict[str, Any] = Depends(get_current_auth0_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Require an env-allowlisted email or an in-app admin grant."""
    if admin_role(db, auth0_user) == "normal":
        raise HTTPException(status_code=403, detail="Super-admin access required")
    return auth0_user


# Compatibility name; dependency overrides keyed on either name hit the same object.
require_super_admin = require_admin
```

Update imports at the top of the file:

```python
import os
from typing import Any, Literal

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PlayerProfile
from ..services.auth_service import get_current_auth0_user
```

- [ ] **Step 5: `/me` and schema**

In `backend/app/schemas/players.py:92` change to `role: Literal["normal", "admin", "super_admin"] = "normal"`.

In `backend/app/routers/players.py`, replace the three lines setting `is_super_admin`, `is_admin`, `role` in `get_my_profile` with:

```python
    profile.role = admin_role(db, auth0_user)
    profile.is_super_admin = profile.role == "super_admin"
    profile.is_admin = profile.role != "normal"
```

and add `admin_role` to the existing `from ..utils.admin_auth import ...` line.

In `frontend/src/hooks/usePlayerProfile.js:191` change `isAdmin: profile ? !!profile.is_super_admin : null,` to `isAdmin: profile ? !!profile.is_admin : null,`.
In `frontend/src/components/ui/Navigation.jsx` change `const { isSuperAdmin, profile } = usePlayerProfile();` to `const { isAdmin, profile } = usePlayerProfile();` and `isSuperAdmin === true` to `isAdmin === true` on line 39 (check the file for any other `isSuperAdmin` use and switch it too).

- [ ] **Step 6: Run tests**

Run: `cd backend && venv/bin/python -m pytest tests/unit/utils/test_admin_auth_profile_flag.py tests/unit/routers/test_account_links.py tests/unit/routers/test_players_router.py -q -p no:warnings`
Expected: all PASS.
Run: `cd frontend && npx vitest run src/components/ui src/hooks src/components/admin` — expected PASS (update any test that mocks `is_super_admin` for nav visibility to also set `is_admin: true`).

- [ ] **Step 7: Commit**

```bash
git add backend/app/models.py backend/migrations/add_profile_admin_flag_postgres.sql backend/app/utils/admin_auth.py backend/app/routers/players.py backend/app/schemas/players.py backend/tests/unit/utils frontend/src/hooks/usePlayerProfile.js frontend/src/components/ui/Navigation.jsx
git commit -m "feat: honor an in-app admin flag alongside the env allowlist"
```

---

### Task 2: Grant / revoke / list API; retire clears the flag

**Files:**
- Create: `backend/app/routers/admin_grants.py`
- Modify: `backend/app/routers/players.py:39,82` (mount)
- Modify: `backend/app/services/player_service.py` (`delete_player_profile`)
- Modify: `backend/openapi.json`, `frontend/src/api/schema.d.ts` (regenerated)
- Test: `backend/tests/unit/routers/test_admin_grants.py`

**Interfaces:**
- Consumes: `admin_auth.require_admin`, `admin_auth.get_super_admin_emails()`, `admin_auth.is_super_admin_email(email)`, model columns from Task 1.
- Produces: `GET /players/admin/admins` → `{"env_admins": [str], "profile_admins": [AdminRow]}`; `POST /players/admin/admins/{player_id}` → `AdminRow`; `DELETE /players/admin/admins/{player_id}` → `AdminRow`. `AdminRow = {id, name, legacy_name, email, auth0_id, is_admin: bool, admin_granted_by, admin_granted_at}`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/unit/routers/test_admin_grants.py`:

```python
"""In-app admin grants: list, grant, revoke, and their guard rails."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import PlayerProfile
from app.services.auth_service import get_current_auth0_user


@pytest.fixture
def grants(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    with sessions() as db:
        db.add_all(
            [
                PlayerProfile(id=1, name="Env Admin", email="env@example.com",
                              preferences={"auth0_id": "auth0|env"}, created_at="2026-01-01"),
                PlayerProfile(id=2, name="Linked", email="linked@example.com",
                              preferences={"auth0_id": "auth0|linked"}, created_at="2026-01-01"),
                PlayerProfile(id=3, name="Unlinked", created_at="2026-01-01"),
            ]
        )
        db.commit()

    def database():
        with sessions() as db:
            yield db

    monkeypatch.setenv("SUPER_ADMIN_EMAILS", "env@example.com")
    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": "auth0|env", "email": "env@example.com"}
    yield TestClient(app), sessions
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_auth0_user, None)
    engine.dispose()


def test_list_shows_env_admins_and_flagged_profiles(grants):
    client, _ = grants
    client.post("/players/admin/admins/2")
    body = client.get("/players/admin/admins").json()
    assert body["env_admins"] == ["env@example.com"]
    assert [row["id"] for row in body["profile_admins"]] == [2]


def test_grant_records_who_and_when_and_is_idempotent(grants):
    client, _ = grants
    first = client.post("/players/admin/admins/2")
    assert first.status_code == 200, first.text
    assert first.json()["is_admin"] is True
    assert first.json()["admin_granted_by"] == "env@example.com"
    assert first.json()["admin_granted_at"]
    again = client.post("/players/admin/admins/2")
    assert again.status_code == 200
    assert again.json()["admin_granted_at"] == first.json()["admin_granted_at"]


def test_grant_rejects_profile_without_login(grants):
    client, _ = grants
    resp = client.post("/players/admin/admins/3")
    assert resp.status_code == 400
    assert "sign in" in resp.json()["detail"].lower()


def test_grant_unknown_profile_is_404(grants):
    client, _ = grants
    assert client.post("/players/admin/admins/999").status_code == 404


def test_revoke_clears_flag_and_history(grants):
    client, _ = grants
    client.post("/players/admin/admins/2")
    resp = client.delete("/players/admin/admins/2")
    assert resp.status_code == 200
    assert (resp.json()["is_admin"], resp.json()["admin_granted_by"]) == (False, None)


def test_env_admin_cannot_be_revoked(grants):
    client, _ = grants
    resp = client.delete("/players/admin/admins/1")
    assert resp.status_code == 400
    assert "deployment config" in resp.json()["detail"]


def test_non_env_admin_cannot_revoke_self(grants):
    client, _ = grants
    client.post("/players/admin/admins/2")
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": "auth0|linked", "email": "linked@example.com"}
    resp = client.delete("/players/admin/admins/2")
    assert resp.status_code == 400
    assert "another admin" in resp.json()["detail"]


def test_flagged_admin_can_grant_others(grants):
    client, sessions = grants
    client.post("/players/admin/admins/2")
    with sessions() as db:
        db.add(PlayerProfile(id=4, name="Third", email="third@example.com",
                             preferences={"auth0_id": "auth0|third"}, created_at="2026-01-01"))
        db.commit()
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": "auth0|linked", "email": "linked@example.com"}
    assert client.post("/players/admin/admins/4").json()["admin_granted_by"] == "linked@example.com"


def test_non_admin_is_forbidden(grants):
    client, _ = grants
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": "auth0|linked", "email": "linked@example.com"}
    assert client.get("/players/admin/admins").status_code == 403


def test_retiring_a_profile_clears_admin(grants):
    client, sessions = grants
    client.post("/players/admin/admins/2")
    assert client.delete("/players/2").status_code == 200
    with sessions() as db:
        player = db.get(PlayerProfile, 2)
        assert (player.is_admin, player.admin_granted_by, player.admin_granted_at) == (0, None, None)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && venv/bin/python -m pytest tests/unit/routers/test_admin_grants.py -q -p no:warnings`
Expected: FAIL — 404s on `/players/admin/admins`.

- [ ] **Step 3: Implement the router**

Create `backend/app/routers/admin_grants.py`:

```python
"""In-app admin grants on linked player profiles; SUPER_ADMIN_EMAILS stays the floor."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PlayerProfile
from ..utils.admin_auth import get_super_admin_emails, is_super_admin_email, require_admin
from ..utils.time import utc_now

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/admins", tags=["players"])


def _row(player: PlayerProfile) -> dict[str, Any]:
    return {
        "id": player.id,
        "name": player.name,
        "legacy_name": player.legacy_name,
        "email": player.email,
        "auth0_id": (player.preferences or {}).get("auth0_id"),
        "is_admin": bool(player.is_admin),
        "admin_granted_by": player.admin_granted_by,
        "admin_granted_at": player.admin_granted_at,
    }


def _get(db: Session, player_id: int) -> PlayerProfile:
    player = db.query(PlayerProfile).filter(PlayerProfile.id == player_id).with_for_update().first()
    if not player:
        raise HTTPException(status_code=404, detail="Player profile not found")
    return player


@router.get("", dependencies=[Depends(require_admin)])
def list_admins(db: Session = Depends(get_db)) -> dict[str, Any]:
    flagged = (
        db.query(PlayerProfile)
        .filter(PlayerProfile.is_admin == 1, PlayerProfile.is_active == 1)
        .order_by(PlayerProfile.id)
        .all()
    )
    return {"env_admins": sorted(get_super_admin_emails()), "profile_admins": [_row(p) for p in flagged]}


@router.post("/{player_id}")
def grant_admin(
    player_id: int, actor: dict[str, Any] = Depends(require_admin), db: Session = Depends(get_db)
) -> dict[str, Any]:
    player = _get(db, player_id)
    if not player.is_active or not (player.preferences or {}).get("auth0_id"):
        raise HTTPException(status_code=400, detail="This profile needs to sign in (and be linked) before it can be made an admin.")
    if not player.is_admin:
        player.is_admin = 1
        player.admin_granted_by = actor.get("email")
        player.admin_granted_at = utc_now().isoformat()
        db.commit()
        logger.info("Admin granted to profile %s by %s", player.id, actor.get("email"))
    return _row(player)


@router.delete("/{player_id}")
def revoke_admin(
    player_id: int, actor: dict[str, Any] = Depends(require_admin), db: Session = Depends(get_db)
) -> dict[str, Any]:
    player = _get(db, player_id)
    if is_super_admin_email(player.email):
        raise HTTPException(status_code=400, detail="This admin is set in the deployment config and can't be removed here.")
    actor_is_env = is_super_admin_email(actor.get("email"))
    if not actor_is_env and (player.preferences or {}).get("auth0_id") == actor.get("sub"):
        raise HTTPException(status_code=400, detail="You can't remove your own admin access. Ask another admin.")
    if player.is_admin:
        player.is_admin = 0
        player.admin_granted_by = None
        player.admin_granted_at = None
        db.commit()
        logger.info("Admin revoked from profile %s by %s", player.id, actor.get("email"))
    return _row(player)
```

Mount it in `backend/app/routers/players.py` next to the account-links router:

```python
from .account_links import router as account_links_router
from .admin_grants import router as admin_grants_router
...
router.include_router(account_links_router)
router.include_router(admin_grants_router)
```

**Route-order check:** `players.py` also defines `/{player_id}` routes. Included routers are appended where `include_router` is called; confirm `/players/admin/admins` isn't captured by `GET /players/{player_id}` (int path param won't match `admin`, so FastAPI returns 422 — if the list test gets 422, move the `include_router` call above the `/{player_id}` route definitions, matching where `account_links_router` is included at line 82).

- [ ] **Step 4: Retire clears the flag**

In `backend/app/services/player_service.py` `delete_player_profile`, after the `player.preferences = {...}` line added in PR #371:

```python
            player.is_admin = 0
            player.admin_granted_by = None
            player.admin_granted_at = None
```

- [ ] **Step 5: Run tests, regenerate contract**

Run: `cd backend && venv/bin/python -m pytest tests/unit/routers/test_admin_grants.py tests/unit/utils -q -p no:warnings` → PASS.
Run: `PATH=$PWD/backend/venv/bin:$PATH ./scripts/sync_openapi.sh` → "in sync".

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/admin_grants.py backend/app/routers/players.py backend/app/services/player_service.py backend/tests/unit/routers/test_admin_grants.py backend/openapi.json frontend/src/api/schema.d.ts
git commit -m "feat: admin grant/revoke API with env floor and self-revoke guard"
```

---

### Task 3: Lock down the still-open admin-like endpoints

**Files:**
- Modify: `backend/app/routers/health.py` (`/admin/ensure-schema`, `/admin/seed-course-holes`)
- Modify: `backend/app/routers/callouts.py:56` (`/callouts/run`)
- Modify: `.github/workflows/callout-list.yml` (pass the secret)
- Modify: `backend/tests/unit/routers/test_callouts_router.py`
- Test: `backend/tests/unit/routers/test_open_admin_endpoints_locked.py`

**Interfaces:**
- Consumes: `admin_auth.require_admin`; `internal_jobs._require_job_token(supplied: str | None) -> None` (raises 503 unset / 403 wrong).

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/unit/routers/test_open_admin_endpoints_locked.py`:

```python
"""Endpoints that used to be callable anonymously."""

import pytest
from fastapi.testclient import TestClient

from app import routers
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("path", ["/admin/ensure-schema", "/admin/seed-course-holes"])
def test_schema_tools_reject_anonymous(path):
    assert client.post(path).status_code in (401, 403)


def test_callout_run_disabled_without_configured_token(monkeypatch):
    monkeypatch.delenv("INTERNAL_JOB_TOKEN", raising=False)
    assert client.post("/callouts/run?window=pre_pairing").status_code == 503


def test_callout_run_rejects_wrong_token(monkeypatch):
    monkeypatch.setenv("INTERNAL_JOB_TOKEN", "right")
    resp = client.post("/callouts/run?window=pre_pairing", headers={"X-Internal-Job-Token": "wrong"})
    assert resp.status_code == 403


def test_callout_run_accepts_right_token(monkeypatch):
    monkeypatch.setenv("INTERNAL_JOB_TOKEN", "right")
    monkeypatch.setattr(routers.callouts, "run_callout_for_next_sunday", lambda db, window: {"sent": 0})
    resp = client.post("/callouts/run?window=pre_pairing", headers={"X-Internal-Job-Token": "right"})
    assert resp.status_code == 200
```

(Check `test_callouts_router.py:28-40` for the exact attribute it monkeypatches and the response shape; mirror it here if it differs.)

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && venv/bin/python -m pytest tests/unit/routers/test_open_admin_endpoints_locked.py -q -p no:warnings`
Expected: FAIL (schema tools return 200/500; callout run returns 200 without token).

- [ ] **Step 3: Implement**

`health.py`: add `from fastapi import Depends` to the existing fastapi import if missing, `from ..utils.admin_auth import require_admin`, and change both decorators:

```python
@router.post("/admin/ensure-schema", dependencies=[Depends(require_admin)])
...
@router.post("/admin/seed-course-holes", dependencies=[Depends(require_admin)])
```

`callouts.py`: import `Header` from fastapi and `from .internal_jobs import _require_job_token`, then:

```python
def _require_cron_token(x_internal_job_token: str | None = Header(default=None)) -> None:
    _require_job_token(x_internal_job_token)


@router.post("/run", dependencies=[Depends(_require_cron_token)])
```

`.github/workflows/callout-list.yml`, in the `callout:` job after the `with:` block:

```yaml
    secrets:
      INTERNAL_JOB_TOKEN: ${{ secrets.INTERNAL_JOB_TOKEN }}
```

(Verify `_cron-curl.yml` declares `INTERNAL_JOB_TOKEN` under `on.workflow_call.secrets` — it does at line ~31; keep the name identical.)

- [ ] **Step 4: Keep existing callout tests valid**

In `backend/tests/unit/routers/test_callouts_router.py`, replace `client = TestClient(app)` with:

```python
import pytest

TOKEN = "test-job-token"
client = TestClient(app, headers={"X-Internal-Job-Token": TOKEN})


@pytest.fixture(autouse=True)
def _job_token(monkeypatch):
    monkeypatch.setenv("INTERNAL_JOB_TOKEN", TOKEN)
```

(Put `import pytest` with the other imports at the top.)

- [ ] **Step 5: Run tests**

Run: `cd backend && venv/bin/python -m pytest tests/unit/routers/test_open_admin_endpoints_locked.py tests/unit/routers/test_callouts_router.py tests/test_internal_jobs.py -q -p no:warnings` → PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/health.py backend/app/routers/callouts.py .github/workflows/callout-list.yml backend/tests/unit/routers/test_open_admin_endpoints_locked.py backend/tests/unit/routers/test_callouts_router.py
git commit -m "fix: require admin for schema tools and the job token for callouts/run"
```

---

### Task 4: Admins tab in the admin page

**Files:**
- Create: `frontend/src/pages/admin/AdminManager.jsx`
- Modify: `frontend/src/pages/AdminPage.jsx` (import ~line 12, tab button after "Account links" ~line 527, body after `{activeTab === 'players' && ...}` ~line 1001)
- Test: `frontend/src/pages/__tests__/AdminManager.test.jsx`

**Interfaces:**
- Consumes: Task 2 endpoints; `GET /players/admin/account-links?query=` → `{players: [{id, name, legacy_name, email, auth0_id, updated_at}], has_more}`; `useAuthenticatedFetch()`; `apiConfig.baseUrl`; `usePlayerProfile()` → `{ profile, isSuperAdmin }`.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/pages/__tests__/AdminManager.test.jsx`:

```jsx
import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import AdminManager from '../admin/AdminManager';

const request = vi.fn();
vi.mock('../../hooks/useAuthenticatedFetch', () => ({ useAuthenticatedFetch: () => request }));
vi.mock('../../hooks/usePlayerProfile', () => ({ usePlayerProfile: () => ({ profile: { id: 9 }, isSuperAdmin: true }) }));
vi.mock('../../components/ui', () => ({ Card: ({ children }) => <div>{children}</div> }));

const ok = data => ({ ok: true, json: async () => data });
const jeff = { id: 2, name: 'Jeff Green', legacy_name: 'Jeff Green', email: 'j@example.com', auth0_id: 'auth0|j', is_admin: true, admin_granted_by: 'env@example.com', admin_granted_at: '2026-10-08T10:00:00' };

beforeEach(() => { request.mockReset(); vi.spyOn(window, 'confirm').mockReturnValue(true); });

test('shows env admins as locked and flagged profiles with who granted them', async () => {
  request.mockResolvedValueOnce(ok({ env_admins: ['env@example.com'], profile_admins: [jeff] }));
  render(<AdminManager />);
  expect(await screen.findByText('env@example.com')).toBeInTheDocument();
  expect(screen.getByText(/Set in deployment config/)).toBeInTheDocument();
  expect(screen.getByText(/granted by env@example.com/)).toBeInTheDocument();
});

test('remove calls DELETE for that profile', async () => {
  request.mockResolvedValueOnce(ok({ env_admins: [], profile_admins: [jeff] }));
  render(<AdminManager />);
  request.mockResolvedValueOnce(ok({ ...jeff, is_admin: false }));
  fireEvent.click(await screen.findByRole('button', { name: 'Remove admin Jeff Green' }));
  await screen.findByText(/Removed admin/);
  expect(request.mock.calls[1][0]).toMatch(/\/players\/admin\/admins\/2$/);
  expect(request.mock.calls[1][1]).toEqual({ method: 'DELETE' });
});

test('search offers Make admin only for linked profiles', async () => {
  request.mockResolvedValueOnce(ok({ env_admins: [], profile_admins: [] }));
  render(<AdminManager />);
  request.mockResolvedValueOnce(ok({ players: [
    { id: 5, name: 'Linked Player', email: 'l@example.com', auth0_id: 'auth0|l' },
    { id: 6, name: 'Never Signed In', email: null, auth0_id: null },
  ] }));
  fireEvent.change(await screen.findByLabelText('Find a player'), { target: { value: 'pla' } });
  fireEvent.click(screen.getByRole('button', { name: 'Search' }));
  expect(await screen.findByRole('button', { name: 'Make admin Linked Player' })).toBeInTheDocument();
  expect(screen.getByText('Needs to sign in first')).toBeInTheDocument();
  request.mockResolvedValueOnce(ok({ id: 5, name: 'Linked Player', is_admin: true, admin_granted_by: 'me@example.com', admin_granted_at: 'now' }));
  fireEvent.click(screen.getByRole('button', { name: 'Make admin Linked Player' }));
  await screen.findByText(/Linked Player is now an admin/);
  expect(request.mock.calls[2][1]).toEqual({ method: 'POST' });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `cd frontend && npx vitest run src/pages/__tests__/AdminManager.test.jsx`
Expected: FAIL — cannot resolve `../admin/AdminManager`.

- [ ] **Step 3: Implement `AdminManager.jsx`**

Create `frontend/src/pages/admin/AdminManager.jsx`:

```jsx
import React, { useCallback, useEffect, useState } from 'react';
import { useAuthenticatedFetch } from '../../hooks/useAuthenticatedFetch';
import { usePlayerProfile } from '../../hooks/usePlayerProfile';
import { Card } from '../../components/ui';
import { apiConfig } from '../../config/api.config';

const inputClass = 'w-full px-3 py-2 border border-gray-300 rounded-lg';
const buttonClass = 'px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50';
const label = player => player.legacy_name || player.name;

export default function AdminManager() {
  const request = useAuthenticatedFetch();
  const { profile, isSuperAdmin } = usePlayerProfile();
  const [admins, setAdmins] = useState(null);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const jsonRequest = useCallback(async (path, options) => {
    const response = await request(`${apiConfig.baseUrl}${path}`, options);
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Request failed. Try again.');
    return data;
  }, [request]);

  const load = useCallback(async () => {
    try { setAdmins(await jsonRequest('/players/admin/admins')); }
    catch (err) { setError(err.message); }
  }, [jsonRequest]);

  useEffect(() => { load(); }, [load]);

  const run = async (action, message) => {
    setBusy(true); setError(''); setSuccess('');
    try { await action(); setSuccess(message); await load(); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  const search = async event => {
    event.preventDefault();
    setBusy(true); setError(''); setResults(null);
    try { setResults((await jsonRequest(`/players/admin/account-links?query=${encodeURIComponent(query.trim())}`)).players); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  const grant = player => run(
    () => jsonRequest(`/players/admin/admins/${player.id}`, { method: 'POST' }),
    `${label(player)} is now an admin.`,
  );

  const revoke = player => {
    if (!window.confirm(`Remove admin access for ${label(player)}?`)) return;
    run(() => jsonRequest(`/players/admin/admins/${player.id}`, { method: 'DELETE' }), `Removed admin access for ${label(player)}.`);
  };

  return (
    <Card className="p-6 space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Admins</h2>
        <p className="text-gray-600 mt-2">Admins can use every tab on this page. See docs/admin-permissions.md in the repo for the full list of what that includes.</p>
      </div>
      {error && <div role="alert" className="p-3 rounded-lg bg-red-50 text-red-800">{error}</div>}
      {success && <div role="status" className="p-3 rounded-lg bg-green-50 text-green-800">{success}</div>}
      {admins && <ul className="divide-y">
        {admins.env_admins.map(email => <li key={email} className="py-2">
          <strong>{email}</strong>
          <div className="text-sm text-gray-500">Set in deployment config — can't be removed here.</div>
        </li>)}
        {admins.profile_admins.map(player => <li key={player.id} className="py-2 flex items-center justify-between gap-3">
          <div>
            <strong>{label(player)}</strong> <span className="text-gray-500">{player.email}</span>
            <div className="text-sm text-gray-500">granted by {player.admin_granted_by || 'unknown'}{player.admin_granted_at ? ` on ${player.admin_granted_at.slice(0, 10)}` : ''}</div>
          </div>
          {(isSuperAdmin || player.id !== profile?.id) && (
            <button type="button" className="text-red-700 underline" disabled={busy} onClick={() => revoke(player)} aria-label={`Remove admin ${label(player)}`}>Remove</button>
          )}
        </li>)}
      </ul>}
      <form onSubmit={search} className="flex flex-wrap items-end gap-3 border-t pt-5">
        <label className="flex-1 min-w-48"><span className="block font-medium mb-1">Find a player</span>
          <input className={inputClass} value={query} onChange={event => setQuery(event.target.value)} required minLength={2} maxLength={100} placeholder="Name or email" disabled={busy} />
        </label>
        <button className={buttonClass} disabled={busy || query.trim().length < 2}>Search</button>
      </form>
      {results?.length === 0 && <p>No matching profiles.</p>}
      {results?.length > 0 && <ul className="divide-y">{results.map(player => <li key={player.id} className="py-2 flex items-center justify-between gap-3">
        <div><strong>{label(player)}</strong> <span className="text-gray-500">{player.email || 'No email'}</span></div>
        {player.auth0_id
          ? <button type="button" className={buttonClass} disabled={busy} onClick={() => grant(player)} aria-label={`Make admin ${label(player)}`}>Make admin</button>
          : <span className="text-sm text-gray-500">Needs to sign in first</span>}
      </li>)}</ul>}
    </Card>
  );
}
```

Note the success text must match the tests: the remove test looks for `/Removed admin/` (matches "Removed admin access for …"), the grant test looks for `/Linked Player is now an admin/`.

- [ ] **Step 4: Wire the tab in `AdminPage.jsx`**

Add `import AdminManager from './admin/AdminManager';` after the `AccountLinkingManager` import. After the "👤 Account links" `</button>`, add:

```jsx
          <button
            onClick={() => setActiveTab('admins')}
            className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
              activeTab === 'admins'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            🔑 Admins
          </button>
```

After `{activeTab === 'players' && <AccountLinkingManager />}` add:

```jsx

        {/* Admins Tab */}
        {activeTab === 'admins' && <AdminManager />}
```

- [ ] **Step 5: Run tests**

Run: `cd frontend && npx vitest run src/pages/__tests__/AdminManager.test.jsx src/pages/__tests__` → PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/admin/AdminManager.jsx frontend/src/pages/AdminPage.jsx frontend/src/pages/__tests__/AdminManager.test.jsx
git commit -m "feat: Admins tab to grant and remove admin access"
```

---

### Task 5: Document admin permissions

**Files:**
- Create: `docs/admin-permissions.md`

- [ ] **Step 1: Write the doc**

Create `docs/admin-permissions.md` with these sections, filling each route list from the current code (`rg -n "require_admin" backend/app` — verify every line before writing it):

1. **Who is an admin** — env floor (`SUPER_ADMIN_EMAILS` in `deploy/gcp/phase1-cloud-run/env.production.yaml`, currently `stuagano@gmail.com`, `greenjs@gmail.com`; change = edit + redeploy) and in-app grants (Admin page → 🔑 Admins). Rules: grant needs a signed-in, linked profile; env admins can't be removed in the app; you can't remove yourself unless you're on the env list; retiring a profile removes its admin; a login matching two profiles gets no admin until fixed in Account links. Note: removing someone from the env list doesn't remove an in-app grant on their profile.
2. **What admins can do**, one table per area with columns *Action · Where (tab or endpoint) · Notes*, marking ⚠️ destructive and ✉️ sends email / touches an external system:
   - Accounts & profiles: account-links search, relink, retire (DELETE /players/{id}), read/edit any profile (GET/PUT /players/{id}), manage admins
   - Roster & signups: add roster name, list/promote/dismiss pending new players
   - Data sync: ⚠️ Sheets sync (`POST /data/sync-sheets`, empties and reloads `legacy_rounds`)
   - Email & comms: ✉️ email config + test sends, Gmail OAuth2 setup + credential upload, ✉️ callout test email, GroupMe groups list
   - Banners & feature flags: banner CRUD, feature toggles (foretees, scorecard_scan, livsow, commissioner_chat, stuart_mode)
   - Badges: check achievements, list holders, backfill career badges
   - LivSOW: seed team starters, set official logos, delete transactions
   - Database & system: browse schemas/tables, database stats, ⚠️ delete orphaned games, ⚠️ run migrations, ⚠️ delete all match records (`DELETE /admin/matches`), ensure-schema, seed course holes, debug paths
3. **Not admin-gated by design** — `/callouts/run` and `/internal/jobs/*` (cron, `INTERNAL_JOB_TOKEN`), `/health/external` (`MONITOR_KEY`).
4. **Known gaps** — public `GET /players` exposes email/Auth0 IDs; `POST /players` unauthenticated; no audit log of admin actions.

- [ ] **Step 2: Commit**

```bash
git add docs/admin-permissions.md
git commit -m "docs: what admins can do and how admin access is managed"
```

---

### Task 6: Full gate, capabilities, PR

- [ ] **Step 1: Backend gate** — `cd backend && venv/bin/ruff check app/ tests/ && venv/bin/ruff format --check app/ tests/ && venv/bin/python scripts/export_openapi.py --check && venv/bin/python -m pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic -q -p no:warnings`. Only acceptable failure: `tests/infra/startup_test.py` (local proxy).
- [ ] **Step 2: Frontend gate** — `cd frontend && npm run typecheck && npx vitest run && npm run build`, then `git checkout -- frontend/public/service-worker.js frontend/public/version.json` (build artifacts).
- [ ] **Step 3: Capabilities** — `PYTHONPATH=.ctk backend/venv/bin/python -m caps status`; re-verify every `[STALE]` one with `caps verify --capability <id>`; commit `.ctk/ledger.json`.
- [ ] **Step 4: Rollout precondition** — confirm with the user that the `INTERNAL_JOB_TOKEN` GitHub secret exists (`gh secret list | grep INTERNAL_JOB_TOKEN`). Do not merge without it.
- [ ] **Step 5: Push + PR** — push `feat/manage-admins`, open PR with summary, the rollout precondition, and test plan; after merge + deploy verify `/health`, anonymous `POST /admin/ensure-schema` → 401/403, and manually dispatch `callout-list.yml` once → 200.
