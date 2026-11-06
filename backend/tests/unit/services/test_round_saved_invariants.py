"""Reviewed saved publication must not infer unknown totals or certify extra holes."""

import json
from copy import deepcopy

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app import models
from app.services.canonical_round_reads import profile_statistics
from app.services.round_identity_migration import apply_manifest, seal_manifest, verify_manifest
from app.services.round_migration_accounting import current_inventory_digest, rows
from app.services.round_review import round_summary
from tests.unit.services.test_round_identity_migration import approve_deltas, approved, migration_fixture
from tests.unit.services.test_round_migration_cli import invoke
from tests.unit.services.test_round_saved_detail import detail_manifest


def reviewed(db, snapshot, pid, *, hold=False):
    manifest = approved(db, snapshot)
    decision = manifest["saved_games"][0]["decision"]
    decision["result_slots"] = {str(pid): "original-slot"}
    if hold:
        decision.update(
            action="hold", reason="Original nullable total must remain unknown; no score inference approved"
        )
    manifest["approval"]["expected_standings"] = (
        {} if hold else {"profile:1": {"score": 4.5, "scored": 1, "participation": 1}}
    )
    approve_deltas(manifest, {"Original": "profile:1", "Known": "guest:known-slot"})
    return seal_manifest(manifest)


def cli_apply(engine, tmp_path, manifest):
    path = tmp_path / "round3-reviewed.json"
    path.write_text(json.dumps(manifest))
    return invoke(
        engine, "apply", "--manifest", str(path), "--expect-checksum", manifest["checksum"], "--ack-paused-writers"
    )


@pytest.mark.parametrize("mixed", [False, True])
def test_unknown_original_total_requires_hold_before_commit(migration_fixture, tmp_path, mixed):
    engine, snapshot = migration_fixture
    with Session(engine) as db:
        _, rid, pid = detail_manifest(db, snapshot)
        original = db.get(models.GamePlayerResult, pid)
        original.total_earnings = None
        if mixed:
            db.add(
                models.GamePlayerResult(
                    game_record_id=rid,
                    participant_id="known-slot",
                    player_name="Known",
                    total_earnings=4.5,
                    hole_scores=deepcopy(original.hole_scores),
                )
            )
            db.get(models.GameRecord, rid).player_count = 2
        db.commit()
        before = {m: rows(db, m) for m in (models.GameRecord, models.GamePlayerResult, models.GameStateModel)}
        manifest = reviewed(db, snapshot, pid)
    for _ in range(2):
        result = cli_apply(engine, tmp_path, manifest)
        assert result.returncode == 2, "Unknown original total must refuse BEFORE a checkpoint commits"
        with Session(engine) as db:
            assert {m: rows(db, m) for m in before} == before
            assert db.query(models.RoundMigrationCheckpoint).count() == 0
    with Session(engine) as db:
        manifest = reviewed(db, snapshot, pid, hold=True)
    for _ in range(2):
        result = cli_apply(engine, tmp_path, manifest)
        assert result.returncode == 0, result.stderr
    with Session(engine) as db:
        assert {m: rows(db, m) for m in before} == before
        assert db.get(models.GamePlayerResult, pid).total_earnings is None
        assert not db.get(models.GameRecord, rid).score_eligible
        assert db.get(models.GameRecord, rid).accepted_revision == 0
        with pytest.raises(HTTPException) as exc:
            round_summary(db, "detail-orphan")
        assert exc.value.status_code == 404  # Held is unavailable, never a newly accepted score or fake zero.
        stats = profile_statistics(db, 1)[1]
        assert stats.scored_round_count == 0 and stats.holes_played is None
        assert stats.avg_earnings_per_hole is None
        assert verify_manifest(db, manifest)["errors"] == []
        db.get(models.GameRecord, rid).score_eligible = True
        db.flush()
        checkpoint = db.query(models.RoundMigrationCheckpoint).one()
        checkpoint.outcome = {**checkpoint.outcome, "inventory_digest": current_inventory_digest(db)}
        db.commit()
        assert verify_manifest(db, manifest)["errors"]
        with pytest.raises(ValueError):
            apply_manifest(db, manifest, expected_checksum=manifest["checksum"])


@pytest.mark.parametrize("partial", [False, True])
def test_demonstrable_richer_original_history_survives(migration_fixture, tmp_path, partial):
    engine, snapshot = migration_fixture
    with Session(engine) as db:
        _, rid, pid = detail_manifest(db, snapshot)
        count = 2 if partial else 18
        if partial:
            db.get(models.GameRecord, rid).detail_coverage = "partial"
            db.get(models.GameRecord, rid).total_holes_played = count
            db.get(models.GamePlayerResult, pid).hole_scores = db.get(models.GamePlayerResult, pid).hole_scores[:count]
        history = [
            {
                "hole": h,
                "points_delta": {"original-slot": 0.25},
                "gross_scores": {"original-slot": 4},
                "par": 4,
                "original_note": "Retained actual state",
                "carryover": 2,
            }
            for h in range(1, count + 1)
        ]
        db.add(models.GameStateModel(game_id="detail-orphan", state={"hole_history": history}))
        db.commit()
        manifest = reviewed(db, snapshot, pid)
    for _ in range(2):
        assert cli_apply(engine, tmp_path, manifest).returncode == 0
    with Session(engine) as db:
        assert db.query(models.GameStateModel).filter_by(game_id="detail-orphan").one().state["hole_history"] == history
        assert verify_manifest(db, manifest)["errors"] == []


@pytest.mark.parametrize("partial", [False, True])
@pytest.mark.parametrize(
    "tamper", ["added", "duplicate", "missing", "replaced", "malformed", "invented_field", "eligibility", "standings"]
)
def test_exact_original_history_and_projection_reject_resealed_tamper(migration_fixture, tmp_path, partial, tamper):
    engine, snapshot = migration_fixture
    with Session(engine) as db:
        _, rid, pid = detail_manifest(db, snapshot)
        if partial:
            record = db.get(models.GameRecord, rid)
            record.detail_coverage, record.total_holes_played = "partial", 2
            db.get(models.GamePlayerResult, pid).hole_scores = db.get(models.GamePlayerResult, pid).hole_scores[:2]
        db.commit()
        manifest = reviewed(db, snapshot, pid)
    for _ in range(2):
        result = cli_apply(engine, tmp_path, manifest)
        assert result.returncode == 0, result.stderr
    with Session(engine) as db:
        assert verify_manifest(db, manifest)["errors"] == []
        game = db.query(models.GameStateModel).filter_by(game_id="detail-orphan").one()
        state = deepcopy(game.state)
        history = state["hole_history"]
        if tamper == "added":
            history.append({**history[0], "hole": 3 if partial else 19})
        elif tamper == "duplicate":
            history.append(deepcopy(history[0]))
        elif tamper == "missing":
            history.pop()
        elif tamper == "replaced":
            history[-1]["hole"] = 3 if partial else 19
        elif tamper == "malformed":
            history[0]["hole"] = True
        elif tamper == "invented_field":
            history[0]["carryover"] = 77
        elif tamper == "eligibility":
            db.get(models.GameRecord, rid).score_eligible = False
        else:
            state["standings"]["original-slot"] = 999
        game.state = state
        flag_modified(game, "state")  # bool True == int 1 to Python, but not the JSON evidence contract.
        db.flush()
        checkpoint = db.query(models.RoundMigrationCheckpoint).one()
        checkpoint.outcome = {**checkpoint.outcome, "inventory_digest": current_inventory_digest(db)}
        db.commit()
        assert verify_manifest(db, manifest)["errors"], "Resealed digest cannot certify invented accepted projection"
        with pytest.raises(ValueError):
            apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
    assert cli_apply(engine, tmp_path, manifest).returncode == 2
