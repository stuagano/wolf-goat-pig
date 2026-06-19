"""Tests for ctk.dbreset — the local-SQLite drift healer wired into conftest."""

from ctk.dbreset import ensure_fresh_sqlite_schema, sqlite_schema_has_drifted
from sqlalchemy import Column, Integer, MetaData, Table, create_engine, inspect


class _FakeBase:
    def __init__(self, metadata):
        self.metadata = metadata


def _model_metadata(with_new_column: bool) -> MetaData:
    md = MetaData()
    cols = [Column("id", Integer, primary_key=True)]
    if with_new_column:
        cols.append(Column("new_col", Integer))
    Table("widget", md, *cols)
    return md


def test_rebuilds_when_a_model_column_is_missing(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 't.db'}")
    # On-disk schema = old (no new_col)
    _model_metadata(with_new_column=False).create_all(engine)
    # Model now defines new_col -> drift
    base = _FakeBase(_model_metadata(with_new_column=True))

    assert sqlite_schema_has_drifted(engine, base) is True
    assert ensure_fresh_sqlite_schema(engine, base) is True
    cols = {c["name"] for c in inspect(engine).get_columns("widget")}
    assert "new_col" in cols


def test_noop_when_schema_is_current(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 't.db'}")
    base = _FakeBase(_model_metadata(with_new_column=True))
    base.metadata.create_all(engine)

    assert sqlite_schema_has_drifted(engine, base) is False
    assert ensure_fresh_sqlite_schema(engine, base) is False


def test_never_touches_a_non_sqlite_engine():
    class _Dialect:
        name = "postgresql"

    class _Engine:
        dialect = _Dialect()

    # Must return False without inspecting/dropping anything on a non-SQLite DB.
    assert ensure_fresh_sqlite_schema(_Engine(), object()) is False
