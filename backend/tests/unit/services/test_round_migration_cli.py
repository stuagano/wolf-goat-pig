"""Actual subprocess CLI proof using a disposable file, no transport credentials."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import models
from app.services.round_migration_accounting import seal_manifest, snapshot_data
from tests.unit.services.test_round_identity_migration import migration_fixture

CLI = Path(__file__).resolve().parents[3] / "scripts" / "migrate_round_identity.py"


def invoke(engine, *args):
    env = {**os.environ, "DATABASE_URL": str(engine.url), "RUN_INPROCESS_SCHEDULERS": "false"}
    # Fixed repository CLI and fixture-owned arguments, never shell evaluation.
    return subprocess.run(  # noqa: S603
        [sys.executable, str(CLI), *args], env=env, text=True, capture_output=True, timeout=30
    )


@pytest.mark.parametrize("partial_canonical", [False, True])
def test_actual_cli_readonly_apply_rerun_verify_and_redacted_failure(migration_fixture, tmp_path, partial_canonical):
    engine, snapshot = migration_fixture
    with Session(engine) as db:
        config = db.get(models.AppConfig, "round_identity")
        config.value = {**config.value, "mode": "legacy", "epoch": 2}
        if partial_canonical:
            from datetime import date

            db.add(models.GameStateModel(game_id="partial-original", state={}))
            record = models.GameRecord(
                game_id="partial-original",
                player_count=1,
                played_on=date(2026, 10, 2),
                accepted_revision=0,
                completed_at="2026-10-02T00:00:00",
                roster_complete=True,
                game_settings={"played_at": "2026-10-02T00:00:00"},
            )
            db.add(record)
            db.flush()
            db.add(
                models.GamePlayerResult(
                    game_record_id=record.id, participant_id="partial-slot", player_name="Partial", total_earnings=6
                )
            )
        db.commit()
    result = invoke(engine, "pause", "--expect-epoch", "2", "--reason", "Synthetic pause-first window")
    assert result.returncode == 0, result.stderr
    source, target = tmp_path / "snapshot.json", tmp_path / "manifest.json"
    source.write_text(json.dumps(snapshot_data(snapshot)))
    result = invoke(engine, "dry-run", "--snapshot", str(source), "--output", str(target))
    assert result.returncode == 0, result.stderr
    with Session(engine) as reader:
        assert reader.query(models.GameStateModel).count() == int(partial_canonical)
        assert reader.query(models.RoundObservation).count() == 0
    manifest = json.loads(target.read_text())
    expected_baseline = {"Guest": {"score": 0.0, "scored": 1, "participation": 1}}
    if partial_canonical:
        expected_baseline["Partial"] = {"score": 6.0, "scored": 1, "participation": 1}
    assert manifest["baseline_pre_cutover"] == expected_baseline
    assert manifest["baseline_canonical_eligibility"] == {}
    assert manifest["configuration"]["reader_mode"] == "legacy"
    manifest["games"][0]["decision"] = {"action": "hold", "actor_profile_id": 1, "reason": "Synthetic ambiguity"}
    for entries in manifest["inventory"].values():
        for entry in entries:
            entry["decision"] = {"action": "preserve", "actor_profile_id": 1, "reason": "Retain original"}
    for saved in manifest["saved_games"]:
        saved["decision"] = {
            "action": "publish_original",
            "actor_profile_id": 1,
            "reason": "Reviewed original partial publication",
            "roster_complete": True,
        }
    expected = {"guest:partial-slot": {"score": 6.0, "scored": 1, "participation": 1}} if partial_canonical else {}
    manifest["approval"] = {"actor_profile_id": 1, "reason": "Synthetic rehearsal", "expected_standings": expected}
    from tests.unit.services.test_round_identity_migration import approve_deltas

    approve_deltas(manifest, {"Partial": "guest:partial-slot"})
    manifest = seal_manifest(manifest)
    reviewed = tmp_path / "reviewed.json"
    reviewed.write_text(json.dumps(manifest))
    for _ in range(2):
        result = invoke(
            engine,
            "apply",
            "--manifest",
            str(reviewed),
            "--expect-checksum",
            manifest["checksum"],
            "--ack-paused-writers",
        )
        assert result.returncode == 0, result.stderr
    result = invoke(
        engine,
        "finalize",
        "--manifest",
        str(reviewed),
        "--expect-checksum",
        manifest["checksum"],
        "--ack-paused-writers",
    )
    assert result.returncode == 0, result.stderr
    result = invoke(engine, "verify", "--manifest", str(reviewed))
    assert result.returncode == 0, result.stderr
    with Session(engine) as reader:
        assert reader.query(models.RoundObservation).count() == 1
        assert reader.query(models.RoundMigrationCheckpoint).count() == 1 + int(partial_canonical)
        assert reader.get(models.RoundComment, 1).body == "Original"
    failed = invoke(engine, "apply", "--manifest", str(reviewed), "--expect-checksum", "wrong", "--ack-paused-writers")
    assert failed.returncode == 2
    assert "Guest" not in failed.stdout + failed.stderr
    assert str(engine.url) not in failed.stdout + failed.stderr
    assert "details redacted" in failed.stderr
