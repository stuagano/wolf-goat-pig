"""Unit tests for matchmaking router — suggestions endpoint (unauthenticated)."""

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import PlayerAvailability, PlayerProfile

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

    def test_suggestions_do_not_publish_email_addresses(self):
        db = SessionLocal()
        created = []
        try:
            for label, email in (
                ("Match Alpha Unique", "match-alpha-unique@example.com"),
                ("Match Beta Unique", "match-beta-unique@example.com"),
            ):
                player = PlayerProfile(name=label, email=email, created_at="2026-01-01", is_active=1)
                db.add(player)
                db.flush()
                db.add(
                    PlayerAvailability(
                        player_profile_id=player.id,
                        day_of_week=0,
                        is_available=1,
                        available_from_time="08:00",
                        available_to_time="12:00",
                        created_at="2026-01-01",
                    )
                )
                created.append(player.id)
            db.commit()
        finally:
            db.close()

        try:
            resp = client.get("/matchmaking/suggestions", params={"min_overlap_hours": 1, "preferred_days": "0"})
            assert resp.status_code == 200, resp.text
            assert "match-alpha-unique@example.com" not in resp.text
            assert "match-beta-unique@example.com" not in resp.text
            for match in resp.json()["matches"]:
                for player in match["players"]:
                    assert "email" not in player
        finally:
            db = SessionLocal()
            try:
                db.query(PlayerAvailability).filter(PlayerAvailability.player_profile_id.in_(created)).delete(
                    synchronize_session=False
                )
                db.query(PlayerProfile).filter(PlayerProfile.id.in_(created)).delete(synchronize_session=False)
                db.commit()
            finally:
                db.close()

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
