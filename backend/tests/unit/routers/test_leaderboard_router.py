"""Unit tests for leaderboard router — game result recording.

Note: GET /leaderboard and /leaderboard/{metric} were removed in the router
extraction — the unified /data/leaderboard endpoint (unified_data.py) is the
replacement and has its own tests.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_id():
    return uuid.uuid4().hex[:8]


# ── POST /game-results ───────────────────────────────────────────────────────


class TestRecordGameResult:
    def _create_player(self):
        name = f"LB-{_unique_id()}"
        email = f"lb-{_unique_id()}@test.com"
        resp = client.post("/players", json={"name": name, "email": email, "handicap": 10.0})
        if resp.status_code in (200, 201):
            return resp.json()["id"]
        return None

    def test_record_result_missing_fields_returns_422(self):
        resp = client.post("/game-results", json={})
        assert resp.status_code == 422

    def test_record_result_invalid_payload_returns_422(self):
        resp = client.post("/game-results", json={"player_profile_id": "not_int"})
        assert resp.status_code == 422
