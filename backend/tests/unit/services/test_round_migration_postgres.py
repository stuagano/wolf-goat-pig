"""Physical disposable PostgreSQL proof; never reads configured application DB."""

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app import models
from app.services.round_cutover import guard_writer, pause_writers
from app.services.round_evidence_guards import install_evidence_guards, prove_evidence_guards
from tests.unit.services.test_round_identity_migration import migration_fixture


@pytest.fixture(params=["ROUND_MIGRATION_PG17_URL", "ROUND_MIGRATION_PG15_URL"])
def migration_pg(request):
    raw = os.environ.get(request.param)
    if not raw:
        pytest.fail(f"Disposable {request.param} required for physical migration proof")
    url = make_url(raw)
    if url.host != "127.0.0.1" or not (url.database or "").endswith("_test") or url.query:
        pytest.fail("Only explicit localhost disposable test databases allowed")
    schema = "migration_" + uuid4().hex
    admin = create_engine(url)
    with admin.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema} -cstatement_timeout=10000"})
    try:
        models.Base.metadata.create_all(engine)
        with Session(engine) as db:
            db.add(models.AppConfig(name="round_identity", value={"mode": "legacy", "epoch": 1}))
            db.add(models.PlayerProfile(id=1, name="Synthetic reviewer", is_active=1))
            db.flush()
            source = models.RoundSource(kind="fixture", scope="synthetic", round_token="one")
            db.add(source)
            db.flush()
            observation = models.RoundObservation(
                source_id=source.id,
                observation_key="one",
                raw_payload={"synthetic": True},
                parsed_values={},
                present_fields={},
                content_fingerprint="one",
            )
            db.add(observation)
            db.flush()
            issue = models.RoundIssue(
                source_id=source.id, observation_id=observation.id, kind="identity", fingerprint="one", field="identity"
            )
            db.add(issue)
            db.flush()
            db.add(
                models.RoundResolution(
                    issue_id=issue.id,
                    actor_profile_id=1,
                    action="keep",
                    reason="Fixture",
                    observation_ids=[observation.id],
                )
            )
            db.commit()
        yield engine
    finally:
        engine.dispose()
        with admin.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


@pytest.mark.parametrize("variable", ["ROUND_MIGRATION_PG17_URL", "ROUND_MIGRATION_PG15_URL"])
@pytest.mark.parametrize(
    "partial_canonical",
    [
        False,
        True,
        "original_detail",
        "detail_missing",
        "detail_conflict",
        "detail_retracted",
        "detail_tamper",
        "unknown_single",
        "unknown_mixed",
    ]
    + [
        f"history_{kind}_{coverage}"
        for kind in (
            "added",
            "duplicate",
            "missing",
            "replaced",
            "malformed",
            "invented_field",
            "eligibility",
            "standings",
        )
        for coverage in ("complete", "partial")
    ],
)
def test_actual_postgres_cli_rehearsal(variable, migration_fixture, tmp_path, partial_canonical):
    from tests.unit.services.test_round_migration_cli import (
        test_actual_cli_readonly_apply_rerun_verify_and_redacted_failure as prove_cli,
    )

    url = make_url(os.environ[variable])
    assert url.host == "127.0.0.1" and url.database.endswith("_test") and not url.query
    name = "migration_" + uuid4().hex + "_test"
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{name}"'))
    engine = create_engine(url.set(database=name))
    source, snapshot = migration_fixture
    try:
        models.Base.metadata.create_all(engine)
        with Session(source) as reader, Session(engine) as writer:
            for model in (
                models.AppConfig,
                models.PlayerProfile,
                models.LegacyRound,
                models.RoundComment,
                models.RoundReaction,
            ):
                for row in reader.query(model):
                    writer.add(model(**{a.key: getattr(row, a.key) for a in model.__mapper__.column_attrs}))
                writer.flush()
            writer.commit()
        if isinstance(partial_canonical, str) and partial_canonical.startswith("unknown_"):
            from tests.unit.services.test_round_saved_invariants import (
                test_unknown_original_total_requires_hold_before_commit,
            )

            test_unknown_original_total_requires_hold_before_commit(
                (engine, snapshot), tmp_path, partial_canonical == "unknown_mixed"
            )
        elif isinstance(partial_canonical, str) and partial_canonical.startswith("history_"):
            from tests.unit.services.test_round_saved_invariants import (
                test_exact_original_history_and_projection_reject_resealed_tamper,
            )

            kind, coverage = partial_canonical.removeprefix("history_").rsplit("_", 1)
            test_exact_original_history_and_projection_reject_resealed_tamper(
                (engine, snapshot), tmp_path, coverage == "partial", kind
            )
        elif partial_canonical == "original_detail":
            from tests.unit.services.test_round_saved_detail import prove_detail

            prove_detail(engine, snapshot, tmp_path)
        elif isinstance(partial_canonical, str) and partial_canonical.startswith("detail_"):
            from tests.unit.services.test_round_saved_detail import (
                test_insufficient_detail_requires_explicit_hold,
                test_verifier_and_replay_reject_detail_loss_even_resealed_checkpoint,
            )

            if partial_canonical == "detail_tamper":
                test_verifier_and_replay_reject_detail_loss_even_resealed_checkpoint(
                    (engine, snapshot), tmp_path, "all"
                )
            else:
                test_insufficient_detail_requires_explicit_hold(
                    (engine, snapshot), partial_canonical.removeprefix("detail_")
                )
        else:
            prove_cli((engine, snapshot), tmp_path, partial_canonical)
    finally:
        engine.dispose()
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE "{name}"'))
        admin.dispose()


def test_normal_init_default_legacy_commissioner_endpoint(migration_pg, monkeypatch):
    from tests.unit.services.test_round_cutover_review import test_normal_fresh_default_legacy_commissioner_http

    with Session(migration_pg) as db:
        db.add(
            models.LegacyRound(
                date="2026-10-01", group="A", member="Original", score=7, source="sheet", status="attested"
            )
        )
        db.commit()
        test_normal_fresh_default_legacy_commissioner_http(db, monkeypatch)


def test_direct_sql_update_delete_truncate_blocked_with_surviving_readback(migration_pg):
    with Session(migration_pg) as db:
        install_evidence_guards(db)
        db.commit()
    with Session(migration_pg) as reader:
        proof = prove_evidence_guards(reader)
        assert set(proof) == {"round_observations", "round_resolutions"}
        assert reader.query(models.RoundObservation).count() == 1
        assert reader.query(models.RoundResolution).count() == 1


@pytest.mark.parametrize("caller", ["writer", "attest", "delete"])
def test_shared_writer_lock_survives_until_commit_and_cutover_drains(migration_pg, caller, monkeypatch):
    entered, finished = Event(), Event()

    def cutover():
        with Session(migration_pg) as db:
            entered.set()
            epoch = pause_writers(db, expected_epoch=1, reason="Synthetic cutover")
            db.commit()
            finished.set()
            return epoch

    with Session(migration_pg) as writer, ThreadPoolExecutor(max_workers=1) as pool:
        if caller == "writer":
            guard_writer(writer)
        else:
            import asyncio

            from app.routers import games, member_rounds

            with Session(migration_pg) as setup:
                setup.add(models.GameStateModel(game_id="fenced-game", state={}))
                setup.add(
                    models.LegacyRound(id=99, source="member", status="pending", member="Author", foursome=["Witness"])
                )
                setup.commit()
            # Intercept only the transaction boundary: the real caller must have
            # acquired a fence before its state/ownership read and mutations.
            commit = writer.commit
            monkeypatch.setattr(writer, "commit", lambda: writer.flush())
            if caller == "attest":
                member_rounds.attest_round(
                    99, models.PlayerProfile(id=1, name="Witness", legacy_name="Witness"), writer
                )
            else:
                asyncio.run(games.delete_game("fenced-game", writer))
            monkeypatch.setattr(writer, "commit", commit)
        future = pool.submit(cutover)
        assert entered.wait(2)
        assert not finished.wait(0.2)
        # A separate physical session confirms a PostgreSQL lock wait, rather
        # than treating a sleeping worker as proof of a fence.
        with migration_pg.connect() as inspector:
            assert (
                inspector.scalar(
                    text(
                        "SELECT count(*) FROM pg_stat_activity WHERE wait_event_type='Lock' "
                        "AND query LIKE '%pg_advisory_xact_lock%'"
                    )
                )
                >= 1
            )
        writer.commit()
        assert future.result(timeout=5) == 2
    with Session(migration_pg) as reader:
        assert reader.get(models.AppConfig, "round_identity").value["mode"] == "paused"
        with pytest.raises(Exception, match="paused"):
            guard_writer(reader)
