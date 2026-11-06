"""Unit tests for team_formation router — random teams, balanced teams, rotations, Sunday pairings, players list."""

import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import get_current_user
from app.utils.admin_auth import require_admin

# Behavior tests for guarded routes; auth is tested in test_write_endpoints_require_auth.py.
pytestmark = pytest.mark.usefixtures("signed_in_admin")

client = TestClient(app)


def post_player_as_admin(payload):
    """POST /players is admin-only; create fixtures through an admin override."""
    previous = app.dependency_overrides.get(require_admin)
    app.dependency_overrides[require_admin] = lambda: {"sub": "auth0|admin"}
    try:
        return client.post("/players", json=payload)
    finally:
        if previous is None:
            app.dependency_overrides.pop(require_admin, None)
        else:
            app.dependency_overrides[require_admin] = previous


TEST_DATE = "2099-01-15"


def _unique_name():
    return f"TFPlayer-{uuid.uuid4().hex[:6]}"


def _create_profile(name=None, handicap=15.0):
    """Create a player profile and return the JSON response."""
    name = name or _unique_name()
    resp = post_player_as_admin({"name": name, "handicap": handicap})
    assert resp.status_code == 200, f"Failed to create profile: {resp.text}"
    return resp.json()


def _create_signup(date, profile_id, player_name, preferred_start_time=None):
    """Create a daily signup and return the JSON response."""
    payload = {"date": date}
    if preferred_start_time:
        payload["preferred_start_time"] = preferred_start_time
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=profile_id,
        legacy_name=player_name,
    )
    try:
        resp = client.post("/signups", json=payload)
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert resp.status_code == 200, f"Failed to create signup: {resp.text}"
    return resp.json()


def _unique_date():
    """Generate a date string that is extremely unlikely to collide with any other test."""
    # Use uuid to ensure uniqueness even across repeated test runs with persistent DB
    uid = uuid.uuid4().int
    year = 2200 + (uid % 800)  # 2200-2999
    month = uid % 12 + 1
    day = (uid >> 4) % 28 + 1
    return f"{year}-{month:02d}-{day:02d}"


def _clear_date(date):
    """Remove any signups already on `date` — the persistent test DB
    accumulates rows across runs, and _unique_date()'s ~269k-date space
    produces birthday-paradox collisions that made these tests flaky."""
    from app import models as _models
    from app.database import SessionLocal

    db = SessionLocal()
    db.query(_models.DailySignup).filter(_models.DailySignup.date == date).delete(synchronize_session=False)
    db.commit()
    db.close()


def _seed_signups(count, date=None):
    """Create `count` player profiles + signups for the given date.  Returns (date, profiles)."""
    date = date or _unique_date()
    _clear_date(date)
    profiles = []
    for i in range(count):
        name = _unique_name()
        profile = _create_profile(name=name, handicap=10.0 + i * 2)
        _create_signup(date, profile["id"], name)
        profiles.append(profile)
    return date, profiles


# ── GET /signups/{date}/players ────────────────────────────────────────────


class TestGetPlayersForDate:
    def test_get_players_returns_200(self):
        date, _ = _seed_signups(3)
        resp = client.get(f"/signups/{date}/players")
        assert resp.status_code == 200

    def test_get_players_response_shape(self):
        date, _ = _seed_signups(2)
        resp = client.get(f"/signups/{date}/players")
        data = resp.json()
        assert "date" in data
        assert "total_players" in data
        assert "players" in data
        assert "can_form_teams" in data
        assert "max_complete_teams" in data

    def test_get_players_count_matches(self):
        date, _profiles = _seed_signups(5)
        resp = client.get(f"/signups/{date}/players")
        data = resp.json()
        assert data["total_players"] == 5
        assert data["can_form_teams"] is True
        assert data["max_complete_teams"] == 1
        assert data["remaining_players"] == 1

    def test_get_players_empty_date(self):
        empty_date = _unique_date()
        _clear_date(empty_date)
        resp = client.get(f"/signups/{empty_date}/players")
        data = resp.json()
        assert data["total_players"] == 0
        assert data["can_form_teams"] is False

    def test_get_players_includes_handicap(self):
        date, profiles = _seed_signups(1)
        resp = client.get(f"/signups/{date}/players")
        data = resp.json()
        player = data["players"][0]
        assert "handicap" in player
        assert player["handicap"] == profiles[0]["handicap"]


# ── GET /pairings/{date} ──────────────────────────────────────────────────


class TestGetGeneratedPairings:
    def test_get_pairings_nonexistent_returns_exists_false(self):
        empty_date = _unique_date()
        _clear_date(empty_date)
        resp = client.get(f"/pairings/{empty_date}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["exists"] is False

    def test_get_pairings_returns_200(self):
        resp = client.get(f"/pairings/{TEST_DATE}")
        assert resp.status_code == 200


# ── DELETE /pairings/{date} ────────────────────────────────────────────────


class TestDeleteGeneratedPairings:
    def test_delete_nonexistent_pairings_returns_404(self):
        empty_date = _unique_date()
        _clear_date(empty_date)
        resp = client.delete(f"/pairings/{empty_date}")
        assert resp.status_code == 404
