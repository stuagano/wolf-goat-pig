"""Behavioral review regressions through real worker, parser and inbound sync."""

from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app import models
from app.schemas.round_identity import RoundDraft
from app.services import spreadsheet_sync_service as sheet
from app.services.completed_game_service import persist_final_results
from app.services.round_evidence import accepted_draft, fingerprint
from app.services.round_identity import sync_round_snapshot
from app.services.round_sheet_delivery import enqueue_sheet_sync, process_sheet_job
from tests.unit.services.test_round_sheet_delivery import delivery_engine, sheet_job_fixture


def enqueue(engine, contract, game_id, operation, action="update", token=None):
    token = token or "round-token"
    snapshot = sheet.fetch_round_snapshot(contract.scope, season_year=2026, contract=contract)
    with Session(engine) as db, db.begin():
        game = db.query(models.GameStateModel).filter_by(game_id=game_id).one()
        job = enqueue_sheet_sync(
            db,
            game_id=game_id,
            source_scope=contract.scope,
            source_round_token=token,
            operation_key=operation,
            expected_revision=game.revision,
            expected_epoch=2,
            expected_source_version=snapshot.source_version,
            action=action,
        )
        return job.id


def refresh(engine, contract):
    snapshot = sheet.fetch_round_snapshot(contract.scope, season_year=2026, contract=contract)
    with Session(engine) as db:
        return sync_round_snapshot(db, snapshot)


@pytest.mark.parametrize("timeout", [False, True])
def test_provider_integer_readback_and_recovery(sheet_job_fixture, timeout, monkeypatch):
    engine, worker, rows, calls, job_id, game_id, contract = sheet_job_fixture
    with Session(engine) as db, db.begin():
        game = db.query(models.GameStateModel).filter_by(game_id=game_id).one()
        draft = accepted_draft(db, game_id)
        draft.players[0].quarters, draft.players[1].quarters = 1.0, -1.0
        persist_final_results(db, game, draft)
        db.get(models.PendingSheetSync, job_id).status = "held"
    job_id = enqueue(engine, contract, game_id, "integer-write", "insert")
    calls["timeout"] = timeout

    def normalize():
        for row in rows:
            if isinstance(row[3], float) and row[3].is_integer():
                row[3] = int(row[3])

    calls["after_write"] = normalize
    if timeout:
        from app.services import round_sheet_delivery as delivery
        from tests.unit.services.test_round_sheet_recovery import Crash, expire

        original = delivery._finish
        monkeypatch.setattr(delivery, "_finish", lambda *a: (_ for _ in ()).throw(Crash()))
        with pytest.raises(Crash):
            process_sheet_job(engine, job_id)
        monkeypatch.setattr(delivery, "_finish", original)
        expire(engine, job_id)
    process_sheet_job(engine, job_id)
    process_sheet_job(engine, job_id)
    with Session(engine) as db:
        assert db.get(models.PendingSheetSync, job_id).status == "done"
        assert db.get(models.PendingSheetSync, job_id).verified_readback
    assert calls["append"] == 1
    outcomes = refresh(engine, contract)
    with Session(engine) as db:
        assert all(o.game_id == game_id and o.status == "unchanged" for o in outcomes), [
            (i.kind, i.field, i.proposed_value) for i in db.query(models.RoundIssue)
        ]


def test_two_game_local_rosters_export_and_echo_distinctly(sheet_job_fixture):
    engine, _, rows, calls, first_job, first_id, contract = sheet_job_fixture
    with Session(engine) as db, db.begin():
        db.get(models.PendingSheetSync, first_job).status = "held"
        db.query(models.RoundSource).filter_by(game_id=first_id).delete()
        first = db.query(models.GameStateModel).filter_by(game_id=first_id).one()
        # Rebuild this synthetic accepted roster as the real app's p1/p2 shape.
        record = db.query(models.GameRecord).filter_by(game_id=first_id).one()
        for result, slot in zip(
            db.query(models.GamePlayerResult).filter_by(game_record_id=record.id).order_by(models.GamePlayerResult.id),
            ["p1", "p2"],
            strict=True,
        ):
            result.participant_id = slot
        second = models.GameStateModel(game_id=str(uuid4()), state={}, game_status="completed")
        db.add(second)
        db.flush()
        draft = accepted_draft(db, first_id)
        persist_final_results(db, second, draft)
        second_id = second.game_id
    for game_id, token in [(first_id, "round-token"), (second_id, "second-round")]:
        job_id = enqueue(engine, contract, game_id, "insert-" + token, "insert", token)
        process_sheet_job(engine, job_id)
        with Session(engine) as db:
            assert db.get(models.PendingSheetSync, job_id).status == "done"
    tokens = {r[7] for r in rows}
    assert len(tokens) == 4
    outcomes = refresh(engine, contract)
    assert {o.game_id for o in outcomes} == {first_id, second_id}
    assert all(o.status == "unchanged" for o in outcomes)
    before = {
        r[6]: set(r[7] for r in rows if r[6] == token)
        for token in ("round-token", "second-round")
        for r in rows
        if r[6] == token
    }
    for game_id, token in [(first_id, "round-token"), (second_id, "second-round")]:
        job_id = enqueue(engine, contract, game_id, "update-" + token, token=token)
        assert enqueue(engine, contract, game_id, "update-" + token, token=token) == job_id
        calls["timeout"] = True
        process_sheet_job(engine, job_id)
        process_sheet_job(engine, job_id)
        with Session(engine) as db:
            assert db.get(models.PendingSheetSync, job_id).status == "done"
        assert {r[7] for r in rows if r[6] == token} == before[token]
        refresh(engine, contract)
    with Session(engine) as db:
        assert {r.participant_id for r in db.query(models.GamePlayerResult)} == {"p1", "p2"}
        assert db.query(models.RoundIssue).count() == 0


def test_missing_outbound_token_then_repeated_real_refresh(sheet_job_fixture):
    engine, worker, rows, _, _, game_id, contract = sheet_job_fixture
    worker()
    refresh(engine, contract)
    job_id = enqueue(engine, contract, game_id, "missing-update")
    rows[:] = [["2026-10-01", "B", "Other Guest", 0, "Course", "", "other-round", "other-slot", "other-operation"]]
    process_sheet_job(engine, job_id)
    for _ in range(2):
        assert all(o.status == "held" for o in refresh(engine, contract))
    with Session(engine) as db:
        issues = db.query(models.RoundIssue).count()
        assert any(
            o.parse_status == "held" and o.raw_payload.get("source_rows") == rows
            for o in db.query(models.RoundObservation)
        )
        assert sorted(r.total_earnings for r in db.query(models.GamePlayerResult)) == [-1.5, 1.5]
    refresh(engine, contract)
    with Session(engine) as db:
        assert db.query(models.RoundIssue).count() == issues


def test_existing_trusted_source_tokens_are_preserved(sheet_job_fixture):
    engine, _, rows, calls, initial, game_id, contract = sheet_job_fixture
    rows[:] = [
        ["1-Oct", "A", "Guest", score, "Synthetic Course", "", "round-token", slot, "historical"]
        for slot, score in [("slot-a", 1.5), ("slot-b", -1.5)]
    ]
    snapshot = sheet.fetch_round_snapshot(contract.scope, season_year=2026, contract=contract)
    with Session(engine) as db, db.begin():
        db.get(models.PendingSheetSync, initial).status = "held"
        source = db.query(models.RoundSource).filter_by(game_id=game_id).one()
        source.binding_evidence = {"reviewed": "synthetic historical mapping"}
        db.add(
            models.RoundObservation(
                source_id=source.id,
                observation_key="trusted-history",
                continuity_verified=True,
                parsed_values=snapshot.rounds[0].draft.model_dump(mode="json"),
                raw_payload={"payload": {"source_version": snapshot.source_version}},
            )
        )
        game = db.query(models.GameStateModel).filter_by(game_id=game_id).one()
        draft = accepted_draft(db, game_id)
        draft.raw_date = "1-Oct"
        persist_final_results(db, game, draft)
    job_id = enqueue(engine, contract, game_id, "trusted-update")
    process_sheet_job(engine, job_id)
    assert {r[7] for r in rows} == {"slot-a", "slot-b"}
    assert calls["append"] == 0 and calls["update"] == 1
    assert all(o.status == "unchanged" and o.game_id == game_id for o in refresh(engine, contract))
    with Session(engine) as db:
        assert db.get(models.PendingSheetSync, job_id).status == "done"
        assert db.query(models.RoundSource).filter_by(game_id=game_id).one().binding_evidence["participant_tokens"] == {
            "slot-a": "slot-a",
            "slot-b": "slot-b",
        }


def test_numeric_canonicalization_is_narrow():
    from app.services.round_sheet_values import cell_fingerprint

    assert cell_fingerprint([[1.0, 0.0, -1.0]]) == cell_fingerprint([[1, 0, -1]])
    assert len({cell_fingerprint([[v]]) for v in [None, "", 0, 0.5, "0", False]}) == 6
    assert cell_fingerprint([["token", "op", 1]]) != cell_fingerprint([["other-token", "op", 1]])
    assert cell_fingerprint([["token", "op", 1]]) != cell_fingerprint([["token", "other-op", 1]])
    for value in [float("nan"), float("inf"), float("-inf")]:
        with pytest.raises(ValueError, match="Nonfinite"):
            cell_fingerprint([[value]])


@pytest.mark.parametrize("date_change", [False, True])
def test_historical_raw_date_correction_roundtrip(sheet_job_fixture, date_change):
    engine, _, rows, _, initial, game_id, contract = sheet_job_fixture
    with Session(engine) as db, db.begin():
        db.get(models.PendingSheetSync, initial).status = "held"
        game = db.query(models.GameStateModel).filter_by(game_id=game_id).one()
        draft = accepted_draft(db, game_id)
        draft.raw_date = "1-Oct"
        persist_final_results(db, game, draft)
    first = enqueue(engine, contract, game_id, "historical-insert", "insert")
    process_sheet_job(engine, first)
    # Actual trusted historical input uses yearless source text.
    assert {r[0] for r in rows} == {"1-Oct"}
    assert all(o.status == "unchanged" for o in refresh(engine, contract))
    with Session(engine) as db, db.begin():
        game = db.query(models.GameStateModel).filter_by(game_id=game_id).one()
        draft = accepted_draft(db, game_id)
        draft.players[0].quarters, draft.players[1].quarters = 2.5, -2.5
        if date_change:
            draft.played_on = RoundDraft(played_on="2026-10-02").played_on
            draft.raw_date = "2-Oct"
        persist_final_results(db, game, draft)
    job_id = enqueue(engine, contract, game_id, "historical-update")
    process_sheet_job(engine, job_id)
    assert {r[0] for r in rows} == ({"2-Oct"} if date_change else {"1-Oct"})
    assert all(o.status == "unchanged" and o.game_id == game_id for o in refresh(engine, contract))
    with Session(engine) as db:
        assert db.query(models.RoundIssue).count() == 0
        assert accepted_draft(db, game_id).raw_date == ("2-Oct" if date_change else "1-Oct")
