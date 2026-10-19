import base64
import uuid
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app import models
from app.database import SessionLocal, engine
from app.main import app
from app.services.auth_service import get_current_user

client = TestClient(app)


def _make_round_with_image(image_b64: str | None) -> str:
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        gid = str(uuid.uuid4())
        g = models.GameStateModel(game_id=gid, game_status="completed", state={}, scorecard_image=image_b64)
        db.merge(g)
        db.commit()
        return g.game_id
    finally:
        db.close()


def test_get_scorecard_photo_returns_image_bytes():
    raw = b"\xff\xd8\xff\xe0jpegbytes"
    gid = _make_round_with_image("data:image/jpeg;base64," + base64.b64encode(raw).decode())
    resp = client.get(f"/games/{gid}/scorecard-photo")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/")
    assert resp.content == raw


def test_get_scorecard_photo_404_when_none():
    gid = _make_round_with_image(None)
    assert client.get(f"/games/{gid}/scorecard-photo").status_code == 404


def test_patch_scorecard_recomputes_standings_from_new_per_hole(monkeypatch):
    monkeypatch.setenv("SUPER_ADMIN_EMAILS", "boss@test.com")
    try:
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id=1, name="Boss", email="boss@test.com", preferences={}, admin_granted=0, is_active=1
        )
        # Totals-only UI sends explicit zeroes on holes 1-17.
        models.Base.metadata.create_all(bind=engine)
        create = client.post(
            "/games/from-scorecard",
            json={
                "players": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}],
                "per_hole_quarters": [
                    {"player_index": i, "hole": h, "quarters": q if h == 18 else 0}
                    for h in range(1, 19)
                    for i, q in enumerate([8, -8, 4, -4])
                ],
            },
        )
        gid = create.json()["game_id"]
        # backfill: spread A's +8 across holes 1 and 2 (sum still 8) — standings unchanged
        patch = client.patch(
            f"/games/{gid}/scorecard",
            json={
                "per_hole_quarters": [
                    {
                        "player_index": i,
                        "hole": h,
                        "quarters": ([5, -5, 4, -4] if h == 1 else [3, -3, 0, 0] if h == 2 else [0, 0, 0, 0])[i],
                    }
                    for h in range(1, 19)
                    for i in range(4)
                ]
            },
        )
        assert patch.status_code == 200, patch.text
        db = SessionLocal()
        try:
            state = db.query(models.GameStateModel).filter_by(game_id=gid).first().state
            assert {e["hole"] for e in state["hole_history"]} == set(range(1, 19))
            # standings preserved: A total +8
            assert state["standings"]["p1"] == 8

            # I1 regression guard: GameRecord.final_scores must reflect the new standings
            # after PATCH (not the stale initial values from before the backfill).
            record = db.query(models.GameRecord).filter_by(game_id=gid).first()
            assert record is not None, "GameRecord must exist after backfill"
            assert record.final_scores is not None, "GameRecord.final_scores must be set"
            assert record.final_scores.get("p1") == 8, (
                f"GameRecord.final_scores['p1'] should be 8 after backfill, got {record.final_scores.get('p1')}"
            )
            assert record.total_holes_played == 18
        finally:
            db.close()
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_patch_scorecard_404_for_missing_round():
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, name="Boss", email="x@test.com", preferences={}, admin_granted=0, is_active=1
    )
    try:
        assert client.patch("/games/nope/scorecard", json={"per_hole_quarters": []}).status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)
