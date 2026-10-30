"""Actual queued worker rejects pre-pause work after a synthetic resume."""

from sqlalchemy.orm import Session

from app import models
from app.services.round_cutover import pause_writers
from tests.unit.services.test_round_sheet_delivery import delivery_engine, sheet_job_fixture


def test_queue_retains_paused_job_then_holds_stale_epoch_without_transport(sheet_job_fixture):
    engine, worker, rows, calls, job_id, *_ = sheet_job_fixture
    with Session(engine) as db:
        assert pause_writers(db, expected_epoch=2, reason="Synthetic queue drain") == 3
        db.commit()
    worker()
    with Session(engine) as db:
        job = db.get(models.PendingSheetSync, job_id)
        assert job.status == "pending" and job.expected_epoch == 2
        assert job.prewrite is None
        config = db.get(models.AppConfig, "round_identity")
        # Test configuration only; no operational Gate D approval is minted.
        config.value = {**config.value, "mode": "canonical", "epoch": 4}
        db.commit()
    worker()
    with Session(engine) as db:
        job = db.get(models.PendingSheetSync, job_id)
        assert job.status == "held" and job.expected_epoch == 2
        assert job.prewrite is None and job.provider_receipt is None
        assert job.game_id and job.operation_key == "operation-1"
    assert rows == []
    assert calls["append"] == calls["update"] == 0
