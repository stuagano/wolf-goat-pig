"""Actual subprocess CLI proof using a disposable file, no transport credentials."""

import json
import os
import subprocess
import sys
from pathlib import Path

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


def test_actual_cli_readonly_apply_rerun_verify_and_redacted_failure(migration_fixture, tmp_path):
    engine, snapshot = migration_fixture
    source, target = tmp_path / "snapshot.json", tmp_path / "manifest.json"
    source.write_text(json.dumps(snapshot_data(snapshot)))
    result = invoke(engine, "dry-run", "--snapshot", str(source), "--output", str(target))
    assert result.returncode == 0, result.stderr
    with Session(engine) as reader:
        assert reader.query(models.GameStateModel).count() == 0
        assert reader.query(models.RoundObservation).count() == 0
    manifest = json.loads(target.read_text())
    manifest["games"][0]["decision"] = {"action": "hold", "actor_profile_id": 1, "reason": "Synthetic ambiguity"}
    for entries in manifest["inventory"].values():
        for entry in entries:
            entry["decision"] = {"action": "preserve", "actor_profile_id": 1, "reason": "Retain original"}
    manifest["approval"] = {"actor_profile_id": 1, "reason": "Synthetic rehearsal", "expected_standings": {}}
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
        assert reader.query(models.RoundMigrationCheckpoint).count() == 1
        assert reader.get(models.RoundComment, 1).body == "Original"
    failed = invoke(engine, "apply", "--manifest", str(reviewed), "--expect-checksum", "wrong", "--ack-paused-writers")
    assert failed.returncode == 2
    assert "Guest" not in failed.stdout + failed.stderr
    assert str(engine.url) not in failed.stdout + failed.stderr
    assert "details redacted" in failed.stderr
