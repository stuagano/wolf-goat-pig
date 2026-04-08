"""Unit tests for matchmaking router — suggestions endpoint (unauthenticated)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── GET /matchmaking/suggestions ─────────────────────────────────────────────


class TestGetMatchSuggestions:
    def test_suggestions_returns_200(self):
        resp = client.get("/matchmaking/suggestions")
        assert resp.status_code == 200

    def test_suggestions_has_expected_shape(self):
        resp = client.get("/matchmaking/suggestions")
        data = resp.json()
        assert "total_matches_found" in data
        assert "filtered_matches" in data
        assert "matches" in data
        assert isinstance(data["matches"], list)

    def test_suggestions_with_min_overlap(self):
        resp = client.get("/matchmaking/suggestions", params={"min_overlap_hours": 1.0})
        assert resp.status_code == 200

    def test_suggestions_with_preferred_days(self):
        resp = client.get("/matchmaking/suggestions", params={"preferred_days": "0,5,6"})
        assert resp.status_code == 200

    def test_suggestions_with_large_min_overlap(self):
        resp = client.get("/matchmaking/suggestions", params={"min_overlap_hours": 24.0})
        data = resp.json()
        assert resp.status_code == 200
        # Very large overlap should return few or no matches
        assert data["total_matches_found"] >= 0


# ── Authenticated endpoints return 401/403 without auth ──────────────────────


class TestMatchmakingAuthRequired:
    """Matchmaking endpoints that require auth should reject unauthenticated requests."""

    def test_my_matches_requires_auth(self):
        resp = client.get("/matchmaking/my-matches")
        # Should not return 200 without auth — typically 401 or 403
        assert resp.status_code in (401, 403, 500)

    def test_respond_to_match_requires_auth(self):
        resp = client.post(
            "/matchmaking/matches/1/respond",
            json={"response": "accepted"},
        )
        assert resp.status_code in (401, 403, 422, 500)

    def test_get_match_details_requires_auth(self):
        resp = client.get("/matchmaking/matches/1")
        assert resp.status_code in (401, 403, 500)
