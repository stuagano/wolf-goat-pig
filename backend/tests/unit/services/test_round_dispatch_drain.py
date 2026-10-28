"""A blocked fake transport must block pause acknowledgment, never send live."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

from app import models
from app.services import round_delivery as delivery
from app.services.round_cutover import pause_writers
from tests.unit.services.test_round_delivery import enqueue, harness


def test_pause_drains_durable_claim_external_effect_and_receipt(harness):
    factory, transport = harness
    with factory() as db:
        row = db.get(models.AppConfig, "round_identity")
        row.value = {**row.value, "mode": "canonical", "dispatch_paused": False}
        epoch = row.value.get("epoch", 0)
        db.commit()
    enqueue(factory)
    sending, release, pausing, paused = Event(), Event(), Event(), Event()

    def send(**kwargs):
        with factory() as db:
            assert db.query(models.RoundDelivery).filter_by(channel="email").one().status == "sending"
        sending.set()
        assert release.wait(5)
        return True

    transport.send_round_conflict_notification.side_effect = send

    def pause():
        with factory() as db:
            pausing.set()
            pause_writers(db, expected_epoch=epoch, reason="Fixture drain")
            db.commit()
            paused.set()

    with ThreadPoolExecutor(max_workers=2) as pool:
        worker = pool.submit(delivery.dispatch_round_deliveries)
        assert sending.wait(3)
        cutover = pool.submit(pause)
        assert pausing.wait(2)
        try:
            assert not paused.wait(0.2)
        finally:
            release.set()
        worker.result(timeout=5)
        cutover.result(timeout=5)
    with factory() as db:
        assert db.query(models.RoundDelivery).filter_by(channel="email").one().status == "accepted"
    delivery.dispatch_round_deliveries()
    transport.send_round_conflict_notification.assert_called_once()
