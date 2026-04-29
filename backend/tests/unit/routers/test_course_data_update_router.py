"""Unit tests for course_data_update router — update single game, update all games."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import GameStateModel

client = TestClient(app)


# =============================================================================
# UPDATE SINGLE GAME COURSE DATA
# =============================================================================


class TestUpdateGameCourseData:
    def test_returns_404_for_nonexistent_game(self):
        resp = client.patch("/games/nonexistent-game-id/update-course-data")
        assert resp.status_code == 404

    def test_returns_200_for_existing_game_no_history(self):
        # First create a game via the app's own API so the DB has it
        from datetime import UTC, datetime

        from app.database import SessionLocal
        from app.models import GameStateModel

        db = SessionLocal()
        try:
            game = GameStateModel(
                game_id="test-course-update-1",
                game_status="in_progress",
                state={},
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            )
            db.add(game)
            db.commit()
        finally:
            db.close()

        resp = client.patch("/games/test-course-update-1/update-course-data")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["holes_updated"] == 0
        assert "No holes to update" in data["message"]

        # Cleanup
        db = SessionLocal()
        try:
            db.query(GameStateModel).filter(GameStateModel.game_id == "test-course-update-1").delete()
            db.commit()
        finally:
            db.close()

    def test_updates_hole_history_pars(self):
        from datetime import UTC, datetime

        from app.data.wing_point_course_data import WING_POINT_COURSE_DATA
        from app.database import SessionLocal

        # Get actual par for hole 1 from Wing Point data
        hole1_data = WING_POINT_COURSE_DATA["holes"][0]
        real_par = hole1_data["par"]
        wrong_par = real_par + 1  # Intentionally wrong

        db = SessionLocal()
        try:
            game = GameStateModel(
                game_id="test-course-update-2",
                game_status="in_progress",
                state={
                    "hole_history": [
                        {"hole": 1, "hole_par": wrong_par, "hole_handicap": 99},
                    ]
                },
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            )
            db.add(game)
            db.commit()
        finally:
            db.close()

        resp = client.patch("/games/test-course-update-2/update-course-data")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["holes_in_history_updated"] >= 1
        assert data["holes_configured"] == 18

        # Cleanup
        db = SessionLocal()
        try:
            db.query(GameStateModel).filter(GameStateModel.game_id == "test-course-update-2").delete()
            db.commit()
        finally:
            db.close()

    def test_adds_holes_config_to_game_state(self):
        from datetime import UTC, datetime

        from app.database import SessionLocal

        db = SessionLocal()
        try:
            game = GameStateModel(
                game_id="test-course-update-3",
                game_status="in_progress",
                state={"hole_history": [{"hole": 1, "hole_par": 4, "hole_handicap": 7}]},
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            )
            db.add(game)
            db.commit()
        finally:
            db.close()

        resp = client.patch("/games/test-course-update-3/update-course-data")
        assert resp.status_code == 200
        data = resp.json()
        assert data["holes_configured"] == 18

        # Verify the game state now has holes_config
        db = SessionLocal()
        try:
            game = db.query(GameStateModel).filter(GameStateModel.game_id == "test-course-update-3").first()
            assert game is not None
            state = game.state
            assert "holes_config" in state
            assert len(state["holes_config"]) == 18
            # Each entry should have hole_number, par, handicap
            first = state["holes_config"][0]
            assert "hole_number" in first
            assert "par" in first
            assert "handicap" in first
        finally:
            db.close()

        # Cleanup
        db = SessionLocal()
        try:
            db.query(GameStateModel).filter(GameStateModel.game_id == "test-course-update-3").delete()
            db.commit()
        finally:
            db.close()


# =============================================================================
# UPDATE ALL GAMES COURSE DATA
# =============================================================================


class TestUpdateAllGamesCourseData:
    def test_returns_200_with_no_games(self):
        # Make sure no in-progress games exist from other tests
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            # Count in-progress games (don't delete, just note count)
            count = db.query(GameStateModel).filter(GameStateModel.game_status == "in_progress").count()
        finally:
            db.close()

        resp = client.patch("/games/update-all-course-data")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_updates_multiple_in_progress_games(self):
        from datetime import UTC, datetime

        from app.database import SessionLocal

        db = SessionLocal()
        game_ids = ["test-bulk-1", "test-bulk-2"]
        try:
            for gid in game_ids:
                game = GameStateModel(
                    game_id=gid,
                    game_status="in_progress",
                    state={
                        "hole_history": [
                            {"hole": 1, "hole_par": 99, "hole_handicap": 99},
                        ]
                    },
                    created_at=datetime.now(UTC).isoformat(),
                    updated_at=datetime.now(UTC).isoformat(),
                )
                db.add(game)
            db.commit()
        finally:
            db.close()

        resp = client.patch("/games/update-all-course-data")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["games_updated"] >= 2
        assert data["holes_configured_per_game"] == 18
        assert "game_details" in data

        # Cleanup
        db = SessionLocal()
        try:
            for gid in game_ids:
                db.query(GameStateModel).filter(GameStateModel.game_id == gid).delete()
            db.commit()
        finally:
            db.close()

    def test_skips_completed_games(self):
        from datetime import UTC, datetime

        from app.database import SessionLocal

        db = SessionLocal()
        try:
            game = GameStateModel(
                game_id="test-bulk-completed",
                game_status="completed",
                state={"hole_history": [{"hole": 1, "hole_par": 99}]},
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            )
            db.add(game)
            db.commit()
        finally:
            db.close()

        resp = client.patch("/games/update-all-course-data")
        assert resp.status_code == 200
        data = resp.json()
        # The completed game should NOT appear in game_details
        if data.get("game_details"):
            game_ids_updated = [g["game_id"] for g in data["game_details"]]
            assert "test-bulk-completed" not in game_ids_updated

        # Cleanup
        db = SessionLocal()
        try:
            db.query(GameStateModel).filter(GameStateModel.game_id == "test-bulk-completed").delete()
            db.commit()
        finally:
            db.close()

    def test_response_includes_expected_keys(self):
        resp = client.patch("/games/update-all-course-data")
        assert resp.status_code == 200
        data = resp.json()
        assert "success" in data
        assert "message" in data
