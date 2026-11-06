"""Orphan repair must preserve original detail, not only quarter totals."""

import json
from copy import deepcopy
from datetime import date

import pytest
from sqlalchemy.orm import Session

from app import models
from app.services.canonical_round_reads import profile_statistics
from app.services.round_identity_migration import apply_manifest, seal_manifest, verify_manifest
from app.services.round_review import round_summary
from tests.unit.services.test_round_identity_migration import approve_deltas, approved, migration_fixture
from tests.unit.services.test_round_migration_cli import invoke


def detail_manifest(db, snapshot):
    snapshot.rounds = []
    record = models.GameRecord(
        game_id="detail-orphan",
        played_on=date(2026, 9, 2),
        completed_at="2026-09-02T12:00:00",
        player_count=1,
        roster_complete=True,
        accepted_revision=0,
        detail_coverage="per_hole_complete",
        total_holes_played=18,
        game_settings={"original_note": "Retain audit", "played_at": "2026-09-02T10:30:00"},
    )
    db.add(record)
    db.flush()
    holes = [
        {"hole": h, "quarters": 0.25, "gross_score": 4, "par": 4, "original_note": f"Original {h}"}
        for h in range(1, 19)
    ]
    result = models.GamePlayerResult(
        game_record_id=record.id,
        participant_id=None,
        player_name="Original",
        player_profile_id=1,
        total_earnings=4.5,
        hole_scores=holes,
        holes_won=18,
        performance_metrics={"retained": "notes"},
    )
    db.add(result)
    db.commit()
    manifest = approved(db, snapshot)
    manifest["saved_games"][0]["decision"]["result_slots"] = {str(result.id): "original-slot"}
    manifest["approval"]["expected_standings"] = {"profile:1": {"score": 4.5, "scored": 1, "participation": 1}}
    approve_deltas(manifest, {"Original": "profile:1"})
    return seal_manifest(manifest), record.id, result.id


def prove_detail(engine, snapshot, tmp_path):
    with Session(engine) as db:
        manifest, rid, pid = detail_manifest(db, snapshot)
        original = deepcopy(db.get(models.GamePlayerResult, pid).hole_scores)
        metadata = deepcopy(db.get(models.GameRecord, rid).game_settings)
    path = tmp_path / "detail-manifest.json"
    path.write_text(json.dumps(manifest))
    for _ in range(2):
        result = invoke(
            engine, "apply", "--manifest", str(path), "--expect-checksum", manifest["checksum"], "--ack-paused-writers"
        )
        assert result.returncode == 0, result.stderr
    with Session(engine) as db:
        record, row = db.get(models.GameRecord, rid), db.get(models.GamePlayerResult, pid)
        assert record.detail_coverage == "per_hole_complete"
        assert record.total_holes_played == 18
        assert row.hole_scores == original and row.performance_metrics == {"retained": "notes"}
        assert record.game_settings == metadata
        summary = round_summary(db, "detail-orphan")
        assert len(summary["hole_history"]) == 18
        assert summary["hole_history"][0] == {
            "hole": 1,
            "points_delta": {"original-slot": 0.25},
            "gross_scores": {"original-slot": 4},
            "par": 4,
        }
        assert summary["capabilities"]["complete_detail"] and summary["detail_reconciled"]
        stats = profile_statistics(db, 1)[1]
        assert stats.holes_played == 18 and stats.avg_earnings_per_hole == 0.25
        assert verify_manifest(db, manifest)["errors"] == []
    return manifest, rid, pid


def test_orphan_original_detail_apply_cli_resume_summary_and_statistics(migration_fixture, tmp_path):
    engine, snapshot = migration_fixture
    prove_detail(engine, snapshot, tmp_path)


@pytest.mark.parametrize("broken", ["missing", "conflict", "retracted"])
def test_insufficient_detail_requires_explicit_hold(migration_fixture, broken):
    engine, snapshot = migration_fixture
    with Session(engine) as db:
        manifest, rid, pid = detail_manifest(db, snapshot)
        row = db.get(models.GamePlayerResult, pid)
        holes = deepcopy(row.hole_scores)
        if broken == "missing":
            holes.pop()
        elif broken == "retracted":
            row.is_retracted = True
        else:
            holes[0]["points_delta"] = {"unproven-slot": 99}
        row.hole_scores = holes
        db.commit()
        manifest = approved(db, snapshot)
        manifest["saved_games"][0]["decision"]["result_slots"] = {str(pid): "original-slot"}
        manifest["approval"]["expected_standings"] = {"profile:1": {"score": 4.5, "scored": 1, "participation": 1}}
        approve_deltas(manifest, {"Original": "profile:1"})
        manifest = seal_manifest(manifest)
        with pytest.raises(ValueError, match=r"detail.*hold"):
            apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        assert not db.query(models.GameStateModel).filter_by(game_id="detail-orphan").count()
        manifest["saved_games"][0]["decision"].update(
            action="hold", reason="Original detail cannot be reconstructed honestly"
        )
        manifest["approval"]["expected_standings"] = {}
        approve_deltas(manifest, {"Original": "profile:1"})
        manifest = seal_manifest(manifest)
        apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        assert verify_manifest(db, manifest)["errors"] == []
        assert db.get(models.GameRecord, rid).total_holes_played == 18
        assert db.get(models.GamePlayerResult, pid).hole_scores == holes


@pytest.mark.parametrize("tamper", ["all", "state", "metadata", "notes", "slots"])
def test_verifier_and_replay_reject_detail_loss_even_resealed_checkpoint(migration_fixture, tmp_path, tamper):
    from app.services.round_migration_accounting import current_inventory_digest

    engine, snapshot = migration_fixture
    manifest, rid, pid = prove_detail(engine, snapshot, tmp_path)
    with Session(engine) as db:
        if tamper in {"all", "metadata"}:
            db.get(models.GameRecord, rid).total_holes_played = None
        if tamper in {"all", "notes"}:
            db.get(models.GamePlayerResult, pid).hole_scores = []
        if tamper in {"all", "state"}:
            db.query(models.GameStateModel).filter_by(game_id="detail-orphan").one().state = {}
        if tamper == "slots":
            db.get(models.GamePlayerResult, pid).participant_id = "unreviewed-slot"
        db.flush()
        checkpoint = db.query(models.RoundMigrationCheckpoint).one()
        checkpoint.outcome = {**checkpoint.outcome, "inventory_digest": current_inventory_digest(db)}
        db.commit()
        assert any("detail" in error for error in verify_manifest(db, manifest)["errors"])
        with pytest.raises(ValueError, match="detail"):
            apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
