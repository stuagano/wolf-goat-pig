"""Router tests for the admin canonical-roster + pending-capture endpoints."""

import uuid

from fastapi.testclient import TestClient

from app.database import engine
from app.main import app
from app.models import Base
from app.services import legacy_player_service as svc

# Ensure the new tables exist in the dev DB (lifespan isn't run by TestClient).
Base.metadata.create_all(bind=engine)

client = TestClient(app)

ADMIN = {"X-Admin-Email": "stuagano@gmail.com"}


def _novel_name(prefix: str) -> str:
    return f"{prefix} {uuid.uuid4().hex[:8]}"


# ── auth ─────────────────────────────────────────────────────────────────────


def test_add_legacy_player_requires_admin():
    resp = client.post("/legacy-players", json={"name": "No Auth"})
    assert resp.status_code == 403


def test_list_pending_requires_admin():
    resp = client.get("/legacy-players/pending")
    assert resp.status_code == 403


# ── add to canonical roster ──────────────────────────────────────────────────


def test_admin_add_legacy_player():
    name = _novel_name("Roster Add")
    resp = client.post("/legacy-players", json={"name": name}, headers=ADMIN)
    assert resp.status_code == 200
    assert resp.json()["added"] is True

    # Now appears in the canonical list.
    listing = client.get("/legacy-players").json()
    assert name in listing["players"]


# ── pending capture lifecycle ────────────────────────────────────────────────


def test_list_and_promote_pending_player():
    name = _novel_name("Pending Promote")
    captured = svc.capture_pending_player(name, email="p@example.com")
    assert captured["captured"] is True
    pending_id = captured["pending_id"]

    listing = client.get("/legacy-players/pending", headers=ADMIN).json()
    assert any(p["id"] == pending_id and p["name"] == name for p in listing["players"])

    resp = client.post(f"/legacy-players/pending/{pending_id}/promote", headers=ADMIN)
    assert resp.status_code == 200
    assert resp.json()["promoted"] is True

    # Promoted → now canonical, no longer pending.
    assert name in client.get("/legacy-players").json()["players"]
    still_pending = client.get("/legacy-players/pending", headers=ADMIN).json()
    assert not any(p["id"] == pending_id for p in still_pending["players"])


def test_dismiss_pending_player():
    name = _novel_name("Pending Dismiss")
    captured = svc.capture_pending_player(name)
    pending_id = captured["pending_id"]

    resp = client.post(f"/legacy-players/pending/{pending_id}/dismiss", headers=ADMIN)
    assert resp.status_code == 200
    assert resp.json()["dismissed"] is True

    # Not canonical, not pending.
    assert name not in client.get("/legacy-players").json()["players"]
    still_pending = client.get("/legacy-players/pending", headers=ADMIN).json()
    assert not any(p["id"] == pending_id for p in still_pending["players"])


def test_promote_missing_pending_returns_404():
    resp = client.post("/legacy-players/pending/99999999/promote", headers=ADMIN)
    assert resp.status_code == 404
