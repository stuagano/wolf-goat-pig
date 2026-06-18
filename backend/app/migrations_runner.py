"""Apply migrations/*.sql files automatically at startup.

History: the repo accumulated *_postgres.sql migration files under
backend/migrations/ on the assumption something applied them at boot —
nothing did. startup.py only runs a hardcoded column list, and
Base.metadata.create_all creates missing TABLES but never adds COLUMNS
to existing ones. Result: schema drift (e.g. badges.emoji missing in
production while the model declared it).

This runner makes the convention real:
- Postgres only (SQLite dev DBs are rebuilt by create_all).
- Files named *_postgres.sql in backend/migrations/, applied in sorted
  filename order.
- Each file is applied exactly once, tracked in schema_migrations.
- Statements tolerate "already exists / duplicate" errors so previously
  hand-applied migrations record cleanly.
- A failing migration logs loudly but never blocks boot.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"

_BENIGN_ERROR_RE = re.compile(r"already exists|duplicate column|duplicate key|duplicate object", re.IGNORECASE)


def _statements(sql: str) -> list[str]:
    """Split a simple DDL file into statements (comment lines stripped)."""
    lines = [ln for ln in sql.splitlines() if not ln.strip().startswith("--")]
    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]


def run_sql_migrations(engine: Engine) -> dict:
    """Apply pending *_postgres.sql migrations. Returns a summary dict."""
    if engine.dialect.name != "postgresql":
        return {"skipped": "not_postgres"}

    files = sorted(MIGRATIONS_DIR.glob("*_postgres.sql"))
    if not files:
        return {"applied": [], "message": "no migration files"}

    applied: list[str] = []
    failed: list[str] = []

    with engine.connect() as conn:
        conn.execute(
            text("CREATE TABLE IF NOT EXISTS schema_migrations (filename VARCHAR PRIMARY KEY, applied_at VARCHAR)")
        )
        conn.commit()
        done = {row[0] for row in conn.execute(text("SELECT filename FROM schema_migrations"))}

        for f in files:
            if f.name in done:
                continue
            logger.info("Applying migration %s", f.name)
            ok = True
            for stmt in _statements(f.read_text()):
                try:
                    conn.execute(text(stmt))
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    if _BENIGN_ERROR_RE.search(str(e)):
                        logger.info("  (already applied) %s…", stmt[:60])
                        continue
                    logger.error("Migration %s failed on: %s… — %s", f.name, stmt[:80], e)
                    ok = False
                    break
            if ok:
                from .utils.time import utc_now

                conn.execute(
                    text("INSERT INTO schema_migrations (filename, applied_at) VALUES (:f, :t)"),
                    {"f": f.name, "t": utc_now().isoformat()},
                )
                conn.commit()
                applied.append(f.name)
            else:
                failed.append(f.name)

    if applied:
        logger.info("Applied %d migration(s): %s", len(applied), ", ".join(applied))
    if failed:
        logger.error("FAILED migration(s) — schema may be drifted: %s", ", ".join(failed))
    return {"applied": applied, "failed": failed}
