"""Actual CLI publication must verify retained retractions, not resurrect history."""

import json
from copy import deepcopy
from datetime import date

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app import models
from app.services.canonical_round_reads import profile_statistics
from app.services.round_identity_migration import seal_manifest, verify_manifest
from app.services.round_migration_accounting import current_inventory_digest, rows
from app.services.round_review import round_summary
from tests.unit.services.test_round_identity_migration import approve_deltas, approved, migration_fixture
from tests.unit.services.test_round_migration_cli import invoke
from tests.unit.services.test_round_saved_detail import detail_manifest


def seed_review(db, snapshot, kind):
    _, rid, pid = detail_manifest(db, snapshot)
    record = db.get(models.GameRecord, rid)
    original = db.get(models.GamePlayerResult, pid)
    original.participant_id = "original-slot"
    if kind == "whole":
        record.is_retracted = True
    else:
        record.detail_coverage, record.total_holes_played = "totals_only", None
        original.hole_scores = []
        db.add(
            models.GamePlayerResult(
                game_record_id=rid,
                participant_id="retired-slot",
                player_name="Historical",
                total_earnings=8.25,
                is_retracted=True,
                performance_metrics={"note": "Retain retired evidence"},
            )
        )
        record.player_count = 2
        if kind == "all":
            original.is_retracted = True
    # A second item forces _drift to verify the first committed checkpoint before
    # continuing; it must not be stranded by valid original retractions.
    next_record = models.GameRecord(
        game_id="next-saved", played_on=date(2026, 9, 3), roster_complete=True, player_count=1
    )
    db.add(next_record)
    db.flush()
    db.add(
        models.GamePlayerResult(
            game_record_id=next_record.id, participant_id="next-slot", player_name="Next", total_earnings=1.25
        )
    )
    db.commit()
    manifest = approved(db, snapshot)
    if kind == "incomplete":
        manifest["saved_games"][0]["decision"]["roster_complete"] = False
    expected = {"guest:next-slot": {"score": 1.25, "scored": 1, "participation": 1}}
    if kind in {"participant", "incomplete"}:
        expected["profile:1"] = {
            "score": 4.5 if kind == "participant" else 0.0,
            "scored": int(kind == "participant"),
            "participation": 1,
        }
    manifest["approval"]["expected_standings"] = expected
    approve_deltas(manifest, {"Original": "profile:1", "Historical": "guest:retired-slot", "Next": "guest:next-slot"})
    return seal_manifest(manifest), rid, pid


def cli(engine, tmp_path, manifest, action):
    path = tmp_path / "retractions.json"
    path.write_text(json.dumps(manifest))
    args = ["--manifest", str(path)]
    if action == "apply":
        args += ["--expect-checksum", manifest["checksum"], "--ack-paused-writers"]
    return invoke(engine, action, *args)


@pytest.mark.parametrize("kind", ["whole", "participant", "all", "incomplete"])
def test_retained_retractions_cli_verify_replay_and_continue(migration_fixture, tmp_path, kind):
    engine, snapshot = migration_fixture
    with Session(engine) as db:
        manifest, rid, pid = seed_review(db, snapshot, kind)
        originals = rows(db, models.GamePlayerResult)
    # First apply, CLI verify, and two same-manifest replays, each a new process.
    for action in ("apply", "verify", "apply", "verify", "apply"):
        result = cli(engine, tmp_path, manifest, action)
        assert result.returncode == 0, (action, result.stderr, result.stdout)
    with Session(engine) as db:
        record = db.get(models.GameRecord, rid)
        state = db.query(models.GameStateModel).filter_by(game_id="detail-orphan").one().state
        active = {} if kind == "all" else {"original-slot": 4.5}
        assert record.is_retracted == (kind == "whole")
        assert record.score_eligible == (kind == "participant")
        assert record.player_count == len(active)
        assert record.final_scores == state["standings"] == active
        assert {p["id"]: p["total_points"] for p in state["players"]} == active
        assert rows(db, models.GamePlayerResult) == originals  # IDs, totals, notes and flags all retained.
        summary = round_summary(db, "detail-orphan")
        assert summary["is_retracted"] == (kind == "whole")
        assert summary["score_eligible"] == (kind == "participant")
        assert len(summary["hole_history"]) == (18 if kind == "whole" else 0)
        assert summary["players"][0]["quarters"] == 4.5
        if kind != "whole":
            retired = next(p for p in summary["players"] if p["participant_id"] == "retired-slot")
            assert retired["is_retracted"] and retired["quarters"] == 8.25
        stats = profile_statistics(db, 1)[1]
        assert stats.scored_round_count == int(kind == "participant")
        assert stats.known_participation_count == int(kind in {"participant", "incomplete"})
        assert stats.total_earnings == (4.5 if kind == "participant" else 0)
        assert stats.holes_played is None and stats.avg_earnings_per_hole is None
        assert db.query(models.RoundMigrationCheckpoint).count() == 2
        assert db.query(models.GameRecord).filter_by(game_id="next-saved").one().score_eligible
        assert verify_manifest(db, manifest)["errors"] == []


@pytest.mark.parametrize("tamper", ["whole_flag", "participant_flag", "remove_active"])
def test_retraction_or_active_removal_resealed_checkpoint_is_not_approved(migration_fixture, tmp_path, tamper):
    engine, snapshot = migration_fixture
    with Session(engine) as db:
        manifest, rid, pid = seed_review(db, snapshot, "whole" if tamper == "whole_flag" else "participant")
    assert cli(engine, tmp_path, manifest, "apply").returncode == 0
    with Session(engine) as db:
        if tamper == "whole_flag":
            db.get(models.GameRecord, rid).is_retracted = False
        elif tamper == "participant_flag":
            db.query(models.GamePlayerResult).filter_by(
                game_record_id=rid, participant_id="retired-slot"
            ).one().is_retracted = False
        else:
            game = db.query(models.GameStateModel).filter_by(game_id="detail-orphan").one()
            state = deepcopy(game.state)
            state.update(players=[], standings={})
            game.state = state
            flag_modified(game, "state")
            db.get(models.GameRecord, rid).final_scores = {}
            db.get(models.GameRecord, rid).player_count = 0
            db.get(models.GameRecord, rid).score_eligible = False
        db.flush()
        checkpoint = (
            db.query(models.RoundMigrationCheckpoint)
            .order_by(models.RoundMigrationCheckpoint.created_at.desc())
            .first()
        )
        checkpoint.outcome = {**checkpoint.outcome, "inventory_digest": current_inventory_digest(db)}
        db.commit()
        assert verify_manifest(db, manifest)["errors"]
    assert cli(engine, tmp_path, manifest, "verify").returncode == 2
    for _ in range(2):
        assert cli(engine, tmp_path, manifest, "apply").returncode == 2


@pytest.mark.parametrize("kind", ["empty", "historical_null"])
def test_unpublishable_originals_require_reviewed_hold_without_mutation(migration_fixture, tmp_path, kind):
    engine, snapshot = migration_fixture
    with Session(engine) as db:
        manifest, rid, pid = seed_review(db, snapshot, "participant")
        if kind == "empty":
            db.query(models.GamePlayerResult).filter_by(game_record_id=rid).delete()
        else:
            db.query(models.GamePlayerResult).filter_by(
                game_record_id=rid, participant_id="retired-slot"
            ).one().total_earnings = None
        db.commit()
        manifest = approved(db, snapshot)
        before = {m: rows(db, m) for m in (models.GameRecord, models.GamePlayerResult, models.GameStateModel)}
    for _ in range(2):
        assert cli(engine, tmp_path, manifest, "apply").returncode == 2
        with Session(engine) as db:
            assert {m: rows(db, m) for m in before} == before
            assert db.query(models.RoundMigrationCheckpoint).count() == 0
    manifest["saved_games"][0]["decision"].update(
        action="hold", reason=f"Reviewed {kind}: original roster cannot be published; no inference or deletion approved"
    )
    manifest["approval"]["expected_standings"] = {"guest:next-slot": {"score": 1.25, "scored": 1, "participation": 1}}
    approve_deltas(manifest)
    manifest = seal_manifest(manifest)
    for action in ("apply", "verify", "apply", "apply"):
        assert cli(engine, tmp_path, manifest, action).returncode == 0
    with Session(engine) as db:
        assert db.get(models.GameRecord, rid).accepted_revision == 0
        assert not db.query(models.GameStateModel).filter_by(game_id="detail-orphan").count()
        assert rows(db, models.GamePlayerResult) == before[models.GamePlayerResult]
        assert db.query(models.RoundMigrationCheckpoint).count() == 2
