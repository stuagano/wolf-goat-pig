"""Shared test configuration for backend test suite.

Ensures the backend package is importable from the repository root and keeps
test-only endpoints disabled by default so unit suites reflect production
behavior.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _ensure_repo_root_on_path() -> None:
    """Add the repository root to sys.path when missing."""
    repo_root = Path(__file__).resolve().parents[2]
    repo_root_str = str(repo_root)

    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


_ensure_repo_root_on_path()

# Harden default environment for backend tests.
os.environ.setdefault("ENABLE_TEST_ENDPOINTS", "false")


import pytest


@pytest.fixture(scope="session", autouse=True)
def _heal_drifted_local_sqlite_schema():
    """Rebuild a drifted local SQLite schema once per session.

    SQLAlchemy's create_all never ALTERs existing tables, so a long-lived
    backend/wolf_goat_pig.db keeps a stale schema after the models gain columns
    and tests fail with "no such column". ctk.dbreset heals exactly that drift
    (SQLite only — it never drops a Postgres DB, so CI/prod are untouched).
    """
    from ctk.dbreset import ensure_fresh_sqlite_schema

    from app.database import engine
    from app.models import Base

    ensure_fresh_sqlite_schema(engine, Base)
    yield
