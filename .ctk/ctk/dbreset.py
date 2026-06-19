"""Heal a drifted local SQLite schema so model drift never causes phantom test failures.

SQLAlchemy's ``create_all`` only CREATES missing tables — it never ALTERs an
existing one. So a long-lived on-disk SQLite dev/test DB keeps its old schema
after the models gain columns, and tests then fail with ``no such column``
(e.g. wolf-goat-pig's ``legacy_rounds.player_profile_id`` after PR #284).

``ensure_fresh_sqlite_schema`` detects that specific drift (a table missing, or
a model column the on-disk table lacks) and, only then, rebuilds the schema from
the models. When the schema already matches it is a no-op, so existing data is
preserved in the common case. It is SQLite-only by design and will NEVER drop a
non-SQLite database (e.g. Postgres in CI/prod).
"""

from __future__ import annotations

from typing import Any


def sqlite_schema_has_drifted(engine: Any, base: Any) -> bool:
    """True if any model table is missing from the DB, or an existing table is
    missing a column the model defines. Removed/extra DB columns are ignored —
    they don't cause ``no such column`` failures."""
    from sqlalchemy import inspect

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    for table in base.metadata.sorted_tables:
        if table.name not in existing_tables:
            return True
        db_columns = {col["name"] for col in inspector.get_columns(table.name)}
        model_columns = {col.name for col in table.columns}
        if model_columns - db_columns:
            return True
    return False


def ensure_fresh_sqlite_schema(engine: Any, base: Any) -> bool:
    """Rebuild a drifted SQLite schema from the models. Returns True if a rebuild
    ran, False if the engine isn't SQLite or the schema was already current.

    Safety: only acts on SQLite engines, so it can never drop a Postgres/MySQL DB.
    """
    if engine.dialect.name != "sqlite":
        return False
    if not sqlite_schema_has_drifted(engine, base):
        return False
    base.metadata.drop_all(bind=engine)
    base.metadata.create_all(bind=engine)
    return True
