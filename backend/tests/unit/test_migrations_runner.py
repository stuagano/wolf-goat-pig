"""Guards the startup SQL-migration runner (app/migrations_runner.py).

History: *_postgres.sql files accumulated under backend/migrations/ on the
assumption something applied them at boot — nothing did, causing schema drift
(badges.emoji missing in prod). migrations_runner made the convention real;
this locks its core behavior: apply-once tracking, idempotency, benign-error
tolerance, and never blocking boot.

The apply path is Postgres-gated, so we drive it against a real on-disk SQLite
engine with the dialect faked to 'postgresql' and SQLite-compatible temp
migrations — exercising the real tracking/idempotency loop without a Postgres.
"""

import pytest
from sqlalchemy import create_engine, text

import app.migrations_runner as mr


def _pg_sqlite_engine(tmp_path):
    """A real on-disk SQLite engine that reports dialect 'postgresql' so the
    runner's apply path executes (file-based so state persists across the
    runner's per-call connections)."""
    engine = create_engine(f"sqlite:///{tmp_path / 'mig.db'}")
    engine.dialect.name = "postgresql"  # instance attr shadows the class attr
    return engine


def _write_migration(tmp_path, monkeypatch, name, sql):
    (tmp_path / name).write_text(sql)
    monkeypatch.setattr(mr, "MIGRATIONS_DIR", tmp_path)


class TestStatements:
    def test_strips_comments_and_splits_on_semicolons(self):
        sql = "-- header\nCREATE TABLE a (id INT);\n-- note\nALTER TABLE a ADD COLUMN b INT;\n"
        assert mr._statements(sql) == [
            "CREATE TABLE a (id INT)",
            "ALTER TABLE a ADD COLUMN b INT",
        ]

    def test_drops_empty_statements(self):
        assert mr._statements(";;\n-- only a comment\n;") == []


class TestRunSqlMigrations:
    def test_non_postgres_engine_is_skipped_and_never_raises(self):
        engine = create_engine("sqlite://")  # real sqlite dialect
        assert mr.run_sql_migrations(engine) == {"skipped": "not_postgres"}

    def test_applies_tracks_then_is_idempotent(self, tmp_path, monkeypatch):
        _write_migration(
            tmp_path,
            monkeypatch,
            "001_widget_postgres.sql",
            "CREATE TABLE widget (id INTEGER PRIMARY KEY);",
        )
        engine = _pg_sqlite_engine(tmp_path)

        first = mr.run_sql_migrations(engine)
        assert first["applied"] == ["001_widget_postgres.sql"]
        assert first.get("failed", []) == []

        # the migration really ran: the table exists and is usable
        with engine.connect() as conn:
            conn.execute(text("INSERT INTO widget (id) VALUES (1)"))
            conn.commit()
            assert conn.execute(text("SELECT count(*) FROM widget")).scalar() == 1
            tracked = {r[0] for r in conn.execute(text("SELECT filename FROM schema_migrations"))}
        assert "001_widget_postgres.sql" in tracked

        # second run is a no-op (already tracked) — apply-once
        second = mr.run_sql_migrations(engine)
        assert second["applied"] == []

    def test_benign_already_exists_is_tolerated(self, tmp_path, monkeypatch):
        engine = _pg_sqlite_engine(tmp_path)
        # pre-create the table so the migration's CREATE hits "already exists"
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE preexisting (id INTEGER)"))
            conn.commit()
        _write_migration(
            tmp_path,
            monkeypatch,
            "002_preexisting_postgres.sql",
            "CREATE TABLE preexisting (id INTEGER);",
        )
        result = mr.run_sql_migrations(engine)
        # benign error swallowed -> migration still records as applied, not failed
        assert "002_preexisting_postgres.sql" in result["applied"]
        assert result.get("failed", []) == []

    def test_bad_statement_records_failure_but_does_not_block_boot(self, tmp_path, monkeypatch):
        _write_migration(
            tmp_path,
            monkeypatch,
            "003_bogus_postgres.sql",
            "THIS IS NOT VALID SQL;",
        )
        engine = _pg_sqlite_engine(tmp_path)
        # must NOT raise (boot must continue even on a broken migration)
        result = mr.run_sql_migrations(engine)
        assert "003_bogus_postgres.sql" in result["failed"]
        assert result["applied"] == []
