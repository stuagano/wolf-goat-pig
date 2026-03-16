"""Shared test configuration for backend test suite.

Ensures the backend package is importable and initializes the test database.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


def _ensure_paths() -> None:
    """Add backend and repo root to sys.path when missing."""
    backend_dir = Path(__file__).resolve().parents[1]
    repo_root = backend_dir.parent

    for p in (str(backend_dir), str(repo_root)):
        if p not in sys.path:
            sys.path.insert(0, p)


_ensure_paths()

# Harden default environment for backend tests.
os.environ.setdefault("ENABLE_TEST_ENDPOINTS", "false")


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initialize test database tables before running tests."""
    from app import models  # noqa: F401
    from app.database import Base, engine

    Base.metadata.create_all(bind=engine)

    try:
        from app.seed_courses import seed_courses
        seed_courses()
    except Exception:
        pass  # Ignore if already seeded or any issues

    yield
