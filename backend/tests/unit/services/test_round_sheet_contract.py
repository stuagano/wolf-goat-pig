"""No production defaults and exact immutable synthetic approval matching."""

import pytest
from sqlalchemy.orm import Session

from app import models
from app.services import spreadsheet_sync_service as sheet
from app.services.round_evidence import fingerprint
from app.services.round_sheet_contract import SheetWriteContract, approved_contract
from app.services.round_sheet_delivery import enqueue_sheet_sync
from tests.unit.services.test_round_sheet_delivery import delivery_engine, sheet_job_fixture


@pytest.mark.parametrize(
    "field,value",
    [("round_column", 6), ("participant_column", 7), ("scope", "synthetic:42:2025"), ("protection_evidence", "")],
)
def test_layout_fails_closed(sheet_job_fixture, field, value):
    *_, contract = sheet_job_fixture
    with pytest.raises(ValueError):
        SheetWriteContract.model_validate({**contract.model_dump(), field: value})


def test_no_default_production_positions_or_approval(sheet_job_fixture):
    engine, _, _, _, _, _, contract = sheet_job_fixture
    with pytest.raises(ValueError):
        SheetWriteContract.model_validate({"scope": "production:42:2026", "season": 2026})
    with Session(engine) as db:
        assert approved_contract(db, "production:42:2026") is None


def test_idempotent_enqueue_and_changed_payload_rejected(sheet_job_fixture):
    engine, _, _, _, job_id, game_id, contract = sheet_job_fixture
    with Session(engine) as db:
        old = db.get(models.PendingSheetSync, job_id)
        arguments = {
            "game_id": game_id,
            "source_scope": contract.scope,
            "source_round_token": "round-token",
            "operation_key": "operation-1",
            "expected_revision": old.expected_revision,
            "expected_epoch": 2,
            "expected_source_version": old.expected_source_version,
            "action": "insert",
        }
        assert enqueue_sheet_sync(db, **arguments).id == job_id
        with pytest.raises(ValueError, match="reused"):
            enqueue_sheet_sync(db, **{**arguments, "source_round_token": "other-token"})
        assert db.query(models.PendingSheetSync).count() == 1


@pytest.mark.parametrize("mutation", ["payload", "approval", "contract", "binding"])
def test_queue_cannot_outlive_its_exact_contract_or_payload(sheet_job_fixture, mutation):
    engine, worker, rows, calls, job_id, _, contract = sheet_job_fixture
    with Session(engine) as db, db.begin():
        if mutation == "payload":
            job = db.get(models.PendingSheetSync, job_id)
            job.payload = {**job.payload, "course_name": "Tampered"}
        elif mutation == "binding":
            db.query(models.RoundSource).one().game_id = "other-uuid"
        else:
            row = db.get(models.AppConfig, "round_sheet_contracts")
            entry = row.value[contract.scope]
            if mutation == "contract":
                entry = {**entry, "contract": {**entry["contract"], "layout_version": "new-version"}}
                entry["approval"] = {**entry["approval"], "contract_fingerprint": fingerprint(entry["contract"])}
            else:
                entry = {**entry, "approval": {**entry["approval"], "reference": "different approval"}}
            row.value = {contract.scope: entry}
    worker()
    assert not rows and calls["append"] == 0
    with Session(engine) as db:
        assert db.get(models.PendingSheetSync, job_id).status == "held"


def test_matching_marker_with_changed_payload_is_not_acceptance(sheet_job_fixture):
    engine, worker, rows, calls, job_id, *_ = sheet_job_fixture
    calls["after_write"] = lambda: rows[0].__setitem__(3, 777)
    worker()
    worker()
    assert calls["append"] == 1
    with Session(engine) as db:
        job = db.get(models.PendingSheetSync, job_id)
        assert job.status == "held" and not job.verified_readback


def test_external_change_after_echo_held_with_raw_evidence(sheet_job_fixture):
    from app.services.round_identity import sync_round_snapshot

    engine, worker, rows, _, _, game_id, contract = sheet_job_fixture
    worker()
    rows[0][3] = 777
    changed = sheet.fetch_round_snapshot(contract.scope, season_year=2026, contract=contract)
    with Session(engine) as db:
        outcomes = sync_round_snapshot(db, changed)
        assert outcomes[0].status == "held" and outcomes[0].game_id == game_id
        assert db.query(models.RoundIssue).count() > 0
        observations = db.query(models.RoundObservation).all()
        assert any(777 in row for o in observations for row in o.raw_payload.get("payload", {}).get("rows", []))
        totals = sorted(r.total_earnings for r in db.query(models.GamePlayerResult))
        assert totals == [-1.5, 1.5]
