"""Task 6 review regressions; real local transactions, mocked transports."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import event

from app import models
from app.database import get_db
from app.routers import notifications
from app.services import round_delivery as delivery
from app.services.auth_service import get_current_user
from tests.unit.services.test_round_delivery import configure_recipient, enqueue, harness, make_due, read


def route(factory, recipient):
    with factory() as db:
        if recipient == 9 and db.get(models.PlayerProfile, 9) is None:
            db.add(
                models.PlayerProfile(
                    id=9, name="B", email="b@example.invalid", is_active=1, preferences={"auth0_id": "auth0|b"}
                )
            )
            db.flush()
        configure_recipient(db, recipient)
        db.commit()


def requeue(factory):
    with factory() as db:
        result = delivery.requeue_round_deliveries(db, ["issue"], actor_profile_id=8, reason="Explicit routing change")
        db.commit()
        return result


@pytest.mark.parametrize("initial_unconfigured", [False, True])
def test_a_b_a_reactivates_only_unsent_replaced_intents(harness, initial_unconfigured):
    factory, transport = harness
    enqueue(factory)
    if initial_unconfigured:
        with factory() as db:
            for row in db.query(models.RoundDelivery):
                row.status = "unconfigured"
            db.commit()
    route(factory, 9)
    assert requeue(factory) == 2
    route(factory, 7)
    assert requeue(factory) == 2
    assert requeue(factory) == 0
    with factory() as db:
        rows = db.query(models.RoundDelivery).all()
        assert len(rows) == 4
        assert {r.status for r in rows if r.recipient_profile_id == 7} == {"pending"}
        assert {r.status for r in rows if r.recipient_profile_id == 9} == {"replaced"}
    delivery.dispatch_round_deliveries()
    assert requeue(factory) == 0
    with factory() as db:
        assert db.query(models.Notification).one().player_profile_id == 7
        assert {r.status for r in db.query(models.RoundDelivery).filter_by(recipient_profile_id=7)} == {
            "accepted",
            "delivered",
        }
    transport.send_round_conflict_notification.assert_called_once()


def test_requeue_never_reactivates_uncertain_former_recipient(harness):
    factory, transport = harness
    enqueue(factory)
    transport.send_round_conflict_notification.return_value = False
    delivery.dispatch_round_deliveries()
    route(factory, 9)
    requeue(factory)
    route(factory, 7)
    assert requeue(factory) == 0
    delivery.dispatch_round_deliveries()
    transport.send_round_conflict_notification.assert_called_once()
    with factory() as db:
        assert (
            db.query(models.RoundDelivery).filter_by(recipient_profile_id=7, channel="email").one().status
            == "uncertain"
        )


def test_two_failing_pg_workers_preserve_lock_attempts_and_backoff(harness, monkeypatch):
    factory, _ = harness
    engine = factory.kw["bind"]
    if engine.dialect.name != "postgresql":
        return
    enqueue(factory)
    # Only exercise notification transactions; email is not relevant to this race.
    with factory() as db:
        db.query(models.RoundDelivery).filter_by(channel="email").update({"status": "accepted"})
        db.commit()
    rollback_entered, release_recovery, second_connected = Event(), Event(), Event()
    locked_delivery = []
    service = delivery.get_notification_service()
    sends = []

    def fail(*args, **kwargs):
        sends.append(1)
        # Flush the actual insert, then fail inside the notification transaction.
        original(*args, **kwargs)
        raise RuntimeError("injected notification failure")

    original = service.send_notification
    monkeypatch.setattr(service, "send_notification", fail)

    def on_rollback(session, transaction):
        if not rollback_entered.is_set():
            rollback_entered.set()
            assert release_recovery.wait(10)

    def connection_seen(connection, cursor, statement, parameters, context, executemany):
        if "FROM round_deliveries" in statement and "FOR UPDATE" in statement and rollback_entered.is_set():
            second_connected.set()

    event.listen(factory.class_, "after_soft_rollback", on_rollback)
    event.listen(engine, "before_cursor_execute", connection_seen)
    try:
        with ThreadPoolExecutor(2) as workers:
            first = workers.submit(delivery.dispatch_round_deliveries)
            assert rollback_entered.wait(10)
            second = workers.submit(delivery.dispatch_round_deliveries)
            assert second_connected.wait(10)
            # Third physical connection observes whether first retained its lock.
            with factory() as db:
                locked_delivery.extend(
                    db.query(models.RoundDelivery).filter_by(channel="in_app").with_for_update(skip_locked=True).all()
                )
                assert locked_delivery == [], "Failure recovery released its owning transaction/row lock"
            release_recovery.set()
            first.result(timeout=10)
            second.result(timeout=10)
    finally:
        release_recovery.set()
        event.remove(factory.class_, "after_soft_rollback", on_rollback)
        event.remove(engine, "before_cursor_execute", connection_seen)
    assert sends == [1]
    with factory() as db:
        row = db.query(models.RoundDelivery).filter_by(channel="in_app").one()
        assert row.attempts == 1 and row.status == "pending"
        deadline = row.lease_expires_at
        assert db.query(models.Notification).count() == 0
    # Both workers fail again on each due cycle, but only one may attempt per
    # committed backoff window. Durable attempts never regress or exceed five.
    for attempt in range(2, 6):
        make_due(factory)
        with ThreadPoolExecutor(2) as workers:
            list(workers.map(lambda _: delivery.dispatch_round_deliveries(), range(2)))
        with factory() as db:
            row = db.query(models.RoundDelivery).filter_by(channel="in_app").one()
            assert row.attempts == attempt
            assert row.lease_expires_at >= deadline
            deadline = row.lease_expires_at
    delivery.dispatch_round_deliveries()
    assert len(sends) == 5
    assert read(factory)["in_app"] == ("failed", 5)


@pytest.mark.parametrize("later_status", ["failed", "uncertain"])
def test_real_notifications_api_read_then_later_email_failure(harness, later_status):
    factory, transport = harness
    enqueue(factory)
    transport.is_configured.return_value = False
    delivery.dispatch_round_deliveries()
    app = FastAPI()
    app.include_router(notifications.router)
    identity = models.PlayerProfile(id=7)

    def db_session():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = db_session
    app.dependency_overrides[get_current_user] = lambda: identity
    url = "/notifications?unread_only=true&limit=10&types=round_conflict&include_delivery_health=true"
    with TestClient(app) as client:
        first = client.get(url).json()
        assert len(first) == 1
        notification_id = first[0]["id"]
        assert client.post(f"/notifications/{notification_id}/read").status_code == 200
        assert client.get(url).json() == []
        # Terminal email health transitions AFTER read, through actual dispatcher.
        if later_status == "failed":
            for _ in range(4):
                make_due(factory)
                delivery.dispatch_round_deliveries()
        else:
            transport.is_configured.return_value = True
            transport.send_round_conflict_notification.return_value = False
            make_due(factory)
            delivery.dispatch_round_deliveries()
        response = client.get(url)
        assert response.status_code == 200
        trouble = response.json()
        assert len(trouble) == 1
        assert trouble[0]["id"] == notification_id and trouble[0]["is_read"] is True
        assert trouble[0]["data"]["delivery_health"] == {"email": later_status}
        assert trouble[0]["data"]["path"].startswith("/")
        client.post("/notifications/read-all")
        assert client.get(url).json() == trouble
        assert client.get(url.replace("round_conflict", "match_found")).json() == []
        assert client.get(url.replace("include_delivery_health=true", "include_delivery_health=false")).json() == []
        delivery.dispatch_round_deliveries()
        assert client.get(url).json() == trouble
        with factory() as db:
            db.get(models.RoundIssue, "issue").status = "resolved"
            db.commit()
        assert client.get(url).json() == []
        identity.id = 8
        assert client.get(url).json() == []
        assert client.post(f"/notifications/{notification_id}/read").status_code == 404
    with factory() as db:
        assert db.query(models.Notification).count() == 1
        assert db.query(models.RoundDelivery).count() == 2
    if later_status == "failed":
        transport.send_round_conflict_notification.assert_not_called()
    else:
        transport.send_round_conflict_notification.assert_called_once()
