"""GameStateModel.state is a MutableDict — in-place TOP-LEVEL mutations persist
without an explicit flag_modified.

This is the regression-prevention test for the silent JSON-write bug: previously
`game.state["x"] = y` followed by commit silently dropped the write because plain
Column(JSON) doesn't track in-place mutation. With MutableDict.as_mutable(JSON)
it's tracked automatically. The test deliberately does NOT call flag_modified —
that's the whole point.
"""

import uuid

from app import database, models

# Ensure tables exist regardless of import order.
models.Base.metadata.create_all(bind=database.engine)


def test_top_level_state_mutation_persists_without_flag_modified():
    gid = "mutable-test-" + uuid.uuid4().hex[:8]

    db = database.SessionLocal()
    try:
        db.add(
            models.GameStateModel(
                game_id=gid,
                game_status="in_progress",
                state={"hole_history": [], "current_hole": 1},
            )
        )
        db.commit()

        row = db.query(models.GameStateModel).filter_by(game_id=gid).first()
        # In-place top-level mutations — NO flag_modified anywhere.
        row.state["hole_history"] = [{"hole": 1, "points_delta": {"p1": 1}}]
        row.state["current_hole"] = 2
        db.commit()
        db.expunge_all()  # drop the identity-map copy so the re-read hits the DB
    finally:
        db.close()

    db2 = database.SessionLocal()
    try:
        fresh = db2.query(models.GameStateModel).filter_by(game_id=gid).first()
        assert fresh.state.get("current_hole") == 2, "top-level mutation did not persist"
        assert fresh.state.get("hole_history") == [{"hole": 1, "points_delta": {"p1": 1}}]
        db2.delete(fresh)
        db2.commit()
    finally:
        db2.close()


def test_none_state_is_handled():
    """MutableDict.as_mutable(JSON) must not choke on a NULL state column."""
    gid = "mutable-none-" + uuid.uuid4().hex[:8]
    db = database.SessionLocal()
    try:
        db.add(models.GameStateModel(game_id=gid, game_status="setup", state=None))
        db.commit()
        row = db.query(models.GameStateModel).filter_by(game_id=gid).first()
        assert row.state is None
        db.delete(row)
        db.commit()
    finally:
        db.close()
