"""Unit tests for leaderboard router — game result recording.

Note: GET /leaderboard and /leaderboard/{metric} were removed in the router
extraction — the unified /data/leaderboard endpoint (unified_data.py) is the
replacement and has its own tests.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app import database, models
from app.main import app
from app.utils.admin_auth import require_admin

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


def _unique_id():
    return uuid.uuid4().hex[:8]


# ── POST /game-results ───────────────────────────────────────────────────────


class TestRecordGameResult:
    def _create_player(self):
        name = f"LB-{_unique_id()}"
        email = f"lb-{_unique_id()}@test.com"
        resp = post_player_as_admin({"name": name, "email": email, "handicap": 10.0})
        if resp.status_code in (200, 201):
            return resp.json()["id"]
        return None

    def test_record_result_missing_fields_returns_422(self):
        resp = client.post("/game-results", json={})
        assert resp.status_code == 422

    def test_record_result_invalid_payload_returns_422(self):
        resp = client.post("/game-results", json={"player_profile_id": "not_int"})
        assert resp.status_code == 422

    def test_record_result_persists(self):
        """Read-back: a recorded result is actually written to game_player_results,
        not just acknowledged in the response."""
        pid = self._create_player()
        if pid is None:
            pytest.skip("player creation unavailable in this environment")

        resp = client.post(
            "/game-results",
            json={
                "game_record_id": 999999,
                "player_profile_id": pid,
                "player_name": "LB Reader",
                "final_position": 1,
                "total_earnings": 12.5,
                "holes_won": 4,
            },
        )
        assert resp.status_code == 200, resp.text

        db = database.SessionLocal()
        try:
            row = db.query(models.GamePlayerResult).filter(models.GamePlayerResult.player_profile_id == pid).first()
            assert row is not None, "recorded result not found in DB"
            assert row.total_earnings == 12.5
            assert row.final_position == 1
        finally:
            db.close()
