"""Real-connection mapped-roster transactions, absence locks and rollback."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Event

import pytest
from sqlalchemy import event, select, text

from app import models
from tests.unit.participant_audit_guard_support import MUTATIONS, assert_audit_guard
from tests.unit.round_identity_postgres_support import identity_pg, race
from tests.unit.routers.test_participant_correction_mapped import corrected, state_blob
from tests.unit.test_participant_correction_postgres import GAME, PATH, request, setup_api


def seed_roster(pg):
    with pg.sessions() as db:
        db.add(models.GameStateModel(game_id=GAME, state=state_blob(), game_status="completed", revision=0))
        db.add(models.GamePlayer(game_id=GAME, player_slot_id="p3", player_name="Stuart Gano", player_profile_id=21))
        db.commit()


def snapshot(pg):
    with pg.sessions() as db:
        return {
            m.__tablename__: [deepcopy(dict(r)) for r in db.execute(select(m.__table__).order_by(m.id)).mappings()]
            for m in (
                models.GameStateModel,
                models.GamePlayer,
                models.GameRecord,
                models.GamePlayerResult,
                models.PlayerProfile,
                models.PlayerStatistics,
                models.Notification,
                models.PendingSheetSync,
                models.PlayerAchievement,
            )
        }


def test_mapped_concurrent_retry_full_independent_readback(identity_pg):
    pg = identity_pg
    setup_api(pg)
    seed_roster(pg)
    before = snapshot(pg)
    body = request(pg)
    responses = race(*[lambda: pg.client.post(PATH + "/correct", json=body) for _ in range(2)])
    assert [r.status_code for r in responses] == [200, 200], [r.text for r in responses]
    assert responses[0].json()["audit_id"] == responses[1].json()["audit_id"]
    expected = deepcopy(before)
    expected["game_state"][0]["state"] = corrected(state_blob())
    expected["game_players"][0]["player_profile_id"] = 20
    expected["game_player_results"][0]["player_profile_id"] = 20
    assert snapshot(pg) == expected
    with pg.sessions() as db:
        audit = db.query(models.ParticipantCorrectionAudit).one()
        assert audit.before["_roster"]["game"] == before["game_state"][0]
        assert audit.after["_roster"]["players"] == expected["game_players"]
        assert db.query(models.ParticipantCorrectionAudit).count() == 1
    for mutation in MUTATIONS + ["TRUNCATE TABLE participant_correction_audits CASCADE"]:
        assert_audit_guard(pg.sessions, mutation)


def test_mapped_competing_previews_are_serialized(identity_pg):
    pg = identity_pg
    setup_api(pg)
    seed_roster(pg)
    first = request(pg)
    second = request(pg, "different-request")
    responses = race(
        lambda: pg.client.post(PATH + "/correct", json=first), lambda: pg.client.post(PATH + "/correct", json=second)
    )
    assert sorted(r.status_code for r in responses) == [200, 409], [r.text for r in responses]
    with pg.sessions() as db:
        assert db.query(models.ParticipantCorrectionAudit).count() == 1
        assert db.query(models.GamePlayer).one().player_profile_id == 20


@pytest.mark.parametrize("change", ["revision", "source", "roster", "slot", "duplicate"])
def test_mapped_preview_rechecks_new_authority_and_roster(identity_pg, change):
    pg = identity_pg
    setup_api(pg)
    seed_roster(pg)
    body = request(pg)
    with pg.sessions() as db:
        game = db.query(models.GameStateModel).one()
        if change == "revision":
            game.revision = 1
        elif change == "source":
            db.add(models.RoundSource(kind="sheet", scope="new", round_token="token", game_id=GAME))
        elif change == "roster":
            state = deepcopy(game.state)
            state["players"][0]["handicap"] = 9
            game.state = state
        elif change == "slot":
            db.query(models.GamePlayer).one().handicap = 9
        else:
            db.add(models.GamePlayerResult(game_record_id=10, player_name="Other", player_profile_id=20))
        db.commit()
    before = snapshot(pg)
    response = pg.client.post(PATH + "/correct", json=body)
    assert response.status_code == 409, response.text
    assert snapshot(pg) == before
    with pg.sessions() as db:
        assert db.query(models.ParticipantCorrectionAudit).count() == 0


def test_mapped_audit_failure_rolls_back_all_links(identity_pg):
    pg = identity_pg
    setup_api(pg)
    seed_roster(pg)
    body = request(pg)
    with pg.engine.begin() as conn:
        conn.execute(
            text(
                "CREATE FUNCTION reject_mapped_audit() RETURNS trigger LANGUAGE plpgsql AS $$ "
                "BEGIN RAISE EXCEPTION 'synthetic mapped audit failure'; END $$"
            )
        )
        conn.execute(
            text(
                "CREATE TRIGGER reject_mapped_audit BEFORE INSERT ON participant_correction_audits "
                "FOR EACH ROW EXECUTE FUNCTION reject_mapped_audit()"
            )
        )
    before = snapshot(pg)
    assert pg.client.post(PATH + "/correct", json=body).status_code == 500
    assert snapshot(pg) == before
    with pg.sessions() as db:
        assert db.query(models.ParticipantCorrectionAudit).count() == 0


def test_unfenced_source_writer_cannot_enter_after_absence_check(identity_pg):
    pg = identity_pg
    setup_api(pg)
    seed_roster(pg)
    body = request(pg)
    at_audit = Event()
    release = Event()
    insert_attempted = Event()
    inserted = Event()

    def hold_audit(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO participant_correction_audits"):
            at_audit.set()
            assert release.wait(10)
        if statement.startswith("INSERT INTO round_sources"):
            insert_attempted.set()

    def source_writer():
        with pg.sessions() as db:
            db.add(models.RoundSource(kind="sheet", scope="racer", round_token="racer", game_id=GAME))
            db.commit()
            inserted.set()

    event.listen(pg.engine, "before_cursor_execute", hold_audit)
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            correction = executor.submit(pg.client.post, PATH + "/correct", json=body)
            try:
                assert at_audit.wait(10)
                source = executor.submit(source_writer)
                assert insert_attempted.wait(5)
                assert not inserted.wait(0.2), "source insertion crossed absence lock"
            finally:
                release.set()
            response = correction.result(timeout=15)
            assert response.status_code == 200, response.text
            source.result(timeout=15)
    finally:
        release.set()
        event.remove(pg.engine, "before_cursor_execute", hold_audit)
    assert inserted.is_set()  # legal later writer; no claim to fence future transactions
