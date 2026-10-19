"""Only the round's players and admins may change its card."""

import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import models
from app.database import SessionLocal, engine
from app.main import app
from app.services.auth_service import get_current_user

client = TestClient(app)

PER_HOLE = {
    "per_hole_quarters": [
        {"player_index": i, "hole": h, "quarters": q} for h in range(1, 19) for i, q in enumerate([2, -2])
    ]
}


def profile(**kw):
    base = {
        "id": 9001,
        "name": "Stranger",
        "email": "stranger@test.com",
        "preferences": {},
        "admin_granted": 0,
        "is_active": 1,
    }
    return SimpleNamespace(**{**base, **kw})


@pytest.fixture
def as_profile():
    def _set(p):
        app.dependency_overrides[get_current_user] = lambda: p

    yield _set
    app.dependency_overrides.pop(get_current_user, None)


def make_round(state_players, game_players=()):
    """A completed round. state_players go in state; game_players become GamePlayer rows."""
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        gid = str(uuid.uuid4())
        db.add(
            models.GameStateModel(
                game_id=gid, game_status="completed", state={"players": state_players, "hole_history": []}
            )
        )
        for slot, (profile_id, user_id) in enumerate(game_players):
            db.add(
                models.GamePlayer(
                    game_id=gid,
                    player_slot_id=f"p{slot}",
                    player_name=f"P{slot}",
                    player_profile_id=profile_id,
                    user_id=user_id,
                )
            )
        db.commit()
        return gid
    finally:
        db.close()


def stored_state(gid):
    db = SessionLocal()
    try:
        return dict(db.query(models.GameStateModel).filter_by(game_id=gid).one().state)
    finally:
        db.close()


TWO = [{"id": "a", "name": "A", "player_profile_id": 501}, {"id": "b", "name": "B"}]


def test_member_by_state_profile_id_may_edit(as_profile):
    gid = make_round(TWO)
    as_profile(profile(id=501, name="Alice"))
    assert client.patch(f"/games/{gid}/scorecard", json=PER_HOLE).status_code == 200


def test_member_by_auth0_sub_may_edit(as_profile):
    gid = make_round(
        [{"id": "p0", "name": "A"}, {"id": "p1", "name": "B"}], game_players=[(None, "auth0|alice"), (None, None)]
    )
    as_profile(profile(preferences={"auth0_id": "auth0|alice"}))
    assert client.patch(f"/games/{gid}/scorecard", json=PER_HOLE).status_code == 200


def test_member_by_game_player_profile_id_may_edit(as_profile):
    gid = make_round([{"id": "p0", "name": "A"}, {"id": "p1", "name": "B"}], game_players=[(777, None), (None, None)])
    as_profile(profile(id=777))
    assert client.patch(f"/games/{gid}/scorecard", json=PER_HOLE).status_code == 200


def test_admin_may_edit_any_round(as_profile, monkeypatch):
    monkeypatch.setenv("SUPER_ADMIN_EMAILS", "boss@test.com")
    gid = make_round(TWO)
    as_profile(profile(email="boss@test.com"))
    assert client.patch(f"/games/{gid}/scorecard", json=PER_HOLE).status_code == 200


def test_signed_in_non_member_is_forbidden(as_profile):
    gid = make_round(TWO)
    as_profile(profile())
    assert client.patch(f"/games/{gid}/scorecard", json=PER_HOLE).status_code == 403


def test_anonymous_is_unauthorized():
    gid = make_round(TWO)
    assert client.patch(f"/games/{gid}/scorecard", json=PER_HOLE).status_code == 401


def test_patch_records_who_edited(as_profile):
    gid = make_round(TWO)
    as_profile(profile(id=501, name="Alice"))
    client.patch(f"/games/{gid}/scorecard", json=PER_HOLE)
    state = stored_state(gid)
    assert state["card_edited_by"] == "Alice"
    assert state["card_edited_at"].startswith("20")
