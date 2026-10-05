"""PostgreSQL startup must use the driver installed by requirements.txt."""

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "url",
    [
        "postgres://user:password@localhost/example",
        "postgresql://user:password@/example?host=/cloudsql/project:region:instance",
        "postgresql+psycopg2://user:password@localhost/example",
    ],
)
def test_postgres_startup_uses_installed_driver(url):
    result = subprocess.run(  # noqa: S603 - fixed Python code and test-only URLs, no shell
        [
            sys.executable,
            "-c",
            "from sqlalchemy.dialects import registry; "
            "registry.register('postgresql', 'sqlalchemy.dialects.postgresql.psycopg', 'PGDialect_psycopg'); "
            "from app.database import engine; "
            "assert engine.dialect.name == 'postgresql'; "
            "assert engine.dialect.driver == 'psycopg2'; "
            "assert engine.dialect.dbapi.__name__ == 'psycopg2'; "
            "import os; from sqlalchemy.engine import make_url; "
            "original = make_url(os.environ['DATABASE_URL']); "
            "assert engine.url.query == original.query; "
            "assert engine.url.password == original.password; "
            "engine.dispose()",
        ],
        cwd=Path(__file__).resolve().parents[2],
        env={**os.environ, "DATABASE_URL": url, "ENVIRONMENT": "test"},
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
