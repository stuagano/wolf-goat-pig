"""Durable round alerts: synthetic recipients and mocked transports only."""

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app import models
from app.services import round_delivery as delivery
from app.utils.time import utc_now


@pytest.fixture(params=["sqlite", "postgres"])
def harness(tmp_path, monkeypatch, request):
    admin = None
    if request.param == "postgres":
        raw = os.environ.get("ROUND_IDENTITY_TEST_DATABASE_URL")
        if not raw:
            pytest.skip("Requires disposable localhost PostgreSQL *_test database")
        url = make_url(raw)
        assert url.host in {"localhost", "127.0.0.1", "::1"} and url.database.endswith("_test") and not url.query
        schema = "delivery_" + uuid4().hex
        admin = create_engine(url.set(drivername="postgresql+psycopg2"), poolclass=NullPool)
        with admin.begin() as tx:
            tx.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(
            url.set(drivername="postgresql+psycopg2"),
            poolclass=NullPool,
            connect_args={"options": f"-csearch_path={schema} -cstatement_timeout=10000"},
        )
    else:
        engine = create_engine(f"sqlite:///{tmp_path / 'delivery.db'}")
    models.Base.metadata.create_all(engine)
    factory = sessionmaker(engine)
    monkeypatch.setattr(delivery, "SessionLocal", factory)
    transport = Mock()
    transport.is_configured.return_value = True
    transport.send_round_conflict_notification.return_value = True
    monkeypatch.setattr(delivery, "get_email_service", lambda: transport)
    with factory() as db:
        db.add_all(
            [
                models.PlayerProfile(
                    id=7,
                    name="Reviewer",
                    email="review@example.invalid",
                    is_active=1,
                    preferences={"auth0_id": "auth0|fixture"},
                ),
                models.PlayerProfile(id=8, name="Admin", is_active=1, admin_granted=1),
                models.RoundSource(id="source", kind="sheet", scope="fixture", round_token="token"),
            ]
        )
        db.flush()
        db.add(models.RoundIssue(id="issue", source_id="source", kind="identity", fingerprint="fixture"))
        configure_recipient(db, 7)
        db.commit()
    # Prevent any application lifespan scheduler from calling real providers.
    monkeypatch.setenv("RUN_INPROCESS_SCHEDULERS", "false")
    yield factory, transport
    engine.dispose()
    if admin:
        with admin.begin() as tx:
            tx.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


def configure_recipient(db, profile_id):
    from app.schemas.round_identity import RecipientConfirmation
    from app.services.round_recipient import attest_recipient
    from app.services.round_review import confirm_routing

    profile = db.get(models.PlayerProfile, profile_id)
    proof = attest_recipient(
        db,
        profile_id,
        {
            "sub": profile.preferences["auth0_id"],
            "email": profile.email,
            "email_verified": True,
        },
    )
    confirm_routing(
        db,
        RecipientConfirmation(
            profile_id=profile_id,
            attestation_id=proof["attestation_id"],
            confirmed=True,
            reason="Synthetic test selection",
        ),
        db.get(models.PlayerProfile, 8),
        {},
    )


def enqueue(factory):
    with factory() as db:
        delivery.enqueue_round_deliveries(db, db.get(models.RoundIssue, "issue"))
        db.commit()


def read(factory):
    with factory() as db:
        return {r.channel: (r.status, r.attempts) for r in db.query(models.RoundDelivery).all()}


def test_both_channels_once_and_second_session_readback(harness):
    factory, transport = harness
    enqueue(factory)
    delivery.dispatch_round_deliveries()
    delivery.dispatch_round_deliveries()
    assert read(factory) == {"email": ("accepted", 1), "in_app": ("delivered", 1)}
    transport.send_round_conflict_notification.assert_called_once()
    with factory() as db:
        notification = db.query(models.Notification).one()
        assert notification.player_profile_id == 7
        assert notification.notification_type == "round_conflict"
        assert notification.data["path"] == "/rounds/reconciliation?issue=issue"
        assert notification.delivery_key


def test_false_transport_is_uncertain_and_never_retried(harness):
    factory, transport = harness
    enqueue(factory)
    transport.send_round_conflict_notification.return_value = False
    delivery.dispatch_round_deliveries()
    delivery.dispatch_round_deliveries()
    assert read(factory)["email"] == ("uncertain", 1)
    assert read(factory)["in_app"] == ("delivered", 1)
    transport.send_round_conflict_notification.assert_called_once()


def test_source_rollback_creates_neither_intent_nor_notification(harness):
    factory, transport = harness
    with factory() as db:
        delivery.enqueue_round_deliveries(db, db.get(models.RoundIssue, "issue"))
        db.rollback()
    delivery.dispatch_round_deliveries()
    assert read(factory) == {}
    transport.send_round_conflict_notification.assert_not_called()


def test_missing_confirmation_retains_two_unconfigured_intents(harness):
    factory, transport = harness
    with factory() as db:
        db.get(models.AppConfig, "round_identity").value = {"reviewer_profile_id": 7, "routing_confirmed": True}
        db.commit()
    enqueue(factory)
    delivery.dispatch_round_deliveries()
    assert read(factory) == {"email": ("unconfigured", 0), "in_app": ("unconfigured", 0)}
    transport.send_round_conflict_notification.assert_not_called()


def make_due(factory):
    with factory() as db:
        for row in db.query(models.RoundDelivery).filter(models.RoundDelivery.status.in_(["pending", "sending"])):
            row.lease_expires_at = None
        db.commit()


def test_rejected_before_acceptance_retries_bounded_without_resending_bell(harness):
    factory, transport = harness
    enqueue(factory)
    transport.send_round_conflict_notification.side_effect = delivery.RoundEmailRejectedError()
    for _ in range(7):
        make_due(factory)
        delivery.dispatch_round_deliveries()
    assert read(factory) == {"email": ("failed", 5), "in_app": ("delivered", 1)}
    assert transport.send_round_conflict_notification.call_count == 5


@pytest.mark.parametrize("after_flush", [False, True])
def test_notification_crash_rolls_back_marker_and_insert(harness, monkeypatch, after_flush):
    factory, _ = harness
    enqueue(factory)
    service = delivery.get_notification_service()
    original = service.send_notification

    def crash(*args, **kwargs):
        if after_flush:
            original(*args, **kwargs)
        raise RuntimeError("injected crash")

    with monkeypatch.context() as patch:
        patch.setattr(service, "send_notification", crash)
        delivery.dispatch_round_deliveries()
    with factory() as db:
        assert db.query(models.Notification).count() == 0
    assert read(factory)["in_app"] == ("pending", 1)
    make_due(factory)
    delivery.dispatch_round_deliveries()
    with factory() as db:
        assert db.query(models.Notification).count() == 1


def test_crash_after_durable_claim_never_blind_resends(harness):
    factory, transport = harness
    enqueue(factory)
    transport.send_round_conflict_notification.side_effect = KeyboardInterrupt("process died")
    with pytest.raises(KeyboardInterrupt):
        delivery.dispatch_round_deliveries()
    assert read(factory)["email"] == ("sending", 1)
    make_due(factory)
    delivery.dispatch_round_deliveries()
    assert read(factory)["email"] == ("uncertain", 1)
    assert read(factory)["in_app"] == ("delivered", 1)
    transport.send_round_conflict_notification.assert_called_once()


def test_unconfigured_provider_retries_with_backoff(harness):
    factory, transport = harness
    enqueue(factory)
    transport.is_configured.return_value = False
    delivery.dispatch_round_deliveries()
    delivery.dispatch_round_deliveries()
    assert read(factory)["email"] == ("pending", 1)
    assert read(factory)["in_app"] == ("delivered", 1)
    transport.send_round_conflict_notification.assert_not_called()


def test_recipient_change_requires_explicit_audited_requeue(harness):
    factory, transport = harness
    enqueue(factory)
    with factory() as db:
        db.add(
            models.PlayerProfile(
                id=9,
                name="New reviewer",
                email="new@example.invalid",
                is_active=1,
                preferences={"auth0_id": "auth0|new"},
            )
        )
        db.flush()
        configure_recipient(db, 9)
        db.commit()
    delivery.dispatch_round_deliveries()
    transport.send_round_conflict_notification.assert_not_called()
    with factory() as db:
        assert delivery.requeue_round_deliveries(db, ["issue"], actor_profile_id=8, reason="Confirmed change") == 2
        db.commit()
    delivery.dispatch_round_deliveries()
    with factory() as db:
        assert db.query(models.RoundDelivery).count() == 4
        assert db.query(models.RoundResolution).one().action == "routing_requeue"
        assert db.query(models.Notification).one().player_profile_id == 9
    transport.send_round_conflict_notification.assert_called_once()


@pytest.mark.parametrize("invalid", ["inactive", "duplicate_subject", "email_changed", "unverified", "no_actor"])
def test_invalid_linkage_stays_unconfigured(harness, invalid):
    factory, transport = harness
    with factory() as db:
        profile = db.get(models.PlayerProfile, 7)
        config = dict(db.get(models.AppConfig, "round_identity").value)
        if invalid == "inactive":
            profile.is_active = 0
        elif invalid == "email_changed":
            profile.email = "changed@example.invalid"
        elif invalid == "duplicate_subject":
            db.add(models.PlayerProfile(id=9, name="Duplicate", preferences={"auth0_id": "auth0|fixture"}))
        elif invalid == "no_actor":
            config["routing_confirmed_by_profile_id"] = None
        else:
            config["routing_linkage_evidence"] = {}
        db.get(models.AppConfig, "round_identity").value = config
        db.commit()
    enqueue(factory)
    delivery.dispatch_round_deliveries()
    assert all(status == "unconfigured" for status, _ in read(factory).values())
    transport.send_round_conflict_notification.assert_not_called()


def test_two_workers_claim_independently_with_no_duplicate_send(harness):
    factory, transport = harness
    if factory.kw["bind"].dialect.name != "postgresql":
        return  # PostgreSQL row locking is the production concurrency contract.
    enqueue(factory)
    entered, release = Event(), Event()

    def accepted(**kwargs):
        with factory() as db:
            assert db.query(models.RoundDelivery).filter_by(channel="email").one().status == "sending"
        entered.set()
        assert release.wait(10)
        return True

    transport.send_round_conflict_notification.side_effect = accepted
    with ThreadPoolExecutor(2) as workers:
        first = workers.submit(delivery.dispatch_round_deliveries)
        assert entered.wait(10)
        second = workers.submit(delivery.dispatch_round_deliveries)
        second.result(timeout=10)
        release.set()
        first.result(timeout=10)
    assert read(factory) == {"email": ("accepted", 1), "in_app": ("delivered", 1)}
    transport.send_round_conflict_notification.assert_called_once()
    with factory() as db:
        assert db.query(models.Notification).count() == 1


def test_filtered_before_limit_and_recipient_authorization(harness):
    from fastapi import HTTPException

    from app.routers.notifications import get_notifications, mark_read

    factory, _ = harness
    enqueue(factory)
    delivery.dispatch_round_deliveries()
    with factory() as db:
        for i in range(20):
            db.add(
                models.Notification(
                    player_profile_id=7,
                    notification_type="game_start",
                    message="other",
                    is_read=False,
                    created_at=f"9999-{i}",
                )
            )
        db.commit()
    with factory() as db:
        rows = get_notifications(True, 1, "round_conflict", db.get(models.PlayerProfile, 7), db)
        assert len(rows) == 1 and rows[0]["notification_type"] == "round_conflict"
        with pytest.raises(HTTPException) as denied:
            mark_read(rows[0]["id"], db.get(models.PlayerProfile, 8), db)
        assert denied.value.status_code == 404
        mark_read(rows[0]["id"], db.get(models.PlayerProfile, 7), db)
    with factory() as db:
        assert db.get(models.Notification, rows[0]["id"]).is_read


def test_requeue_is_admin_only_and_does_not_replay_success(harness):
    from fastapi import HTTPException

    factory, transport = harness
    enqueue(factory)
    delivery.dispatch_round_deliveries()
    with factory() as db:
        with pytest.raises(HTTPException) as denied:
            delivery.requeue_round_deliveries(db, ["issue"], actor_profile_id=7, reason="no")
        assert denied.value.status_code == 403
        assert delivery.requeue_round_deliveries(db, ["issue"], actor_profile_id=8, reason="already delivered") == 0
        db.commit()
    delivery.dispatch_round_deliveries()
    transport.send_round_conflict_notification.assert_called_once()


def test_uncertain_email_health_on_existing_bell_no_recursive_event(harness):
    from app.routers.notifications import get_notifications

    factory, transport = harness
    enqueue(factory)
    transport.send_round_conflict_notification.return_value = False
    delivery.dispatch_round_deliveries()
    with factory() as db:
        rows = get_notifications(True, 10, "round_conflict", db.get(models.PlayerProfile, 7), db)
        assert rows[0]["data"]["delivery_health"] == {"email": "uncertain"}
        assert db.query(models.RoundDelivery).count() == 2
        assert db.query(models.Notification).count() == 1


def test_same_event_enqueue_idempotent(harness):
    factory, _ = harness
    enqueue(factory)
    enqueue(factory)
    with factory() as db:
        assert db.query(models.RoundDelivery).count() == 2
        assert len({r.delivery_key for r in db.query(models.RoundDelivery)}) == 2


def test_precommit_email_crash_means_no_network_call(harness, monkeypatch):
    factory, transport = harness
    enqueue(factory)
    session_class = factory.class_
    original = session_class.commit

    def die(db):
        if any(isinstance(r, models.RoundDelivery) and r.status == "sending" for r in db.dirty):
            raise KeyboardInterrupt("before durable claim")
        return original(db)

    with monkeypatch.context() as patch:
        patch.setattr(session_class, "commit", die)
        with pytest.raises(KeyboardInterrupt):
            delivery.dispatch_round_deliveries()
    assert read(factory)["email"] == ("pending", 0)
    transport.send_round_conflict_notification.assert_not_called()
    delivery.dispatch_round_deliveries()
    transport.send_round_conflict_notification.assert_called_once()


def test_acceptance_then_crash_before_marker_never_resends(harness, monkeypatch):
    factory, transport = harness
    enqueue(factory)
    session_class = factory.class_
    original = session_class.commit

    def die(db):
        if any(isinstance(r, models.RoundDelivery) and r.status == "accepted" for r in db.dirty):
            raise KeyboardInterrupt("after provider acceptance")
        return original(db)

    with monkeypatch.context() as patch:
        patch.setattr(session_class, "commit", die)
        with pytest.raises(KeyboardInterrupt):
            delivery.dispatch_round_deliveries()
    assert read(factory)["email"] == ("sending", 1)
    make_due(factory)
    delivery.dispatch_round_deliveries()
    assert read(factory)["email"] == ("uncertain", 1)
    transport.send_round_conflict_notification.assert_called_once()


def test_scheduler_uses_one_shot_drain_with_mocked_transport(harness):
    from app.services.email_scheduler import email_scheduler

    factory, transport = harness
    enqueue(factory)
    result = email_scheduler.run_job("round-deliveries")
    assert result["status"] == "completed"
    assert read(factory)["email"] == ("accepted", 1)
    transport.send_round_conflict_notification.assert_called_once()


def test_existing_email_template_and_provider_only(monkeypatch):
    from app.services.email_service import EmailService

    service = object.__new__(EmailService)
    service.provider = Mock()
    service.provider.is_configured.return_value = True
    service.provider.send_email.return_value = True
    assert service.send_round_conflict_notification(
        to_email="fixture@example.invalid", issue_id="issue", path="/game/fixture"
    )
    args = service.provider.send_email.call_args.args
    assert "Review round" in args[2] and "Manage your email preferences" in args[2]
    assert "/game/fixture" in args[3]
    with pytest.raises(ValueError):
        service.send_round_conflict_notification(to_email="fixture@example.invalid", issue_id="issue", path="//evil")
    service.provider.send_email.assert_called_once()


@pytest.mark.parametrize(
    "path", ["https://evil.invalid", "//evil.invalid", "/\\evil", "/%2f%2fevil", "javascript:alert(1)", "/game/a\n"]
)
def test_safe_path_rejects_external_and_ambiguous_links(path):
    assert delivery.safe_round_path(path) is None
