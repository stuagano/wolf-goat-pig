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
from fastapi import Header


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


@pytest.fixture
def mock_admin_identity():
    """Translate legacy test headers into mocked authenticated users.

    Production routes never trust this header; this fixture only keeps router
    tests focused on authorization outcomes without minting Auth0 JWTs.
    """
    from app.main import app
    from app.models import PlayerProfile
    from app.services.auth_service import get_current_auth0_user, get_current_user

    def _current_user(x_admin_email: str | None = Header(None)) -> PlayerProfile:
        return PlayerProfile(
            id=999,
            name="Admin Test User",
            email=x_admin_email,
            handicap=18.0,
            is_active=1,
            is_ai=0,
            created_at="2026-01-01T00:00:00",
        )

    def _auth0_user(x_admin_email: str | None = Header(None)) -> dict[str, str | None]:
        return {
            "sub": "auth0|admin-test",
            "email": x_admin_email,
            "name": "Admin Test User",
        }

    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_current_auth0_user] = _auth0_user
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_current_auth0_user, None)
