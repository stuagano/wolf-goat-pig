# Admin-Approved Account Claims Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When a returning player picks a roster name held by their login-less original profile, record a claim instead of failing, and let an admin approve it in one click (move login onto the original, retire the stray).

**Architecture:** A new `account_claims` table and `account_claim_service.py` hold the claim logic. `PUT /players/me/legacy-name` returns 202 with a pending claim when the name's holder has no login; `/players/me` reports `pending_claim`. A new admin router (`/players/admin/claims`) lists, approves (atomic identity move + retire) and dismisses. Frontend: the profile hook handles 202, onboarding shows a waiting note, and the Account links tab gets a Claim requests list.

**Tech Stack:** FastAPI, SQLAlchemy (Postgres prod via startup SQL migrations, SQLite tests), React + Vitest.

**Spec:** `docs/superpowers/specs/2026-10-09-account-claims-design.md`

## Global Constraints

- Admin approval required; picking a name never by itself hands over a profile's history.
- A claim is only created when the holder is **active and has no Auth0 login**; a holder with a login keeps today's 409.
- Requester must have `email_verified is True`, else 403.
- Retired (inactive) profiles do not hold roster names (`is_canonical_name_claimed` ignores them).
- Approval moves identity only (email, `preferences.auth0_id`, `legacy_name`, `name`) and retires the stray; records on the stray stay put.
- Player message (202): `"Request sent — a club admin will connect you to your history."`
- Claim statuses: `pending` · `approved` · `dismissed`; superseded claims → `dismissed` with `resolved_by="superseded"`.
- ORM rule from PR #373: never add an ORM attribute whose name matches a `PlayerProfileResponse` field (`from_attributes` would leak it). `pending_claim` is computed in `/me`, not stored on `PlayerProfile`.
- Run commands from the worktree root `/Users/stuart.gano/Documents/wolf-goat-pig/.worktrees/account-claims`. Python: `backend/venv/bin/python` (symlink once: `ln -s /Users/stuart.gano/Documents/wolf-goat-pig/backend/venv backend/venv`; same for `frontend/node_modules`). Never stage those symlinks or `.ctk/ledger.json`.
- Never edit code containing `!` via shell heredocs; use Edit/Write. Commit messages `<type>: <description>` ending with `Co-authored-by: Isaac <no-reply@databricks.com>`.

## Review Focus

- Player picks a name, then picks a **different** name before approval → the first claim is superseded, admins see only the latest. Test in Task 1.
- Admin approves after the original was already linked another way (e.g. hand relink) → 409, nothing moved. Test in Task 3.
- Admin double-clicks Approve → second call 409 "already approved", no second move. Test in Task 3.
- Requester's verified email already belongs to another profile at approval time → unique-email collision returns 409 instead of a 500. Test in Task 3.
- Player reloads after requesting → onboarding shows "waiting" instead of asking again. Test in Task 4.

---

### Task 1: Claim storage, claim service, retired profiles don't hold names

**Files:**
- Modify: `backend/app/models.py` (add `AccountClaim` after `PendingLegacyPlayer`, ~line 860)
- Create: `backend/migrations/add_account_claims_postgres.sql`
- Create: `backend/app/services/account_claim_service.py`
- Modify: `backend/app/services/legacy_player_service.py:124-140` (`is_canonical_name_claimed`)
- Test: `backend/tests/unit/services/test_account_claim_service.py`

**Interfaces:**
- Produces: model `AccountClaim` (columns per spec). Service functions:
  - `find_name_holder(db, canonical_name: str) -> PlayerProfile | None` (active only, `legacy_name` or `name`, case-insensitive, lowest id)
  - `has_login(profile: PlayerProfile) -> bool`
  - `pending_claim_for(db, requester_profile_id: int) -> AccountClaim | None`
  - `request_claim_for_name(db, requester: PlayerProfile, canonical_name: str, *, email: str | None, email_verified: bool | None) -> dict` → `{"status": "taken"}` | `{"status": "unverified"}` | `{"status": "pending", "claim": AccountClaim, "created": bool}` (caller commits)
  - `notify_admins_of_claim(canonical_name: str, requester_email: str | None) -> None` (non-blocking thread; calls `get_email_service().send_account_claim_notification(admin_email, canonical_name, requester_email)` for each `get_admin_emails()` — the email method is added in Task 2; guard with `getattr` is NOT allowed, Task 2 adds it before anything calls this in production)

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/unit/services/test_account_claim_service.py`:

```python
"""Claim storage and the rules for when picking a taken name becomes a claim."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import AccountClaim, LegacyRosterPlayer, PlayerProfile
from app.services import account_claim_service as svc
from app.services.legacy_player_service import link_profile_to_canonical_name


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    for name in ["Gregg Colburn", "Kevin Gent", "Dom Damico", "Chip Halbert"]:
        session.add(LegacyRosterPlayer(name=name, source="seed", added_at="2026-01-01"))
    session.add_all(
        [
            PlayerProfile(id=1, name="Gregg Colburn", legacy_name="Gregg Colburn", created_at="2025-01-01"),
            PlayerProfile(id=2, name="gregg@example.com", email="gregg@example.com",
                          preferences={"auth0_id": "auth0|gregg"}, created_at="2026-10-09"),
            PlayerProfile(id=3, name="Kevin Gent", legacy_name="Kevin Gent",
                          preferences={"auth0_id": "google-oauth2|kevin"}, created_at="2025-01-01"),
            PlayerProfile(id=4, name="old stray", legacy_name="Dom Damico", is_active=0, created_at="2026-01-01"),
            PlayerProfile(id=5, name="Chip Halbert", legacy_name="Chip Halbert", created_at="2025-01-01"),
        ]
    )
    session.commit()
    yield session
    session.close()
    engine.dispose()


def test_holder_lookup_ignores_retired_profiles(db):
    assert svc.find_name_holder(db, "gregg colburn").id == 1
    assert svc.find_name_holder(db, "Dom Damico") is None


def test_retired_profile_no_longer_blocks_linking_its_name(db):
    result = link_profile_to_canonical_name(db, 2, "Dom Damico")
    assert result["linked"] is True


def test_name_held_by_login_less_original_becomes_a_pending_claim(db):
    out = svc.request_claim_for_name(db, db.get(PlayerProfile, 2), "Gregg Colburn",
                                     email="gregg@example.com", email_verified=True)
    db.commit()
    assert out["status"] == "pending" and out["created"] is True
    claim = out["claim"]
    assert (claim.requester_profile_id, claim.target_profile_id, claim.canonical_name, claim.status) == (2, 1, "Gregg Colburn", "pending")
    assert claim.requester_email == "gregg@example.com"
    assert svc.pending_claim_for(db, 2).id == claim.id


def test_repeat_request_reuses_the_pending_claim(db):
    first = svc.request_claim_for_name(db, db.get(PlayerProfile, 2), "Gregg Colburn", email="g@x.com", email_verified=True)
    again = svc.request_claim_for_name(db, db.get(PlayerProfile, 2), "Gregg Colburn", email="g@x.com", email_verified=True)
    db.commit()
    assert again["created"] is False and again["claim"].id == first["claim"].id
    assert db.query(AccountClaim).count() == 1


def test_picking_a_different_name_supersedes_the_old_claim(db):
    first = svc.request_claim_for_name(db, db.get(PlayerProfile, 2), "Gregg Colburn", email="g@x.com", email_verified=True)
    second = svc.request_claim_for_name(db, db.get(PlayerProfile, 2), "Chip Halbert", email="g@x.com", email_verified=True)
    db.commit()
    assert second["created"] is True and second["claim"].target_profile_id == 5
    old = db.get(AccountClaim, first["claim"].id)
    assert (old.status, old.resolved_by) == ("dismissed", "superseded")
    assert svc.pending_claim_for(db, 2).id == second["claim"].id


def test_name_held_by_a_profile_with_a_login_is_taken(db):
    out = svc.request_claim_for_name(db, db.get(PlayerProfile, 2), "Kevin Gent", email="g@x.com", email_verified=True)
    assert out == {"status": "taken"}
    assert db.query(AccountClaim).count() == 0


def test_unverified_requester_cannot_claim(db):
    out = svc.request_claim_for_name(db, db.get(PlayerProfile, 2), "Gregg Colburn", email="g@x.com", email_verified=False)
    assert out == {"status": "unverified"}
    assert db.query(AccountClaim).count() == 0
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && venv/bin/python -m pytest tests/unit/services/test_account_claim_service.py -q -p no:warnings`
Expected: FAIL — `ImportError: cannot import name 'AccountClaim'`.

- [ ] **Step 3: Model + migration**

In `backend/app/models.py`, after the `PendingLegacyPlayer` class:

```python
class AccountClaim(Base):
    """A returning player's request to be connected to their original profile.

    Created when someone picks a roster name held by an active profile with no
    login. An admin approves (moves the login onto the original, retires the
    requester's stray profile) or dismisses it.
    """

    __tablename__ = "account_claims"
    id = Column(Integer, primary_key=True, index=True)
    requester_profile_id = Column(Integer, nullable=False, index=True)
    target_profile_id = Column(Integer, nullable=False, index=True)
    canonical_name = Column(String, nullable=False)
    requester_email = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending", server_default="pending", index=True)
    created_at = Column(String)
    resolved_at = Column(String, nullable=True)
    resolved_by = Column(String, nullable=True)
```

Create `backend/migrations/add_account_claims_postgres.sql`:

```sql
CREATE TABLE IF NOT EXISTS account_claims (
    id SERIAL PRIMARY KEY,
    requester_profile_id INTEGER NOT NULL,
    target_profile_id INTEGER NOT NULL,
    canonical_name VARCHAR NOT NULL,
    requester_email VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'pending',
    created_at VARCHAR,
    resolved_at VARCHAR,
    resolved_by VARCHAR
);
CREATE INDEX IF NOT EXISTS ix_account_claims_requester_profile_id ON account_claims (requester_profile_id);
CREATE INDEX IF NOT EXISTS ix_account_claims_target_profile_id ON account_claims (target_profile_id);
CREATE INDEX IF NOT EXISTS ix_account_claims_status ON account_claims (status);
```

- [ ] **Step 4: Retired profiles don't hold names**

In `backend/app/services/legacy_player_service.py` `is_canonical_name_claimed`, change the query to:

```python
    query = db.query(PlayerProfile).filter(
        PlayerProfile.is_active == 1,
        or_(
            func.lower(PlayerProfile.legacy_name) == canonical_name.lower(),
            func.lower(PlayerProfile.name) == canonical_name.lower(),
        ),
    )
```

and append to its docstring: `Retired (inactive) profiles never hold a name.`

- [ ] **Step 5: Service**

Create `backend/app/services/account_claim_service.py`:

```python
"""Claims: a returning player asks to be connected to their original profile.

Many players have an original profile (their history, no email, no login) from
before logins existed. On first sign-in they land on a new stray profile; when
they pick their roster name it's already held by the original. Instead of a
dead end, that becomes a claim an admin approves (see routers/account_claims.py).
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from sqlalchemy import func, or_

from ..models import AccountClaim, PlayerProfile
from ..utils.time import utc_now

logger = logging.getLogger(__name__)


def has_login(profile: PlayerProfile) -> bool:
    return bool((profile.preferences or {}).get("auth0_id"))


def find_name_holder(db: Any, canonical_name: str) -> PlayerProfile | None:
    """The active profile holding this roster name (lowest id wins)."""
    low = canonical_name.lower()
    return (
        db.query(PlayerProfile)
        .filter(
            PlayerProfile.is_active == 1,
            or_(func.lower(PlayerProfile.legacy_name) == low, func.lower(PlayerProfile.name) == low),
        )
        .order_by(PlayerProfile.id)
        .first()
    )


def pending_claim_for(db: Any, requester_profile_id: int) -> AccountClaim | None:
    return (
        db.query(AccountClaim)
        .filter(AccountClaim.requester_profile_id == requester_profile_id, AccountClaim.status == "pending")
        .order_by(AccountClaim.id.desc())
        .first()
    )


def request_claim_for_name(
    db: Any,
    requester: PlayerProfile,
    canonical_name: str,
    *,
    email: str | None,
    email_verified: bool | None,
) -> dict[str, Any]:
    """Turn "that name is taken" into a pending claim when the holder has no login. Caller commits."""
    holder = find_name_holder(db, canonical_name)
    if holder is None or holder.id == requester.id or has_login(holder):
        return {"status": "taken"}
    if email_verified is not True:
        return {"status": "unverified"}

    now = utc_now().isoformat()
    existing = pending_claim_for(db, requester.id)
    if existing and existing.target_profile_id == holder.id:
        return {"status": "pending", "claim": existing, "created": False}
    if existing:
        existing.status = "dismissed"
        existing.resolved_at = now
        existing.resolved_by = "superseded"
    claim = AccountClaim(
        requester_profile_id=requester.id,
        target_profile_id=holder.id,
        canonical_name=canonical_name,
        requester_email=email,
        status="pending",
        created_at=now,
    )
    db.add(claim)
    db.flush()
    logger.info("Claim %s: profile %s asks to be %r (profile %s)", claim.id, requester.id, canonical_name, holder.id)
    return {"status": "pending", "claim": claim, "created": True}


def notify_admins_of_claim(canonical_name: str, requester_email: str | None) -> None:
    """Best-effort, non-blocking admin email; never affects the player's request."""

    def _send() -> None:
        try:
            from ..utils.admin_auth import get_admin_emails
            from .email_service import get_email_service

            service = get_email_service()
            if not service.is_configured():
                return
            for admin_email in get_admin_emails():
                service.send_account_claim_notification(admin_email, canonical_name, requester_email)
        except Exception as exc:  # never surface to the player
            logger.warning("Failed to notify admins of claim for %r: %s", canonical_name, exc)

    threading.Thread(target=_send, daemon=True, name="account-claim-notify").start()
```

- [ ] **Step 6: Run tests**

Run: `cd backend && venv/bin/python -m pytest tests/unit/services/test_account_claim_service.py tests/unit/services/test_legacy_player_service.py tests/unit/routers/test_account_links.py -q -p no:warnings`
Expected: PASS. If an existing test relied on an inactive profile blocking a name, read it: if it asserts the old behaviour on purpose, update it to the new rule and say so in your report.

- [ ] **Step 7: Commit**

```bash
git add backend/app/models.py backend/migrations/add_account_claims_postgres.sql backend/app/services/account_claim_service.py backend/app/services/legacy_player_service.py backend/tests/unit/services/test_account_claim_service.py
git commit -m "feat: store account claims; retired profiles no longer hold roster names"
```

---

### Task 2: Player flow — 202 claim on a taken name, `pending_claim` on `/me`, admin email

**Files:**
- Modify: `backend/app/routers/players.py` (`update_my_legacy_name`, `get_my_profile`)
- Modify: `backend/app/schemas/players.py` (add `PendingClaimInfo`; `PlayerProfileResponse.pending_claim`), `backend/app/schemas/__init__.py` (export `PendingClaimInfo`)
- Modify: `backend/app/services/email_service.py` (add `send_account_claim_notification` after `send_new_player_notification`)
- Modify: `backend/openapi.json`, `frontend/src/api/schema.d.ts` (regenerated)
- Test: `backend/tests/unit/routers/test_account_claims_player.py`

**Interfaces:**
- Consumes (Task 1): `account_claim_service.request_claim_for_name`, `.pending_claim_for`, `.notify_admins_of_claim`.
- Produces: `PUT /players/me/legacy-name` → 202 `{"status": "claim_pending", "canonical_name": str, "message": str}`; 403 for unverified; unchanged 409 when the holder has a login. `GET /players/me` → `pending_claim: {"canonical_name": str, "created_at": str | null} | null`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/unit/routers/test_account_claims_player.py`:

```python
"""Player side of claims: picking a taken name, and /players/me reporting it."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import AccountClaim, LegacyRosterPlayer, PlayerProfile
from app.services import account_claim_service
from app.services.auth_service import get_current_auth0_user


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setattr("app.services.auth_service._send_welcome_email", lambda *args: None)
    notified = []
    monkeypatch.setattr(account_claim_service, "notify_admins_of_claim", lambda *args: notified.append(args))
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    with sessions() as db:
        for name in ["Gregg Colburn", "Kevin Gent"]:
            db.add(LegacyRosterPlayer(name=name, source="seed", added_at="2026-01-01"))
        db.add_all(
            [
                PlayerProfile(id=1, name="Gregg Colburn", legacy_name="Gregg Colburn", created_at="2025-01-01"),
                PlayerProfile(id=2, name="gregg@example.com", email="gregg@example.com",
                              preferences={"auth0_id": "auth0|gregg"}, created_at="2026-10-09"),
                PlayerProfile(id=3, name="Kevin Gent", legacy_name="Kevin Gent",
                              preferences={"auth0_id": "google-oauth2|kevin"}, created_at="2025-01-01"),
            ]
        )
        db.commit()

    def database():
        with sessions() as db:
            yield db

    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_current_auth0_user] = lambda: {
        "sub": "auth0|gregg", "email": "gregg@example.com", "email_verified": True, "name": "gregg@example.com",
    }
    yield TestClient(app), sessions, notified
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_auth0_user, None)
    engine.dispose()


def pick(client, name):
    return client.put("/players/me/legacy-name", json={"legacy_name": name})


def test_picking_a_name_held_by_a_login_less_original_returns_202_and_notifies(env):
    client, sessions, notified = env
    resp = pick(client, "Gregg Colburn")
    assert resp.status_code == 202, resp.text
    assert resp.json() == {
        "status": "claim_pending",
        "canonical_name": "Gregg Colburn",
        "message": "Request sent — a club admin will connect you to your history.",
    }
    assert notified == [("Gregg Colburn", "gregg@example.com")]
    with sessions() as db:
        assert db.query(AccountClaim).filter_by(status="pending").count() == 1


def test_repeat_pick_does_not_notify_twice(env):
    client, _, notified = env
    pick(client, "Gregg Colburn")
    assert pick(client, "Gregg Colburn").status_code == 202
    assert len(notified) == 1


def test_name_held_by_a_profile_with_a_login_is_still_409(env):
    client, sessions, notified = env
    resp = pick(client, "Kevin Gent")
    assert resp.status_code == 409
    assert notified == []
    with sessions() as db:
        assert db.query(AccountClaim).count() == 0


def test_unverified_email_gets_403(env):
    client, _, _ = env
    app.dependency_overrides[get_current_auth0_user] = lambda: {
        "sub": "auth0|gregg", "email": "gregg@example.com", "email_verified": False,
    }
    resp = pick(client, "Gregg Colburn")
    assert resp.status_code == 403
    assert "Verify your email" in resp.json()["detail"]


def test_me_reports_the_pending_claim(env):
    client, _, _ = env
    assert client.get("/players/me").json()["pending_claim"] is None
    pick(client, "Gregg Colburn")
    claim = client.get("/players/me").json()["pending_claim"]
    assert claim["canonical_name"] == "Gregg Colburn" and claim["created_at"]


def test_other_profile_responses_never_carry_pending_claim(env):
    client, _, _ = env
    pick(client, "Gregg Colburn")
    assert client.get("/players/name/gregg@example.com").json().get("pending_claim") is None
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && venv/bin/python -m pytest tests/unit/routers/test_account_claims_player.py -q -p no:warnings`
Expected: FAIL — the first test gets 409, `/me` has no `pending_claim`.

- [ ] **Step 3: Schema**

In `backend/app/schemas/players.py`, before `PlayerProfileResponse`:

```python
class PendingClaimInfo(BaseModel):
    """A claim this player made on an original profile, waiting for an admin."""

    canonical_name: str
    created_at: str | None = None
```

In `PlayerProfileResponse`, after `legacy_name_suggestion: str | None = None`:

```python
    # Computed in GET /players/me only; never an ORM attribute (see PR #373).
    pending_claim: PendingClaimInfo | None = None
```

Add `PendingClaimInfo` to the `from .players import (...)` block and `__all__` in `backend/app/schemas/__init__.py`.

- [ ] **Step 4: Email**

In `backend/app/services/email_service.py`, after `send_new_player_notification`:

```python
    def send_account_claim_notification(
        self,
        to_email: str,
        canonical_name: str,
        requester_email: str | None = None,
    ) -> bool:
        """Alert an admin that a returning player asked to be connected to their original profile."""
        who = f"<strong>{requester_email}</strong>" if requester_email else "A player"
        content = f"""
        <h2>Player wants their history connected</h2>
        <p>{who} signed in and says they are <strong>{canonical_name}</strong>.
        That player's original profile has no login yet.</p>
        <p>Open the admin page → <strong>Account links</strong> → <strong>Claim requests</strong>
        to approve or dismiss it.</p>
        """
        template = Template(self._get_base_template())
        html_body = template.render(subject="WGP claim request", content=content)
        return self._send_email(
            to_email=to_email,
            subject=f"WGP claim request: {canonical_name}",
            html_body=html_body,
        )
```

- [ ] **Step 5: Router**

In `backend/app/routers/players.py`:

Imports: add `from fastapi.responses import JSONResponse` if not present (the file already imports `Response` from `fastapi.responses` — extend that line), and `from ..services import account_claim_service`.

`update_my_legacy_name`: add the parameter `auth0_user: dict[str, Any] = Depends(get_current_auth0_user),` after `current_user`, add `responses={202: {"description": "Name belongs to an original profile with no login; a claim was sent to admins"}}` to its `@router.put(...)` decorator, and replace the `if link_result["status"] == "claimed":` block with:

```python
            if link_result["status"] == "claimed":
                outcome = account_claim_service.request_claim_for_name(
                    db,
                    current_user,
                    canonical,
                    email=(auth0_user.get("email") or current_user.email),
                    email_verified=auth0_user.get("email_verified"),
                )
                if outcome["status"] == "unverified":
                    raise HTTPException(
                        status_code=403,
                        detail="Verify your email address, then pick your name again so a club admin can connect you.",
                    )
                if outcome["status"] == "pending":
                    claim = outcome["claim"]
                    db.commit()
                    if outcome["created"]:
                        account_claim_service.notify_admins_of_claim(canonical, claim.requester_email)
                    return JSONResponse(
                        status_code=202,
                        content={
                            "status": "claim_pending",
                            "canonical_name": canonical,
                            "message": "Request sent — a club admin will connect you to your history.",
                        },
                    )
                raise HTTPException(
                    status_code=409,
                    detail=f"'{canonical}' already has a player profile. Ask a club admin to connect your sign-in to that player in Account links.",
                )
```

(Keep the existing 409 text exactly as it is in the file today.)

`get_my_profile`: before `return profile`, add:

```python
    claim = account_claim_service.pending_claim_for(db, cast("int", current_user.id))
    profile.pending_claim = (
        schemas.PendingClaimInfo(canonical_name=claim.canonical_name, created_at=claim.created_at) if claim else None
    )
```

- [ ] **Step 6: Run tests + contract**

Run: `cd backend && venv/bin/python -m pytest tests/unit/routers/test_account_claims_player.py tests/unit/routers/test_players_router.py -q -p no:warnings` → PASS.
Run from worktree root: `PATH=$PWD/backend/venv/bin:$PATH ./scripts/sync_openapi.sh` → "in sync".

- [ ] **Step 7: Commit**

```bash
git add backend/app/routers/players.py backend/app/schemas/players.py backend/app/schemas/__init__.py backend/app/services/email_service.py backend/tests/unit/routers/test_account_claims_player.py backend/openapi.json frontend/src/api/schema.d.ts
git commit -m "feat: picking a name held by a login-less original sends a claim to admins"
```

---

### Task 3: Admin API — list, approve, dismiss

**Files:**
- Create: `backend/app/routers/account_claims.py`
- Modify: `backend/app/routers/players.py:39,84` (import + `router.include_router(account_claims_router)` after `admin_grants_router`)
- Modify: `backend/app/services/player_service.py` (extract `release_identity_and_retire`)
- Modify: `backend/openapi.json`, `frontend/src/api/schema.d.ts` (regenerated)
- Test: `backend/tests/unit/routers/test_account_claims_admin.py`

**Interfaces:**
- Consumes (Task 1): `AccountClaim`, `account_claim_service.has_login`.
- Produces: `GET /players/admin/claims?status=pending` → `{"claims": [ClaimRow]}`; `POST /players/admin/claims/{id}/approve` → `ClaimRow`; `POST /players/admin/claims/{id}/dismiss` → `ClaimRow`. `ClaimRow = {id, canonical_name, requester_email, status, created_at, resolved_at, resolved_by, requester: ProfileSummary|null, target: ProfileSummary|null}`; `ProfileSummary = {id, name, legacy_name, email, login (provider prefix or null), is_active, updated_at}`. Module function `player_service.release_identity_and_retire(player: PlayerProfile) -> None` (caller commits).

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/unit/routers/test_account_claims_admin.py`:

```python
"""Admin side of claims: approve moves the login onto the original and retires the stray."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import AccountClaim, LegacyRosterPlayer, PlayerProfile
from app.services.auth_service import AuthService, get_current_auth0_user

ADMIN = {"sub": "auth0|admin", "email": "admin@example.com"}


@pytest.fixture
def env(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    with sessions() as db:
        db.add(LegacyRosterPlayer(name="Gregg Colburn", source="seed", added_at="2026-01-01"))
        db.add_all(
            [
                PlayerProfile(id=1, name="Gregg Colburn", legacy_name="Gregg Colburn", created_at="2025-01-01"),
                PlayerProfile(id=2, name="gregg@example.com", email="gregg@example.com",
                              preferences={"auth0_id": "auth0|gregg", "display_hints": True}, created_at="2026-10-09"),
                AccountClaim(id=10, requester_profile_id=2, target_profile_id=1, canonical_name="Gregg Colburn",
                             requester_email="gregg@example.com", status="pending", created_at="2026-10-09T10:00:00"),
            ]
        )
        db.commit()

    def database():
        with sessions() as db:
            yield db

    monkeypatch.setenv("SUPER_ADMIN_EMAILS", "admin@example.com")
    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_current_auth0_user] = lambda: ADMIN
    yield TestClient(app), sessions
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_auth0_user, None)
    engine.dispose()


def test_list_shows_pending_claims_with_both_profiles(env):
    client, _ = env
    claims = client.get("/players/admin/claims").json()["claims"]
    assert [c["id"] for c in claims] == [10]
    assert claims[0]["requester"]["id"] == 2 and claims[0]["requester"]["login"] == "auth0"
    assert claims[0]["target"]["id"] == 1 and claims[0]["target"]["login"] is None


def test_approve_moves_login_onto_original_and_retires_the_stray(env):
    client, sessions = env
    resp = client.post("/players/admin/claims/10/approve")
    assert resp.status_code == 200, resp.text
    assert (resp.json()["status"], resp.json()["resolved_by"]) == ("approved", "admin@example.com")
    with sessions() as db:
        original, stray = db.get(PlayerProfile, 1), db.get(PlayerProfile, 2)
        assert (original.email, original.preferences["auth0_id"], original.legacy_name, original.name) == (
            "gregg@example.com", "auth0|gregg", "Gregg Colburn", "Gregg Colburn")
        assert not stray.is_active and stray.email is None and "auth0_id" not in (stray.preferences or {})
        resolved = AuthService.get_or_create_player_profile(
            db, {"sub": "auth0|gregg", "email": "gregg@example.com", "email_verified": True, "name": "Gregg"})
        assert resolved.id == 1


def test_second_approve_is_409(env):
    client, _ = env
    client.post("/players/admin/claims/10/approve")
    resp = client.post("/players/admin/claims/10/approve")
    assert resp.status_code == 409
    assert "already approved" in resp.json()["detail"]


def test_approve_refused_when_original_already_has_a_login(env):
    client, sessions = env
    with sessions() as db:
        db.get(PlayerProfile, 1).preferences = {"auth0_id": "google-oauth2|someone"}
        db.commit()
    resp = client.post("/players/admin/claims/10/approve")
    assert resp.status_code == 409
    with sessions() as db:
        assert db.get(PlayerProfile, 2).is_active and db.get(AccountClaim, 10).status == "pending"


def test_approve_refused_when_requester_was_retired(env):
    client, sessions = env
    with sessions() as db:
        db.get(PlayerProfile, 2).is_active = 0
        db.commit()
    assert client.post("/players/admin/claims/10/approve").status_code == 409


def test_approve_email_collision_is_409_not_500(env):
    client, sessions = env
    with sessions() as db:
        db.get(AccountClaim, 10).requester_email = "taken@example.com"
        db.get(PlayerProfile, 2).email = None
        db.add(PlayerProfile(id=3, name="Someone Else", email="taken@example.com", created_at="2025-01-01"))
        db.commit()
    resp = client.post("/players/admin/claims/10/approve")
    assert resp.status_code == 409
    with sessions() as db:
        assert db.get(PlayerProfile, 2).is_active and db.get(AccountClaim, 10).status == "pending"


def test_dismiss_once(env):
    client, _ = env
    resp = client.post("/players/admin/claims/10/dismiss")
    assert resp.status_code == 200 and resp.json()["status"] == "dismissed"
    assert client.post("/players/admin/claims/10/dismiss").status_code == 409
    assert client.get("/players/admin/claims").json()["claims"] == []


def test_unknown_claim_404_and_non_admin_403(env):
    client, _ = env
    assert client.post("/players/admin/claims/999/approve").status_code == 404
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": "auth0|x", "email": "player@example.com"}
    assert client.get("/players/admin/claims").status_code == 403
    assert client.post("/players/admin/claims/10/approve").status_code == 403
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && venv/bin/python -m pytest tests/unit/routers/test_account_claims_admin.py -q -p no:warnings`
Expected: FAIL — 404s on `/players/admin/claims`.

- [ ] **Step 3: Extract the retire helper**

In `backend/app/services/player_service.py`, add a module-level function (above `class PlayerService`):

```python
def release_identity_and_retire(player: PlayerProfile) -> None:
    """Deactivate a profile and free its identity (email, login, GHIN, admin). Caller commits.

    An inactive profile that still holds an email/Auth0 ID blocks that person's
    sign-in and any relink to their real profile.
    """
    player.is_active = 0
    player.ghin_id = None
    player.email = None
    player.preferences = {k: v for k, v in (player.preferences or {}).items() if k != "auth0_id"}
    player.admin_granted = 0
    player.admin_granted_by = None
    player.admin_granted_at = None
```

and replace the body lines in `delete_player_profile` from `player.is_active = 0` through `player.admin_granted_at = None` with `release_identity_and_retire(player)`.

- [ ] **Step 4: Router**

Create `backend/app/routers/account_claims.py`:

```python
"""Admin: approve or dismiss returning players' claims on their original profile."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AccountClaim, PlayerProfile
from ..services.account_claim_service import has_login
from ..services.player_service import release_identity_and_retire
from ..utils.admin_auth import require_admin
from ..utils.time import utc_now

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/claims", tags=["players"])


def _summary(player: PlayerProfile | None) -> dict[str, Any] | None:
    if player is None:
        return None
    login = (player.preferences or {}).get("auth0_id") or ""
    return {
        "id": player.id,
        "name": player.name,
        "legacy_name": player.legacy_name,
        "email": player.email,
        "login": login.split("|")[0] or None,
        "is_active": bool(player.is_active),
        "updated_at": player.updated_at,
    }


def _row(db: Session, claim: AccountClaim) -> dict[str, Any]:
    return {
        "id": claim.id,
        "canonical_name": claim.canonical_name,
        "requester_email": claim.requester_email,
        "status": claim.status,
        "created_at": claim.created_at,
        "resolved_at": claim.resolved_at,
        "resolved_by": claim.resolved_by,
        "requester": _summary(db.get(PlayerProfile, claim.requester_profile_id)),
        "target": _summary(db.get(PlayerProfile, claim.target_profile_id)),
    }


def _pending(db: Session, claim_id: int) -> AccountClaim:
    claim = db.query(AccountClaim).filter(AccountClaim.id == claim_id).with_for_update().first()
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.status != "pending":
        raise HTTPException(status_code=409, detail=f"This claim is already {claim.status}.")
    return claim


@router.get("", dependencies=[Depends(require_admin)])
def list_claims(
    status: str = Query("pending", pattern="^(pending|approved|dismissed)$"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    claims = db.query(AccountClaim).filter(AccountClaim.status == status).order_by(AccountClaim.id.desc()).limit(100).all()
    return {"claims": [_row(db, claim) for claim in claims]}


@router.post("/{claim_id}/approve")
def approve_claim(
    claim_id: int, admin: dict[str, Any] = Depends(require_admin), db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Move the requester's login onto the original profile and retire the stray, atomically."""
    claim = _pending(db, claim_id)
    requester = db.query(PlayerProfile).filter(PlayerProfile.id == claim.requester_profile_id).with_for_update().first()
    target = db.query(PlayerProfile).filter(PlayerProfile.id == claim.target_profile_id).with_for_update().first()
    subject = (requester.preferences or {}).get("auth0_id") if requester else None
    email = (requester.email if requester else None) or claim.requester_email

    # Same identity locks as relink-auth0, so a concurrent relink can't interleave.
    if db.get_bind().dialect.name == "postgresql":
        identities = [f"roster:{claim.canonical_name.lower()}"] + [
            value for value in (f"auth0:{subject}" if subject else None, f"email:{email}" if email else None) if value
        ]
        for identity in sorted(identities):
            db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:identity))"), {"identity": f"account-link:{identity}"})

    if target is None or not target.is_active:
        raise HTTPException(status_code=409, detail=f"The original profile #{claim.target_profile_id} is no longer active. Dismiss this claim.")
    if has_login(target):
        raise HTTPException(status_code=409, detail=f"Profile #{target.id} already has a login. Dismiss this claim.")
    if requester is None or not requester.is_active or not subject:
        raise HTTPException(status_code=409, detail="The requesting sign-in no longer has an active profile. Dismiss this claim.")

    release_identity_and_retire(requester)  # frees the email + login before the original takes them
    db.flush()
    now = utc_now().isoformat()
    target.email = email
    target.preferences = {**(target.preferences or {}), "auth0_id": subject}
    target.legacy_name = claim.canonical_name
    target.name = claim.canonical_name
    target.updated_at = now
    claim.status = "approved"
    claim.resolved_at = now
    claim.resolved_by = admin.get("email")
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="That email or name already belongs to another profile. Resolve it in Account links, then try again.",
        ) from exc
    logger.info("Claim %s approved by %s: profile %s -> %s", claim.id, admin.get("email"), claim.requester_profile_id, target.id)
    return _row(db, claim)


@router.post("/{claim_id}/dismiss")
def dismiss_claim(
    claim_id: int, admin: dict[str, Any] = Depends(require_admin), db: Session = Depends(get_db)
) -> dict[str, Any]:
    claim = _pending(db, claim_id)
    claim.status = "dismissed"
    claim.resolved_at = utc_now().isoformat()
    claim.resolved_by = admin.get("email")
    db.commit()
    logger.info("Claim %s dismissed by %s", claim.id, admin.get("email"))
    return _row(db, claim)
```

Mount in `backend/app/routers/players.py`: next to `from .admin_grants import router as admin_grants_router` add `from .account_claims import router as account_claims_router`, and after `router.include_router(admin_grants_router)` add `router.include_router(account_claims_router)`.

- [ ] **Step 5: Run tests + contract**

Run: `cd backend && venv/bin/python -m pytest tests/unit/routers/test_account_claims_admin.py tests/unit/routers/test_players_router.py tests/unit/routers/test_admin_grants.py -q -p no:warnings` → PASS.
Run from worktree root: `PATH=$PWD/backend/venv/bin:$PATH ./scripts/sync_openapi.sh` → "in sync".

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/account_claims.py backend/app/routers/players.py backend/app/services/player_service.py backend/tests/unit/routers/test_account_claims_admin.py backend/openapi.json frontend/src/api/schema.d.ts
git commit -m "feat: admins approve or dismiss account claims"
```

---

### Task 4: Onboarding — handle 202 and show the waiting note

**Files:**
- Modify: `frontend/src/hooks/usePlayerProfile.js` (`updateLegacyName`, `needsLegacyName`, returned `pendingClaim`)
- Modify: `frontend/src/components/auth/OnboardingWrapper.jsx`
- Test: `frontend/src/hooks/__tests__/usePlayerProfile.test.js`, `frontend/src/components/auth/__tests__/OnboardingWrapper.test.jsx`

**Interfaces:**
- Consumes (Task 2): 202 body `{status: "claim_pending", canonical_name, message}`; `/players/me` `pending_claim`.
- Produces: `usePlayerProfile()` adds `pendingClaim` (`{canonical_name, created_at} | null`); `needsLegacyName` is false while a claim is pending; `updateLegacyName` resolves to the 202 body on a claim.

- [ ] **Step 1: Write the failing tests**

Append to `frontend/src/hooks/__tests__/usePlayerProfile.test.js` inside the existing `describe("usePlayerProfile synchronization", ...)` block (it already mocks Auth0 and fetch in `beforeEach`):

```js
  test("a 202 claim_pending response records the claim and stops asking for a name", async () => {
    const { result } = renderHook(() => usePlayerProfile());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.needsLegacyName).toBe(true);

    global.fetch.mockImplementationOnce(() => Promise.resolve({
      ok: true,
      status: 202,
      json: () => Promise.resolve({
        status: "claim_pending",
        canonical_name: "Player One",
        message: "Request sent — a club admin will connect you to your history.",
      }),
    }));
    let returned;
    await act(async () => { returned = await result.current.updateLegacyName("Player One"); });

    expect(returned.status).toBe("claim_pending");
    expect(result.current.pendingClaim.canonical_name).toBe("Player One");
    expect(result.current.needsLegacyName).toBe(false);
  });
```

Append to `frontend/src/components/auth/__tests__/OnboardingWrapper.test.jsx` (use the file's existing `mockUseAuth0` setup from its `beforeEach`; if it sets the Auth0 mock per-test, copy that call into this test):

```jsx
test("shows a waiting note instead of the history prompt while a claim is pending", async () => {
  global.fetch.mockImplementation(() => okJson({
    id: 5,
    legacy_name: null,
    pending_claim: { canonical_name: "Gregg Colburn", created_at: "2026-10-09T10:00:00" },
  }));
  render(<OnboardingWrapper><div>app</div></OnboardingWrapper>);
  expect(await screen.findByText(/Waiting for a club admin to connect you to Gregg Colburn/)).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Find my player history" })).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run to verify failure**

Run: `cd frontend && npx vitest run src/hooks/__tests__/usePlayerProfile.test.js src/components/auth/__tests__/OnboardingWrapper.test.jsx`
Expected: FAIL (`pendingClaim` undefined; no waiting note).

- [ ] **Step 3: Hook**

In `frontend/src/hooks/usePlayerProfile.js`:

Change `const needsLegacyName = isUnlinked && !legacyNameSkipped;` to:

```js
  const pendingClaim = profile?.pending_claim || null;
  const needsLegacyName = isUnlinked && !legacyNameSkipped && !pendingClaim;
```

In `updateLegacyName`, immediately after the `fetch(...)` call returns `response` and before `if (!response.ok) {`, add:

```js
        if (response.status === 202) {
          const claim = await response.json();
          setProfile((current) => (current
            ? { ...current, pending_claim: { canonical_name: claim.canonical_name, created_at: new Date().toISOString() } }
            : current));
          return claim;
        }
```

Add `pendingClaim,` to the hook's returned object (next to `needsLegacyName`).

- [ ] **Step 4: Wrapper**

In `frontend/src/components/auth/OnboardingWrapper.jsx`, add `pendingClaim,` to the `usePlayerProfile()` destructure, and directly before `{canLink && !findingPlayer && <section aria-label="Player history"` add:

```jsx
      {ready && !error && pendingClaim && <section aria-label="Claim pending" style={{ padding: 16, background: '#eef5ed', color: '#234422' }}>
        <p style={{ margin: 0 }}>Waiting for a club admin to connect you to {pendingClaim.canonical_name}. You can keep using the app in the meantime.</p>
      </section>}
```

(`OnboardingModal` already calls `onComplete` after `updateLegacyName` resolves, so a 202 closes the modal and this note takes over — no modal change.)

- [ ] **Step 5: Run tests**

Run: `cd frontend && npx vitest run src/hooks src/components/auth` → PASS. Then `npm run typecheck` → clean.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/hooks/usePlayerProfile.js frontend/src/components/auth/OnboardingWrapper.jsx frontend/src/hooks/__tests__/usePlayerProfile.test.js frontend/src/components/auth/__tests__/OnboardingWrapper.test.jsx
git commit -m "feat: onboarding shows a waiting note while an account claim is pending"
```

---

### Task 5: Claim requests in the Account links tab

**Files:**
- Create: `frontend/src/pages/admin/ClaimRequests.jsx`
- Modify: `frontend/src/pages/admin/AccountLinkingManager.jsx` (import; render `<ClaimRequests />` after the intro `<div>`)
- Modify: `frontend/src/pages/__tests__/AccountLinkingManager.test.jsx` (mock `ClaimRequests` so its mount-time fetch doesn't consume the existing tests' mocked responses)
- Test: `frontend/src/pages/__tests__/ClaimRequests.test.jsx`

**Interfaces:**
- Consumes (Task 3): `GET /players/admin/claims?status=pending` → `{claims: ClaimRow[]}`; `POST /players/admin/claims/{id}/approve|dismiss`.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/pages/__tests__/ClaimRequests.test.jsx`:

```jsx
import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import ClaimRequests from '../admin/ClaimRequests';

const request = vi.fn();
vi.mock('../../hooks/useAuthenticatedFetch', () => ({ useAuthenticatedFetch: () => request }));

const ok = data => ({ ok: true, json: async () => data });
const claim = {
  id: 10, canonical_name: 'Gregg Colburn', requester_email: 'gregg@example.com', status: 'pending',
  created_at: '2026-10-09T10:00:00', requester: { id: 2 }, target: { id: 1 },
};

beforeEach(() => { request.mockReset(); vi.spyOn(window, 'confirm').mockReturnValue(true); });

test('lists pending claims', async () => {
  request.mockResolvedValueOnce(ok({ claims: [claim] }));
  render(<ClaimRequests />);
  expect(await screen.findByText('gregg@example.com')).toBeInTheDocument();
  expect(screen.getByText(/Original profile #1/)).toBeInTheDocument();
});

test('shows the empty state', async () => {
  request.mockResolvedValueOnce(ok({ claims: [] }));
  render(<ClaimRequests />);
  expect(await screen.findByText('No claim requests.')).toBeInTheDocument();
});

test('approve posts, confirms, and reloads', async () => {
  request.mockResolvedValueOnce(ok({ claims: [claim] }));
  render(<ClaimRequests />);
  request.mockResolvedValueOnce(ok({ ...claim, status: 'approved' })).mockResolvedValueOnce(ok({ claims: [] }));
  fireEvent.click(await screen.findByRole('button', { name: 'Approve claim for Gregg Colburn' }));
  expect(await screen.findByText(/Connected Gregg Colburn/)).toBeInTheDocument();
  expect(request.mock.calls[1][0]).toMatch(/\/players\/admin\/claims\/10\/approve$/);
  expect(request.mock.calls[1][1]).toEqual({ method: 'POST' });
  expect(window.confirm).toHaveBeenCalled();
});

test('dismiss posts without a confirm and shows server errors', async () => {
  request.mockResolvedValueOnce(ok({ claims: [claim] }));
  render(<ClaimRequests />);
  request.mockResolvedValueOnce({ ok: false, status: 409, json: async () => ({ detail: 'This claim is already dismissed.' }) });
  fireEvent.click(await screen.findByRole('button', { name: 'Dismiss claim for Gregg Colburn' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('already dismissed');
  expect(request.mock.calls[1][0]).toMatch(/\/claims\/10\/dismiss$/);
});
```

- [ ] **Step 2: Run to verify failure**

Run: `cd frontend && npx vitest run src/pages/__tests__/ClaimRequests.test.jsx`
Expected: FAIL — cannot resolve `../admin/ClaimRequests`.

- [ ] **Step 3: Component**

Create `frontend/src/pages/admin/ClaimRequests.jsx` (Write tool only — it contains `!`):

```jsx
import React, { useCallback, useEffect, useState } from 'react';
import { useAuthenticatedFetch } from '../../hooks/useAuthenticatedFetch';
import { apiConfig } from '../../config/api.config';

const buttonClass = 'px-3 py-1 bg-blue-600 text-white rounded-lg disabled:opacity-50';

/** Returning players asking to be connected to their original profile (admin approves). */
export default function ClaimRequests() {
  const request = useAuthenticatedFetch();
  const [claims, setClaims] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const call = useCallback(async (path, options) => {
    const response = await request(`${apiConfig.baseUrl}${path}`, options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `HTTP ${response.status}`);
    return data;
  }, [request]);

  const load = useCallback(async () => {
    try { setClaims((await call('/players/admin/claims?status=pending')).claims); }
    catch (err) { setError(err.message); }
  }, [call]);

  useEffect(() => { load(); }, [load]);

  const resolve = async (claim, action) => {
    if (action === 'approve' && !window.confirm(`Connect ${claim.requester_email || 'this sign-in'} to ${claim.canonical_name} (profile #${claim.target?.id})? Their new profile #${claim.requester?.id} will be retired.`)) return;
    setBusy(true); setError(''); setSuccess('');
    try {
      await call(`/players/admin/claims/${claim.id}/${action}`, { method: 'POST' });
      setSuccess(action === 'approve'
        ? `Connected ${claim.canonical_name}. They can refresh the app to see their history.`
        : `Dismissed the claim for ${claim.canonical_name}.`);
      await load();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  return (
    <section aria-label="Claim requests" className="space-y-3">
      <h3 className="font-semibold">Claim requests</h3>
      {error && <div role="alert" className="p-3 rounded-lg bg-red-50 text-red-800">{error}</div>}
      {success && <div role="status" className="p-3 rounded-lg bg-green-50 text-green-800">{success}</div>}
      {claims?.length === 0 && <p className="text-gray-500">No claim requests.</p>}
      {claims?.length > 0 && <ul className="divide-y">{claims.map(claim => (
        <li key={claim.id} className="py-2 flex flex-wrap items-center justify-between gap-3">
          <div>
            <strong>{claim.requester_email || `Profile #${claim.requester?.id}`}</strong> wants to be <strong>{claim.canonical_name}</strong>
            <div className="text-sm text-gray-500">Original profile #{claim.target?.id} · requested {claim.created_at?.slice(0, 10)}</div>
          </div>
          <div className="flex gap-3">
            <button type="button" className={buttonClass} disabled={busy} onClick={() => resolve(claim, 'approve')} aria-label={`Approve claim for ${claim.canonical_name}`}>Approve</button>
            <button type="button" className="underline disabled:opacity-50" disabled={busy} onClick={() => resolve(claim, 'dismiss')} aria-label={`Dismiss claim for ${claim.canonical_name}`}>Dismiss</button>
          </div>
        </li>
      ))}</ul>}
    </section>
  );
}
```

- [ ] **Step 4: Wire into Account links**

In `frontend/src/pages/admin/AccountLinkingManager.jsx`: add `import ClaimRequests from './ClaimRequests';` after the other imports, and directly after the intro `<div>` (the one containing `<h2 className="text-xl font-semibold">Account links</h2>` and its paragraph) add `<ClaimRequests />`.

In `frontend/src/pages/__tests__/AccountLinkingManager.test.jsx`, next to the other `vi.mock(...)` lines add:

```jsx
vi.mock('../admin/ClaimRequests', () => ({ default: () => null }));
```

- [ ] **Step 5: Run tests**

Run: `cd frontend && npx vitest run src/pages` → PASS. `npm run typecheck` → clean. `grep -c '\\!' src/pages/admin/ClaimRequests.jsx` → 0.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/admin/ClaimRequests.jsx frontend/src/pages/admin/AccountLinkingManager.jsx frontend/src/pages/__tests__/ClaimRequests.test.jsx frontend/src/pages/__tests__/AccountLinkingManager.test.jsx
git commit -m "feat: Claim requests list with approve and dismiss in Account links"
```

---

### Task 6: Full gate, capabilities, PR

- [ ] **Step 1: Backend gate** — `cd backend && venv/bin/ruff check app/ tests/ && venv/bin/ruff format --check app/ tests/ && venv/bin/python scripts/export_openapi.py --check && venv/bin/python -m pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic -q -p no:warnings`. Only acceptable failure: `tests/infra/startup_test.py` (local proxy).
- [ ] **Step 2: Frontend gate** — `cd frontend && npm run typecheck && npx vitest run && npm run build`, then `git checkout -- frontend/public/service-worker.js frontend/public/version.json`.
- [ ] **Step 3: Capabilities** — `PYTHONPATH=.ctk backend/venv/bin/python -m caps status`; re-verify each `[STALE]`; commit `.ctk/ledger.json`.
- [ ] **Step 4: Push + PR** — push `feat/account-claims`, open a PR (summary, test plan with post-deploy checks: a test sign-in picking a login-less name gets the waiting note; the claim appears under Account links → Claim requests; Approve lands the player on the original).
