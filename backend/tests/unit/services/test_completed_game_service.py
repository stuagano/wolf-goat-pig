from app.services.completed_game_service import build_hole_history


def test_build_hole_history_maps_indices_to_player_ids_and_sums_standings():
    players = [
        {"id": "p1", "name": "John", "player_profile_id": 1},
        {"id": "p2", "name": "Mary", "player_profile_id": None},
    ]
    per_hole = [
        {"player_index": 0, "hole": 1, "quarters": 2},
        {"player_index": 1, "hole": 1, "quarters": -2},
        {"player_index": 0, "hole": 2, "quarters": -1},
        {"player_index": 1, "hole": 2, "quarters": 1},
    ]
    hole_history, standings = build_hole_history(players, per_hole)

    assert hole_history == [
        {"hole": 1, "points_delta": {"p1": 2, "p2": -2}},
        {"hole": 2, "points_delta": {"p1": -1, "p2": 1}},
    ]
    assert standings == {"p1": 1, "p2": -1}


import json
import uuid

from sqlalchemy import text

from app import models
from app.database import SessionLocal, engine
from app.services.completed_game_service import build_hole_history, persist_completed_game


def _session():
    models.Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_persist_completed_game_writes_record_and_results_on_sqlite():
    db = _session()
    try:
        players = [
            {"id": "p1", "name": "Alice", "player_profile_id": None, "handicap": 10},
            {"id": "p2", "name": "Bob", "player_profile_id": None, "handicap": 8},
            {"id": "p3", "name": "Cara", "player_profile_id": None, "handicap": 12},
            {"id": "p4", "name": "Dan", "player_profile_id": None, "handicap": 6},
        ]
        per_hole = []
        for h in range(1, 19):
            per_hole += [
                {"player_index": 0, "hole": h, "quarters": 1},
                {"player_index": 1, "hole": h, "quarters": 1},
                {"player_index": 2, "hole": h, "quarters": -1},
                {"player_index": 3, "hole": h, "quarters": -1},
            ]
        hole_history, standings = build_hole_history(players, per_hole)
        game_id = str(uuid.uuid4())
        game = models.GameStateModel(
            game_id=game_id,
            game_status="completed",
            state={
                "players": players,
                "hole_history": hole_history,
                "hole_quarters": {str(h): {} for h in range(1, 19)},
                "standings": standings,
                "course_name": "Wing Point",
            },
            created_at="2026-06-18T00:00:00",
            updated_at="2026-06-18T00:00:00",
        )
        db.add(game)
        db.commit()

        created = persist_completed_game(db, game)
        assert created == 4

        rec = db.query(models.GameRecord).filter(models.GameRecord.game_id == game_id).first()
        assert rec is not None
        assert rec.player_count == 4

        rows = db.execute(
            text(
                "SELECT player_name, total_earnings, final_position, hole_scores "
                "FROM game_player_results WHERE game_record_id = :rid ORDER BY final_position"
            ),
            {"rid": rec.id},
        ).fetchall()
        assert len(rows) == 4
        # Alice/Bob each +18, ranked above Cara/Dan at -18
        top = rows[0]
        assert top.total_earnings == 18
        # hole_scores must round-trip as JSON, not be corrupted to 0
        assert json.loads(top.hole_scores)[0]["hole"] == 1
    finally:
        db.rollback()
        db.close()
