"""Real queue/connector/inbound integration with synthetic Gate B only."""

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from app import models
from app.schemas.round_identity import RoundDraft
from app.services import spreadsheet_sync_service as sheet
from app.services.completed_game_service import persist_final_results
from app.services.round_evidence import fingerprint
from app.services.round_sheet_contract import SheetWriteContract


@pytest.fixture(params=["sqlite", "postgresql"])
def delivery_engine(request, tmp_path):
    admin = None
    if request.param == "sqlite":
        engine = create_engine(f"sqlite:///{tmp_path}/delivery.db")
    else:
        raw = os.environ.get("ROUND_IDENTITY_TEST_DATABASE_URL")
        if not raw:
            pytest.skip("Requires disposable local PostgreSQL")
        url = make_url(raw)
        assert url.host in {"localhost", "127.0.0.1", "::1"} and url.database.endswith("_test")
        schema = "sheet_delivery_" + uuid4().hex
        admin = create_engine(url.set(drivername="postgresql+psycopg2"), poolclass=NullPool)
        with admin.begin() as tx:
            tx.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(
            url.set(drivername="postgresql+psycopg2"),
            poolclass=NullPool,
            connect_args={"options": f"-csearch_path={schema} -cstatement_timeout=10000"},
        )
    models.Base.metadata.create_all(engine)
    yield engine
    engine.dispose()
    if admin:
        with admin.begin() as tx:
            tx.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


@pytest.fixture
def sheet_job_fixture(delivery_engine, monkeypatch):
    from app.services.round_sheet_delivery import enqueue_sheet_sync, process_sheet_job

    engine = delivery_engine
    scope = "synthetic:42:2026"
    contract = SheetWriteContract(
        scope=scope,
        tab_title="Details",
        season=2026,
        layout_version="synthetic-v1",
        round_column=7,
        participant_column=8,
        operation_column=9,
        full_history_evidence="synthetic restored full grid",
        whole_row_sorting_evidence="synthetic whole row",
        protection_evidence="synthetic protected IDs",
    )
    entry = {
        "contract": contract.model_dump(),
        "approval": {
            "enabled": True,
            "contract_fingerprint": fingerprint(contract.model_dump()),
            "reference": "TEST ONLY",
            "actor_profile_id": 1,
            "approved_at": "2026-10-27T00:00:00+00:00",
            "allowed_operations": ["insert", "update"],
        },
    }
    rows = []
    calls = {"append": 0, "update": 0, "timeout": False, "unavailable": False}
    monkeypatch.setattr(
        sheet,
        "_sheets_metadata_get",
        lambda *_: {
            "sheets": [
                {
                    "properties": {
                        "sheetId": 42,
                        "title": "Details",
                        "gridProperties": {"rowCount": 100, "columnCount": 9},
                    }
                }
            ]
        },
    )

    def get(_, range_, **_kwargs):
        if calls["unavailable"]:
            return None
        return {"range": range_, "majorDimension": "ROWS", "values": [list(r) for r in rows]}

    def write(_, range_, values, *, updates=None):
        if updates is None:
            calls["append"] += 1
            rows.extend([list(r) for r in values])
        else:
            calls["update"] += 1
            for index, row, _old in updates:
                rows[index - 2] = list(row)
        if calls.get("after_write"):
            calls["after_write"]()
        if calls["timeout"]:
            raise TimeoutError("accepted then lost response")
        return {"spreadsheetId": "synthetic", "updatedRows": len(values)}

    monkeypatch.setattr(sheet, "_sheets_api_get", get)
    monkeypatch.setattr(sheet, "_sheets_identity_write", write)
    with Session(engine) as db:
        db.add(models.AppConfig(name="round_identity", value={"mode": "canonical", "epoch": 2, "season": 2026}))
        db.add(models.AppConfig(name="round_sheet_contracts", value={scope: entry}))
        game = models.GameStateModel(game_id=str(uuid4()), state={}, game_status="completed")
        db.add(game)
        db.flush()
        draft = RoundDraft(
            played_on="2026-10-01",
            raw_date="2026-10-01",
            course_name="Synthetic Course",
            group="A",
            roster_complete=True,
            players=[
                {"participant_id": "slot-a", "name": "Guest", "quarters": 1.5},
                {"participant_id": "slot-b", "name": "Guest", "quarters": -1.5},
            ],
        )
        persist_final_results(db, game, draft)
        db.commit()
        baseline = sheet.fetch_round_snapshot(scope, season_year=2026, contract=contract)
        job = enqueue_sheet_sync(
            db,
            game_id=game.game_id,
            source_scope=scope,
            source_round_token="round-token",
            operation_key="operation-1",
            expected_revision=game.revision,
            expected_epoch=2,
            expected_source_version=baseline.source_version,
            action="insert",
        )
        db.commit()
        job_id, game_id = job.id, game.game_id
    return engine, lambda: process_sheet_job(engine, job_id), rows, calls, job_id, game_id, contract


def test_accepted_then_timeout_is_not_appended_twice(sheet_job_fixture):
    engine, worker, rows, calls, job_id, *_ = sheet_job_fixture
    calls["timeout"] = True
    worker()
    worker()
    assert len(rows) == 2 and calls["append"] == 1
    with Session(engine) as db:
        job = db.get(models.PendingSheetSync, job_id)
        assert job.status == "done" and job.verified_readback and job.provider_receipt


def test_actual_inbound_echo_same_uuid_without_conflict(sheet_job_fixture):
    from app.services.round_identity import sync_round_snapshot

    engine, worker, rows, calls, job_id, game_id, contract = sheet_job_fixture
    worker()
    snapshot = sheet.fetch_round_snapshot(contract.scope, season_year=2026, contract=contract)
    with Session(engine) as db:
        outcomes = sync_round_snapshot(db, snapshot)
        assert all(o.game_id == game_id and o.status == "unchanged" for o in outcomes)
        assert db.query(models.GameStateModel).count() == 1
        assert db.query(models.RoundIssue).count() == 0
        assert db.query(models.GamePlayerResult).count() == 2


@pytest.mark.parametrize(
    "fault", ["missing_approval", "stale_approval", "paused", "epoch", "revision", "source_changed"]
)
def test_prewrite_guards_no_side_effect(sheet_job_fixture, fault):
    engine, worker, rows, calls, job_id, game_id, contract = sheet_job_fixture
    with Session(engine) as db:
        if fault.endswith("approval"):
            row = db.get(models.AppConfig, "round_sheet_contracts")
            entry = row.value[contract.scope]
            if fault == "missing_approval":
                row.value = {}
            else:
                row.value = {
                    contract.scope: {**entry, "approval": {**entry["approval"], "contract_fingerprint": "stale"}}
                }
        elif fault in {"paused", "epoch"}:
            row = db.get(models.AppConfig, "round_identity")
            row.value = {**row.value, **({"mode": "paused"} if fault == "paused" else {"epoch": 3})}
        elif fault == "revision":
            db.query(models.GameStateModel).filter_by(game_id=game_id).one().revision += 1
        else:
            rows.append(["external", "A", "External", 0, "", "", "other", "other-slot", ""])
        db.commit()
    worker()
    assert calls["append"] == calls["update"] == 0
    with Session(engine) as db:
        assert db.get(models.PendingSheetSync, job_id).status == "held"


def test_historical_unbound_is_held_without_guess(sheet_job_fixture):
    from app.services.round_sheet_delivery import process_sheet_job

    engine, _, rows, calls, *_ = sheet_job_fixture
    with Session(engine) as db:
        job = models.PendingSheetSync(date="2026-10-01", group="A", player_scores={"Guest": 0}, status="pending")
        db.add(job)
        db.commit()
        job_id = job.id
    process_sheet_job(engine, job_id)
    assert not rows and calls["append"] == 0
    with Session(engine) as db:
        assert db.get(models.PendingSheetSync, job_id).status == "held"
        assert "manifest" in db.get(models.PendingSheetSync, job_id).error
