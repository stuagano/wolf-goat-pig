"""Required PG15 race/rollback proofs, read through new physical connections."""

from threading import Event

import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app import models
from app.schemas.round_identity import ResolutionDecision
from app.services.round_reconciliation import observe_round, resolve_issue
from tests.unit.round_identity_postgres_support import identity_pg, race
from tests.unit.services.test_round_identity_migration import migration_fixture
from tests.unit.services.test_round_reconciliation import draft, source


def ingest(harness, ref=None, value=None, key="one"):
    with harness.sessions() as db:
        harness.writer_pids.add(db.scalar(text("SELECT pg_backend_pid()")))
        outcome = observe_round(
            db, ref or source(), value or draft(), observation_key=key, raw_payload={}, continuity_verified=True
        )
        db.commit()
        return outcome


@pytest.mark.parametrize("kind", ["same_token", "two_scopes", "two_actors"])
def test_simultaneous_creators_recheck_committed_identity(identity_pg, kind):
    h = identity_pg

    def operation(index):
        if kind != "two_actors":
            return ingest(h, source(scope="one" if kind == "same_token" else str(index)))
        from app.services.round_cutover import guard_writer
        from app.services.round_writes import create_observation

        with h.sessions() as db:
            h.writer_pids.add(db.scalar(text("SELECT pg_backend_pid()")))
            guard_writer(db, expected_epoch=4)
            _, outcome = create_observation(db, index + 1, "same-real-round", {}, draft(), "manual")
            db.commit()
            return type("Outcome", (), outcome)()

    outcomes = race(lambda: operation(0), lambda: operation(1))
    durable = h.snapshot()
    assert len(durable["game_state"]) == len(durable["game_records"]) == 1
    assert len(durable["game_player_results"]) == 2
    ids = {o.game_id for o in outcomes if o.game_id}
    assert ids == {durable["game_state"][0]["game_id"]}
    if kind == "same_token":
        assert sorted(o.status for o in outcomes) == ["accepted", "unchanged"]
        assert len(durable["round_sources"]) == len(durable["round_observations"]) == 1
        assert durable["round_deliveries"] == []
    else:
        assert sorted(o.status for o in outcomes) == ["accepted", "held"]
        assert len(durable["round_sources"]) == 2
        assert len(durable["round_issues"]) == 1
        assert len(durable["round_deliveries"]) == 2
        assert set(durable["round_issues"][0]["candidate_game_ids"]) == ids
    if kind == "two_actors":
        assert len(durable["round_requests"]) == 2


@pytest.mark.parametrize("phase", ["new_game", "existing_game"])
def test_issue_trigger_failure_rolls_back_projection_and_both_intents(identity_pg, phase):
    h = identity_pg
    if phase == "existing_game":
        ingest(h)
    before = h.snapshot()
    with h.engine.begin() as conn:
        conn.execute(
            text("""CREATE FUNCTION reject_fixture_issue() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'fixture rejects issue commit'; END $$""")
        )
        conn.execute(
            text(
                "CREATE TRIGGER reject_issue BEFORE INSERT ON round_issues "
                "FOR EACH ROW EXECUTE FUNCTION reject_fixture_issue()"
            )
        )
    try:
        with pytest.raises(DBAPIError, match="fixture rejects issue commit"), h.sessions() as db:
            if phase == "new_game":
                observe_round(db, source(), draft(), observation_key="first", raw_payload={}, continuity_verified=True)
                observe_round(
                    db, source("overlap"), draft(), observation_key="overlap", raw_payload={}, continuity_verified=True
                )
            else:
                value = draft(course_name="Disputed")
                observe_round(db, source(), value, observation_key="changed", raw_payload={}, continuity_verified=True)
            db.commit()
        assert h.snapshot() == before
    finally:
        with h.engine.begin() as conn:
            conn.execute(text("DROP TRIGGER reject_issue ON round_issues"))
            conn.execute(text("DROP FUNCTION reject_fixture_issue()"))


def test_expired_owner_cannot_publish_or_release_successor_lease(identity_pg):
    from app.services.round_source_lease import SourceLeaseLostError, fence, heartbeat, source_lease

    h = identity_pg
    with source_lease(h.engine, "fixture") as stale:
        with h.sessions() as db:
            db.get(models.RoundIdentityLease, stale[0]).expires_at = "2000-01-01"
            db.commit()
        with source_lease(h.engine, "fixture") as fresh:
            assert fresh[2] == stale[2] + 1
            with pytest.raises(SourceLeaseLostError):
                heartbeat(h.engine, stale)
            with pytest.raises(SourceLeaseLostError), h.sessions() as db:
                fence(db, stale)
            with h.sessions() as db:
                row = fence(db, fresh)
                assert row.owner == fresh[1]
            # stale context exit must not clear the newer owner's claim.
    with h.sessions() as db:
        row = db.get(models.RoundIdentityLease, stale[0])
        assert row.epoch == fresh[2] and row.owner is None
    assert h.snapshot()["game_records"] == []


def test_new_evidence_wins_against_waiting_stale_resolution(identity_pg):
    h = identity_pg
    ingest(h)
    conflict = ingest(h, value=draft(course_name="B"), key="b")
    with h.sessions() as db:
        issue = db.get(models.RoundIssue, conflict.issue_ids[0])
        old_id = issue.id
        decision = ResolutionDecision(
            action="accept",
            reason="Old evidence",
            expected_game_revision=conflict.revision,
            expected_issue_revision=issue.revision,
            expected_head_revision=issue.head_revision,
        )
    entered, release = Event(), Event()

    def newer():
        with h.sessions() as db:
            outcome = observe_round(
                db, source(), draft(course_name="C"), observation_key="c", raw_payload={}, continuity_verified=True
            )
            entered.set()
            assert release.wait(10)
            db.commit()
            return outcome

    def stale():
        assert entered.wait(10)
        release.set()
        with h.sessions() as db:
            with pytest.raises(HTTPException) as error:
                resolve_issue(db, old_id, decision, actor_profile_id=8)
            assert error.value.status_code == 409
            db.rollback()

    race(newer, stale)
    durable = h.snapshot()
    assert durable["game_records"][0]["course_name"] == "Wing Point"
    assert next(i for i in durable["round_issues"] if i["id"] == old_id)["status"] == "superseded"
    assert any(i["proposed_value"] == "C" and i["status"] == "open" for i in durable["round_issues"])
    assert durable["round_resolutions"] == []


def test_duplicate_channel_workers_have_single_receipt_per_event(identity_pg, monkeypatch):
    from unittest.mock import Mock

    from app.services import round_delivery as delivery
    from tests.unit.services.test_round_delivery import configure_recipient

    h = identity_pg
    with h.sessions() as db:
        configure_recipient(db, 7)
        db.commit()
    ingest(h)
    ingest(h, value=draft(course_name="Changed"), key="conflict")
    monkeypatch.setattr(delivery, "SessionLocal", h.sessions)
    transport = Mock()
    transport.is_configured.return_value = True
    entered, release = Event(), Event()

    def send(**_):
        entered.set()
        assert release.wait(10)
        return True

    transport.send_round_conflict_notification.side_effect = send
    monkeypatch.setattr(delivery, "get_email_service", lambda: transport)

    def second():
        assert entered.wait(10)
        try:
            return delivery.dispatch_round_deliveries()
        finally:
            release.set()

    race(delivery.dispatch_round_deliveries, second)
    delivery.dispatch_round_deliveries()
    durable = h.snapshot()
    assert {d["channel"]: (d["status"], d["attempts"]) for d in durable["round_deliveries"]} == {
        "email": ("accepted", 1),
        "in_app": ("delivered", 1),
    }
    assert len(durable["notifications"]) == 1
    assert durable["notifications"][0]["delivery_key"]
    transport.send_round_conflict_notification.assert_called_once()


def test_mounted_stale_client_cannot_replay_after_pause_and_fixture_resume(identity_pg):
    from app.services.round_cutover import pause_writers
    from tests.unit.routers.test_round_reconciliation_api import login

    h = identity_pg
    login(h.app, h.sessions, 8)
    with h.sessions() as db:
        config = db.get(models.AppConfig, "round_identity")
        config.value = {**config.value, "require_client_epoch": True}
        db.add(models.GameStateModel(game_id="epoch-fixture", state={}, game_status="in_progress"))
        db.commit()
    with h.sessions() as db:
        assert pause_writers(db, expected_epoch=4, reason="Synthetic epoch rehearsal") == 5
        db.commit()
    before = h.snapshot()
    body = {"expected_epoch": 4, "expected_revision": 0, "holes": []}
    paused = h.client.post("/games/epoch-fixture/scores", json=body)
    assert paused.status_code == 409, paused.text
    assert h.snapshot() == before
    # Synthetic configuration transition only: this is not Gate D activation.
    with h.sessions() as db:
        config = db.get(models.AppConfig, "round_identity")
        config.value = {**config.value, "mode": "canonical", "epoch": 6}
        db.commit()
    resumed = h.snapshot()
    for payload in (body, {k: v for k, v in body.items() if k != "expected_epoch"}):
        response = h.client.post("/games/epoch-fixture/scores", json=payload)
        assert response.status_code == 409, response.text
        assert h.snapshot() == resumed
    with h.sessions() as db:
        assert db.query(models.HoleEvent).count() == 0


def test_pg15_manifest_rerun_preserves_uuid_social_and_unknowns(identity_pg, migration_fixture):
    from app.services.round_identity_migration import apply_manifest, verify_manifest
    from tests.unit.services.test_round_identity_migration import approved

    h = identity_pg
    original, snapshot = migration_fixture
    with original.connect() as reader, h.engine.begin() as writer:
        for model in (models.LegacyRound, models.RoundComment, models.RoundReaction):
            for row in reader.execute(model.__table__.select()).mappings():
                writer.execute(model.__table__.insert().values(**dict(row)))
    with h.sessions() as db:
        config = db.get(models.AppConfig, "round_identity")
        config.value = {"mode": "paused", "epoch": 3, "season": 2026}
        db.commit()
        manifest = approved(db, snapshot)
        first = apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        db.commit()
    before = h.snapshot()
    with h.sessions() as db:
        second = apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        assert verify_manifest(db, manifest)["errors"] == []
        db.commit()
    assert first["game_ids"] == second["game_ids"]
    assert h.snapshot() == before
    with h.sessions() as reader:
        game_id = first["game_ids"][0]
        assert reader.get(models.RoundComment, 1).game_id == game_id
        assert reader.get(models.RoundReaction, 1).game_id == game_id
        record = reader.query(models.GameRecord).one()
        assert record.total_holes_played is None and record.course_name is None
        assert reader.query(models.GamePlayerResult).one().holes_won is None
