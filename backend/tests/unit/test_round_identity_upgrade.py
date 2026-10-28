"""Expansion is repeatable, preserves rows, and never rebuilds SQLite at boot."""

import os
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect, text

from app import database


@pytest.fixture
def local_engine(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'upgrade.db'}")
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", database.sessionmaker(bind=engine))
    yield engine
    engine.dispose()


def test_fresh_init_and_repeat_preserve_view_and_legacy_default(local_engine):
    database.init_db()
    with local_engine.begin() as conn:
        conn.execute(text("INSERT INTO legacy_rounds (id, member, status) VALUES (10, 'Avery', 'attested')"))
        conn.execute(text("INSERT INTO legacy_rounds (id, member, status) VALUES (11, 'Blair', 'pending')"))
    database.init_db()
    with local_engine.connect() as conn:
        assert conn.execute(text("SELECT id, game_id FROM legacy_rounds_official")).all() == [(10, None)]
        assert conn.execute(text("SELECT count(*) FROM app_config WHERE name='round_identity'")).scalar() == 0


def test_partial_expansion_is_resumable_without_backfill(local_engine):
    with local_engine.begin() as conn:
        conn.execute(text("CREATE TABLE legacy_rounds (id INTEGER PRIMARY KEY, member VARCHAR, status VARCHAR)"))
        conn.execute(text("INSERT INTO legacy_rounds VALUES (19, 'Original name', 'attested')"))
    database.ensure_legacy_rounds_official_view(local_engine)
    database.expand_round_identity_schema(local_engine)
    database.expand_round_identity_schema(local_engine)
    database.ensure_legacy_rounds_official_view(local_engine)
    with local_engine.connect() as conn:
        assert conn.execute(text("SELECT id, member, game_id FROM legacy_rounds_official")).all() == [
            (19, "Original name", None)
        ]
    assert {c["name"] for c in inspect(local_engine).get_columns("legacy_rounds")} >= {"game_id", "participant_id"}


def test_sqlite_rebuild_requirement_fails_explicitly_and_keeps_data(local_engine):
    with local_engine.begin() as conn:
        conn.execute(text("CREATE TABLE game_player_results (id INTEGER PRIMARY KEY, total_earnings FLOAT NOT NULL)"))
        conn.execute(text("INSERT INTO game_player_results VALUES (4, 7.5)"))
    with pytest.raises(RuntimeError, match=r"offline.*upgrade"):
        database.expand_round_identity_schema(local_engine)
    with local_engine.connect() as conn:
        assert conn.execute(text("SELECT id, total_earnings FROM game_player_results")).all() == [(4, 7.5)]


def test_retraction_columns_expand_without_rewriting_existing_rows(local_engine):
    with local_engine.begin() as conn:
        conn.execute(text("CREATE TABLE game_records (id INTEGER PRIMARY KEY)"))
        conn.execute(text("CREATE TABLE game_player_results (id INTEGER PRIMARY KEY, game_record_id INTEGER)"))
        conn.execute(text("INSERT INTO game_records VALUES (8)"))
        conn.execute(text("INSERT INTO game_player_results VALUES (9, 8)"))
    database.expand_round_identity_schema(local_engine)
    database.expand_round_identity_schema(local_engine)
    with local_engine.connect() as conn:
        assert conn.execute(text("SELECT id, is_retracted FROM game_records")).all() == [(8, 0)]
        assert conn.execute(text("SELECT id, is_retracted FROM game_player_results")).all() == [(9, 0)]


def test_old_delivery_sqlite_requires_explicit_offline_upgrade(local_engine):
    with local_engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE round_deliveries (id VARCHAR PRIMARY KEY, recipient_profile_id INTEGER NOT NULL, delivery_key VARCHAR)"
            )
        )
        conn.execute(text("INSERT INTO round_deliveries VALUES ('preserve', 7, 'old')"))
    with pytest.raises(RuntimeError, match="offline SQLite upgrade"):
        database.expand_round_identity_schema(local_engine)
    with local_engine.connect() as conn:
        assert conn.execute(text("SELECT * FROM round_deliveries")).all() == [("preserve", 7, "old")]


def test_sheet_queue_expansion_preserves_historical_unbound_job(local_engine):
    with local_engine.begin() as conn:
        conn.execute(text("CREATE TABLE pending_sheet_syncs (id INTEGER PRIMARY KEY, status VARCHAR)"))
        conn.execute(text("INSERT INTO pending_sheet_syncs VALUES (17, 'processing')"))
    database.expand_round_identity_schema(local_engine)
    database.expand_round_identity_schema(local_engine)
    with local_engine.connect() as conn:
        assert conn.execute(
            text("SELECT id, status, prewrite, lease_owner, expected_epoch FROM pending_sheet_syncs")
        ).all() == [(17, "processing", None, None, None)]
    assert any(
        i["name"] == "uq_sheet_sync_operation" and i["unique"]
        for i in inspect(local_engine).get_indexes("pending_sheet_syncs")
    )


def test_missing_status_view_is_skipped(local_engine):
    with local_engine.begin() as conn:
        conn.execute(text("CREATE TABLE legacy_rounds (id INTEGER PRIMARY KEY)"))
    database.ensure_legacy_rounds_official_view(local_engine)
    assert inspect(local_engine).get_view_names() == []


def test_postgres_expansion_restart_and_partial_apply():
    """Opt-in only to a disposable loopback *_test database; never shared data."""
    from sqlalchemy.engine import make_url

    from app.migrations_runner import _statements

    url = os.getenv("ROUND_IDENTITY_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set ROUND_IDENTITY_TEST_DATABASE_URL to a disposable local *_test database")
    parsed = make_url(url)
    if parsed.host not in ("127.0.0.1", "localhost") or not (parsed.database or "").endswith("_test"):
        pytest.fail("Identity upgrade tests require a disposable loopback *_test database")
    engine = create_engine(parsed.set(drivername="postgresql+psycopg2"))
    schema = "identity_" + uuid4().hex
    sql = (
        Path(__file__).resolve().parents[2] / "migrations" / "zz_20261027_round_identity_expand_postgres.sql"
    ).read_text()
    statements = _statements(sql)
    try:
        with engine.connect() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
            conn.execute(text(f'SET search_path TO "{schema}"'))
            conn.commit()
            database.Base.metadata.create_all(conn)
            conn.commit()
            # Rehearse creation of all new evidence tables, not just ORM create_all.
            for table in reversed(database.Base.metadata.sorted_tables):
                if table.name.startswith("round_") and table.name not in ("round_comments", "round_reactions"):
                    conn.execute(text(f'DROP TABLE "{table.name}"'))
            # Reproduce a pre-expansion view and missing columns without dropping rows.
            for table, column in (
                ("legacy_rounds", "game_id"),
                ("legacy_rounds", "participant_id"),
                ("game_state", "revision"),
            ):
                conn.execute(text(f'ALTER TABLE "{table}" DROP COLUMN "{column}"'))
            conn.execute(text("INSERT INTO legacy_rounds (id, member, status) VALUES (29, 'Original', 'attested')"))
            conn.commit()
            conn.execute(
                text("CREATE VIEW legacy_rounds_official AS SELECT * FROM legacy_rounds WHERE status <> 'pending'")
            )
            conn.commit()
            # Simulate startup interruption after independently committed DDL.
            for statement in statements[:3]:
                conn.execute(text(statement))
                conn.commit()
            for _ in range(2):
                for statement in statements:
                    conn.execute(text(statement))
                    conn.commit()
            assert conn.execute(text("SELECT id, member, game_id FROM legacy_rounds_official")).all() == [
                (29, "Original", None)
            ]
            assert conn.execute(text("SELECT count(*) FROM app_config")).scalar() == 0
    finally:
        with engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        engine.dispose()


def test_postgres_expansion_is_simple_restart_safe_ddl_only():
    from app.migrations_runner import _statements

    sql = (
        Path(__file__).resolve().parents[2] / "migrations" / "zz_20261027_round_identity_expand_postgres.sql"
    ).read_text()
    statements = _statements(sql)
    assert statements
    for statement in statements:
        normalized = statement.upper()
        assert not any(word in normalized for word in ("INSERT INTO", "UPDATE ", "DELETE FROM", "DROP TABLE"))
        assert (
            "IF NOT EXISTS" in normalized
            or "DROP NOT NULL" in normalized
            or "DROP DEFAULT" in normalized
            or "SET NOT NULL" in normalized
            or "CREATE OR REPLACE VIEW" in normalized
        )
