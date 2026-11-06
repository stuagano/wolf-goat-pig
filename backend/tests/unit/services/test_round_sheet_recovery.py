"""Crash, claim and token-update proofs using the same real queue fixture."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from sqlalchemy.orm import Session

from app import models
from app.services import spreadsheet_sync_service as sheet
from app.services.round_sheet_delivery import enqueue_sheet_sync, process_sheet_job
from app.services.round_source_lease import source_lease
from tests.unit.services.test_round_sheet_delivery import delivery_engine, sheet_job_fixture


class Crash(BaseException):
    pass


def expire(engine, job_id):
    with Session(engine) as db, db.begin():
        job = db.get(models.PendingSheetSync, job_id)
        job.lease_expires_at = "2000-01-01T00:00:00+00:00"


@pytest.mark.parametrize("point", ["before_write", "after_write", "before_done", "after_done"])
def test_crash_recovery_never_reappends(sheet_job_fixture, monkeypatch, point):
    from app.services import round_sheet_delivery as delivery

    engine, worker, rows, calls, job_id, *_ = sheet_job_fixture
    original_write, original_finish = sheet.write_identity_round, delivery._finish
    if point == "before_write":
        monkeypatch.setattr(sheet, "write_identity_round", lambda *a: (_ for _ in ()).throw(Crash()))
    elif point == "after_write":
        calls["after_write"] = lambda: (_ for _ in ()).throw(Crash())
    elif point == "before_done":
        monkeypatch.setattr(delivery, "_finish", lambda *a: (_ for _ in ()).throw(Crash()))
    if point == "after_done":
        worker()
    else:
        with pytest.raises(Crash):
            worker()
    monkeypatch.setattr(sheet, "write_identity_round", original_write)
    monkeypatch.setattr(delivery, "_finish", original_finish)
    calls.pop("after_write", None)
    expire(engine, job_id)
    worker()
    worker()
    assert calls["append"] == (0 if point == "before_write" else 1)
    with Session(engine) as db:
        job = db.get(models.PendingSheetSync, job_id)
        assert job.prewrite
        assert job.status == ("held" if point == "before_write" else "done")
        if rows:
            assert len(rows) == 2 and job.verified_readback


def test_timeout_unavailable_readback_is_held_not_retried(sheet_job_fixture):
    engine, worker, rows, calls, job_id, *_ = sheet_job_fixture
    calls["timeout"] = True
    calls["after_write"] = lambda: calls.update(unavailable=True)
    worker()
    calls["unavailable"] = False
    worker()
    assert len(rows) == 2 and calls["append"] == 1
    with Session(engine) as db:
        job = db.get(models.PendingSheetSync, job_id)
        assert job.status == "held" and job.prewrite and not job.verified_readback


def update_job(fixture):
    engine, worker, rows, calls, job_id, game_id, contract = fixture
    worker()
    with Session(engine) as db, db.begin():
        old = db.get(models.PendingSheetSync, job_id)
        job = enqueue_sheet_sync(
            db,
            game_id=game_id,
            source_scope=contract.scope,
            source_round_token="round-token",
            operation_key="operation-2",
            expected_revision=old.expected_revision,
            expected_epoch=2,
            expected_source_version=old.verified_readback["source_version"],
            action="update",
        )
        return job.id


@pytest.mark.parametrize("missing", [False, True])
def test_update_only_token_rows_never_append(sheet_job_fixture, missing):
    engine, _, rows, calls, *_ = sheet_job_fixture
    job_id = update_job(sheet_job_fixture)
    if missing:
        rows.clear()
    process_sheet_job(engine, job_id)
    assert calls["append"] == 1 and calls["update"] == (0 if missing else 1)
    with Session(engine) as db:
        job = db.get(models.PendingSheetSync, job_id)
        assert job.status == ("held" if missing else "done")
        if not missing:
            assert len(rows) == 2 and all(r[8] == "operation-2" for r in rows)
        else:
            assert db.query(models.RoundIssue).filter_by(kind="outbound_identity").count() == 1
            assert db.query(models.RoundObservation).filter_by(parse_status="held").count() == 1


def test_duplicate_worker_claim_cannot_write(sheet_job_fixture, monkeypatch):
    engine, worker, rows, calls, *_ = sheet_job_fixture
    entered, release = Event(), Event()
    original = sheet.fetch_round_snapshot
    first = True

    def read(*args, **kwargs):
        nonlocal first
        if first:
            first = False
            entered.set()
            assert release.wait(10)
        return original(*args, **kwargs)

    monkeypatch.setattr(sheet, "fetch_round_snapshot", read)
    with ThreadPoolExecutor(max_workers=2) as pool:
        running = pool.submit(worker)
        assert entered.wait(10)
        worker()
        assert calls["append"] == 0
        release.set()
        running.result(10)
    assert calls["append"] == 1 and len(rows) == 2


def test_inbound_outbound_share_scope_lease(sheet_job_fixture):
    engine, worker, rows, calls, job_id, _, contract = sheet_job_fixture
    with source_lease(engine, contract.scope):
        worker()
    assert not rows and calls["append"] == 0
    with Session(engine) as db:
        assert db.get(models.PendingSheetSync, job_id).status == "held"


def test_expired_claim_cannot_publish_or_write(sheet_job_fixture, monkeypatch):
    engine, worker, rows, calls, job_id, *_ = sheet_job_fixture
    original = sheet.fetch_round_snapshot

    def read(*args, **kwargs):
        snapshot = original(*args, **kwargs)
        expire(engine, job_id)
        return snapshot

    monkeypatch.setattr(sheet, "fetch_round_snapshot", read)
    worker()
    assert calls["append"] == 0 and not rows
    with Session(engine) as db:
        assert db.get(models.PendingSheetSync, job_id).status == "processing"


def test_expired_source_lease_fences_prewrite(sheet_job_fixture, monkeypatch):
    engine, worker, rows, calls, job_id, _, contract = sheet_job_fixture
    original = sheet.fetch_round_snapshot

    def read(*args, **kwargs):
        result = original(*args, **kwargs)
        with Session(engine) as db, db.begin():
            lease = db.get(models.RoundIdentityLease, "sheet:" + contract.scope)
            lease.expires_at = "2000-01-01T00:00:00+00:00"
        return result

    monkeypatch.setattr(sheet, "fetch_round_snapshot", read)
    worker()
    assert not rows and calls["append"] == 0
    with Session(engine) as db:
        assert db.get(models.PendingSheetSync, job_id).status == "held"


def test_actual_scheduler_drains_the_same_queue(sheet_job_fixture, monkeypatch):
    from app.services.email_scheduler import EmailScheduler

    engine, _, rows, calls, job_id, *_ = sheet_job_fixture
    scheduler = EmailScheduler()
    monkeypatch.setattr(scheduler, "_get_db", lambda: Session(engine))
    scheduler._process_pending_sheet_syncs()
    assert calls["append"] == 1 and len(rows) == 2
    with Session(engine) as db:
        assert db.get(models.PendingSheetSync, job_id).status == "done"


def test_unreviewed_changed_baseline_cannot_be_enqueued(sheet_job_fixture):
    engine, _, rows, _, _, game_id, contract = sheet_job_fixture
    update_job(sheet_job_fixture)
    rows[0][3] = 99
    changed = sheet.fetch_round_snapshot(contract.scope, season_year=2026, contract=contract)
    with Session(engine) as db:
        revision = db.query(models.GameStateModel).filter_by(game_id=game_id).one().revision
        with pytest.raises(ValueError, match="Reviewed source baseline"):
            enqueue_sheet_sync(
                db,
                game_id=game_id,
                source_scope=contract.scope,
                source_round_token="round-token",
                operation_key="operation-3",
                expected_revision=revision,
                expected_epoch=2,
                expected_source_version=changed.source_version,
                action="update",
            )
