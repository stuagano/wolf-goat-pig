#!/usr/bin/env python3
"""Offline identity migration. Local disposable databases only in this revision."""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.round_identity import RoundDraft, SourceRef
from app.services.round_cutover import pause_writers, store_verification
from app.services.round_evidence_guards import install_evidence_guards
from app.services.round_identity_migration import apply_manifest, build_manifest, finalize_constraints, verify_manifest
from app.services.round_snapshot import SheetRound, SheetSnapshot


def local_engine():
    raw = os.environ.get("DATABASE_URL", "")
    url = make_url(raw)
    if url.get_backend_name() == "sqlite":
        if not url.database or url.database == ":memory:":
            raise ValueError("Explicit disposable file database required")
    elif url.get_backend_name() == "postgresql":
        if url.host not in {"localhost", "127.0.0.1", "::1"} or not (url.database or "").endswith("_test") or url.query:
            raise ValueError("Only local disposable PostgreSQL *_test databases allowed")
        url = url.set(drivername="postgresql+psycopg2")
    else:
        raise ValueError("Only approved local disposable databases allowed")
    return create_engine(url, echo=False)


def load(path):
    return json.loads(Path(path).read_text())


def write_artifact(path, value):
    target = Path(path)
    # Never follow or overwrite an existing manifest/artifact, even a symlink.
    with target.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def snapshot_from_json(data):
    data = dict(data)
    data["rounds"] = [
        SheetRound(
            SourceRef.model_validate(r["source"]),
            RoundDraft.model_validate(r["draft"]),
            r["raw_payload"],
            r["observation_key"],
            r["continuity_verified"],
        )
        for r in data["rounds"]
    ]
    return SheetSnapshot(**data)


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    dry = commands.add_parser("dry-run", help="Read-only source/database inventory; never approves decisions")
    dry.add_argument("--snapshot", required=True)
    dry.add_argument("--output", required=True)
    verify = commands.add_parser("verify", help="Recompute actual database readback")
    verify.add_argument("--manifest", required=True)
    verify.add_argument("--store", action="store_true", help="Store server-side verification while paused")
    apply = commands.add_parser("apply", help="Whole-game commits with durable checkpoints")
    apply.add_argument("--manifest", required=True)
    apply.add_argument("--expect-checksum", required=True)
    apply.add_argument("--ack-paused-writers", action="store_true", required=True)
    finalize = commands.add_parser("finalize", help="Verify and install offline constraints and evidence guards")
    finalize.add_argument("--manifest", required=True)
    finalize.add_argument("--expect-checksum", required=True)
    finalize.add_argument("--ack-paused-writers", action="store_true", required=True)
    pause = commands.add_parser("pause", help="Drain converted writers and advance epoch; does not stop old binaries")
    pause.add_argument("--expect-epoch", type=int, required=True)
    pause.add_argument("--reason", required=True)
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    # SQL/driver exception text may contain DSNs or payloads; no raw exceptions.
    logging.disable(logging.CRITICAL)
    engine = None
    try:
        engine = local_engine()
        with Session(engine) as db:
            if args.command == "dry-run":
                if engine.dialect.name == "postgresql":
                    db.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"))
                else:
                    db.execute(text("PRAGMA query_only = ON"))
                manifest = build_manifest(db, snapshot_from_json(load(args.snapshot)))
                db.rollback()
                write_artifact(args.output, manifest)
                output = {"checksum": manifest["checksum"], "status": "unreviewed"}
            elif args.command == "pause":
                epoch = pause_writers(db, expected_epoch=args.expect_epoch, reason=args.reason)
                db.commit()
                output = {"mode": "paused", "epoch": epoch}
            else:
                manifest = load(args.manifest)
                if args.command == "apply":
                    output = apply_manifest(db, manifest, expected_checksum=args.expect_checksum)
                elif args.command == "finalize":
                    from app.services.round_migration_accounting import validate_checksum

                    validate_checksum(manifest, args.expect_checksum)
                    finalize_constraints(db, manifest)
                    install_evidence_guards(db)
                    db.commit()
                    output = {"status": "finalized", "manifest_checksum": manifest["checksum"]}
                else:
                    output = store_verification(db, manifest) if args.store else verify_manifest(db, manifest)
                    if args.store:
                        db.commit()
                    if output["errors"] or output["unaccounted_source_rows"]:
                        print(json.dumps({"status": "verification_failed", "error_count": len(output["errors"])}))
                        return 2
            # Never emit source rows, names, addresses, DB URLs, or evidence.
            print(
                json.dumps(
                    {
                        k: v
                        for k, v in output.items()
                        if k in {"checksum", "status", "mode", "epoch", "manifest_checksum"}
                    }
                )
            )
            return 0
    except Exception:
        print(
            "Migration refused; inspect approved local artifacts and database state (details redacted)", file=sys.stderr
        )
        return 2
    finally:
        if engine:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
