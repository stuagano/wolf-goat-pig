import logging
import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from starlette.exceptions import HTTPException

from .observability.score_save import is_score_save_request

logger = logging.getLogger(__name__)


def _int_env(name: str, default: int) -> int:
    """Read an int env var, falling back to ``default`` on unset/invalid values."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid int for %s=%r; using default %d", name, raw, default)
        return default


# Database configuration with environment-specific settings
DATABASE_URL = os.getenv("DATABASE_URL")

# Check if we're using PostgreSQL or SQLite
is_postgresql = DATABASE_URL and DATABASE_URL.startswith(("postgres://", "postgresql://", "postgresql+psycopg2://"))

if is_postgresql and DATABASE_URL:
    # Production database (PostgreSQL)
    if DATABASE_URL.startswith("postgres://"):
        # Fix for newer SQLAlchemy versions
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # Pool sizing is env-tunable. Bump DB_POOL_SIZE/DB_MAX_OVERFLOW via env
    # without a code change. The Cloud SQL Auth Proxy / Unix-socket form
    # (postgresql://user:pass@/db?host=/cloudsql/CONN) works unchanged here:
    # Explicitly select the installed psycopg2 driver; SQLAlchemy's default can change.
    engine = create_engine(
        make_url(DATABASE_URL).set(drivername="postgresql+psycopg2"),
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=_int_env("DB_POOL_RECYCLE", 300),  # Recycle connections every 5 minutes
        pool_size=_int_env("DB_POOL_SIZE", 5),  # Maximum persistent pool size
        max_overflow=_int_env("DB_MAX_OVERFLOW", 10),  # Allow additional overflow connections
        pool_timeout=_int_env("DB_POOL_TIMEOUT", 30),  # Wait up to 30s for a connection
        pool_reset_on_return="rollback",  # Always rollback on connection return to reset transaction state
        connect_args={
            "connect_timeout": _int_env("DB_CONNECT_TIMEOUT", 10),  # Connection timeout in seconds
            "options": f"-c statement_timeout={_int_env('DB_STATEMENT_TIMEOUT_MS', 30000)}",  # Query timeout
        },
        echo=os.getenv("ENVIRONMENT") == "development",
    )
else:
    # Development/local database (SQLite)
    # Check if DATABASE_URL is set to a SQLite path
    if DATABASE_URL and DATABASE_URL.startswith("sqlite:///"):
        SQLITE_DATABASE_URL = DATABASE_URL
    else:
        SQLITE_DATABASE_URL = "sqlite:///./wolf_goat_pig.db"

    engine = create_engine(
        SQLITE_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=os.getenv("ENVIRONMENT") == "development",
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    FastAPI dependency for database sessions.
    Use this for endpoint dependencies: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    except HTTPException:
        # Expected client errors (e.g. a 403 from require_admin) are not DB failures.
        db.rollback()
        raise
    except Exception as e:
        # The score-save middleware records a bounded correlated outcome.
        # Validation and SQL exceptions here can contain the entire payload.
        if not is_score_save_request():
            logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_isolated_session() -> Generator[Session, None, None]:
    """
    Context manager for isolated database sessions.

    Use this for independent operations that should not share transaction state:
    - Background tasks
    - Batch operations
    - Operations that might fail but shouldn't affect other operations

    Example:
        with get_isolated_session() as db:
            # Do database operations
            db.commit()  # Explicitly commit

    Benefits:
    - Each operation gets its own connection from the pool
    - Transaction failures are isolated
    - Automatic rollback on exception
    - Automatic session cleanup
    """
    session = SessionLocal()
    try:
        logger.debug("Created isolated database session")
        yield session
        # Note: Caller must explicitly commit() if they want changes persisted
    except Exception as e:
        logger.error(f"Error in isolated session: {e}")
        session.rollback()
        raise
    finally:
        session.close()
        logger.debug("Closed isolated database session")


def ensure_legacy_rounds_official_view(bind) -> None:
    """Create the ``legacy_rounds_official`` view if the status column exists.

    The view excludes unattested member self-posts (``status='pending'``) and is
    the only legacy-rounds source the Commissioner's read-only SQL path may query.
    DDL-only boot compatibility; no identity rows are backfilled.
    Skips when the ``status`` column is missing (pre-attestation schema).
    """
    dialect = bind.dialect.name
    inspector = inspect(bind)
    if not inspector.has_table("legacy_rounds") or "status" not in {
        column["name"] for column in inspector.get_columns("legacy_rounds")
    }:
        logger.warning("Skipping legacy_rounds_official view — legacy_rounds.status column missing")
        return
    # Explicit legacy compatibility columns: expansion must not silently alter
    # a view's schema or make boot perform identity backfill/contraction.
    names = [c["name"] for c in inspector.get_columns("legacy_rounds")]
    projection = ", ".join(f'"{name}"' for name in names)
    with bind.begin() as conn:
        if dialect == "postgresql":
            # Existing PostgreSQL views may have a pre-expansion column order.
            # Appending columns is legal; never reorder or drop at boot.
            conn.execute(
                text(
                    "CREATE OR REPLACE VIEW legacy_rounds_official AS "
                    f"SELECT {projection} FROM legacy_rounds WHERE status <> 'pending'"
                )
            )
            return
        conn.execute(text("DROP VIEW IF EXISTS legacy_rounds_official"))
        conn.execute(
            text(
                "CREATE VIEW legacy_rounds_official AS "
                f"SELECT {projection} FROM legacy_rounds WHERE status <> 'pending'"
            )
        )


# Columns the Commissioner's read-only SQL path may read. Keep in sync with the
# schema documented in routers/commissioner.py.
CANONICAL_ROUND_RESULTS_VIEW = """
SELECT r.game_id AS game_id, p.participant_id AS participant_id,
       p.player_profile_id AS player_profile_id, p.player_name AS member,
       p.total_earnings AS score, r.played_on AS played_on, r.raw_date AS raw_date,
       r.course_name AS location, r."group" AS "group", r.detail_coverage AS detail_coverage,
       r.score_eligible AS score_eligible, r.accepted_revision AS accepted_revision
FROM game_records r
JOIN game_player_results p ON p.game_record_id = r.id
WHERE r.is_retracted = false AND p.is_retracted = false
  AND r.accepted_revision > 0 AND p.participant_id IS NOT NULL
"""


def ensure_canonical_round_results_view(bind) -> None:
    """Current-season eligible verified-profile results for Commissioner standings.

    This scored-only projection matches the profile leaderboard, not all-time
    history or guest-inclusive extreme scores. COUNT(*) is scored appearances;
    known participation coverage comes from UnifiedDataService, not this view.
    """
    inspector = inspect(bind)
    required = {"game_records": ("is_retracted", "accepted_revision"), "game_player_results": ("is_retracted",)}
    for table, columns in required.items():
        if not inspector.has_table(table) or not set(columns) <= {c["name"] for c in inspector.get_columns(table)}:
            logger.warning("Skipping canonical_round_results view — %s expansion incomplete", table)
            return
    sql = (
        CANONICAL_ROUND_RESULTS_VIEW
        + """
  AND r.score_eligible = true AND r.roster_complete = true
  AND r.played_on IS NOT NULL AND p.total_earnings IS NOT NULL
  AND p.player_profile_id IS NOT NULL
  AND EXISTS (SELECT 1 FROM game_state g WHERE g.game_id = r.game_id)
  AND r.player_count = (SELECT COUNT(*) FROM game_player_results x
                       WHERE x.game_record_id = r.id AND x.is_retracted = false
                       AND x.participant_id IS NOT NULL)
   AND NOT EXISTS (SELECT 1 FROM game_player_results x
                   WHERE x.game_record_id = r.id AND x.is_retracted = false
                   AND x.participant_id IS NOT NULL AND x.total_earnings IS NULL)
"""
    )
    if bind.dialect.name == "postgresql":
        sql += " AND EXTRACT(YEAR FROM r.played_on) = (SELECT (value->>'season')::integer FROM app_config WHERE name = 'round_identity')"
    else:
        sql += " AND CAST(strftime('%Y', r.played_on) AS INTEGER) = (SELECT json_extract(value, '$.season') FROM app_config WHERE name = 'round_identity')"
    with bind.begin() as conn:
        if bind.dialect.name == "postgresql":
            conn.execute(text(f"CREATE OR REPLACE VIEW canonical_round_results AS {sql}"))
            return
        # SQLite has no CREATE OR REPLACE VIEW. Refresh in the same DDL
        # transaction so an expanded definition never remains silently stale.
        conn.execute(text("DROP VIEW IF EXISTS canonical_round_results"))
        conn.execute(text(f"CREATE VIEW canonical_round_results AS {sql.replace('false', '0')}"))


# Only additive columns at boot. Backfill, old index retirement, and legacy
# foreign-key accounting belong to the explicit offline migration.
ROUND_IDENTITY_COLUMNS = {
    "game_state": ("revision",),
    "game_records": (
        "played_on",
        "raw_date",
        "group",
        "detail_coverage",
        "roster_complete",
        "score_eligible",
        "accepted_revision",
        "is_retracted",
    ),
    "game_player_results": ("participant_id", "is_retracted"),
    "legacy_rounds": ("game_id", "participant_id"),
    "round_comments": ("game_id",),
    "round_reactions": ("game_id",),
    "pending_sheet_syncs": (
        "game_id",
        "source_round_token",
        "source_scope",
        "operation_key",
        "expected_revision",
        "expected_epoch",
        "expected_source_version",
        "payload_fingerprint",
        "contract_fingerprint",
        "payload",
        "lease_owner",
        "lease_expires_at",
        "claim_generation",
        "prewrite",
        "provider_receipt",
        "verified_readback",
    ),
    "notifications": ("delivery_key",),
}


def expand_round_identity_schema(bind) -> None:
    """Expand disposable/restored SQLite without rebuilding any existing table.

    PostgreSQL expansion is handled by the restart-safe SQL migration. SQLite
    cannot relax NOT NULL or remove defaults without a table rebuild; fail
    explicitly so a restored database must be upgraded offline, never erased.
    """
    if bind.dialect.name != "sqlite":
        return
    from sqlalchemy.schema import CreateColumn

    from . import models  # noqa: F401

    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    for table_name in ("game_records", "game_player_results"):
        if table_name not in tables:
            continue
        for column in inspector.get_columns(table_name):
            model_column = Base.metadata.tables[table_name].columns.get(column["name"])
            if model_column is None or not model_column.nullable:
                continue
            if not column["nullable"] or (model_column.default is None and column["default"] is not None):
                raise RuntimeError(
                    f"Round identity requires an offline SQLite upgrade for {table_name}.{column['name']}; "
                    "boot will not rebuild tables or discard data"
                )
    if "round_deliveries" in tables:
        columns = {c["name"]: c for c in inspector.get_columns("round_deliveries")}
        if not columns["recipient_profile_id"]["nullable"] or columns["delivery_key"]["nullable"]:
            raise RuntimeError(
                "Round delivery requires an offline SQLite upgrade; boot will not rebuild evidence tables"
            )
    with bind.begin() as conn:
        for table_name, names in ROUND_IDENTITY_COLUMNS.items():
            if table_name not in tables:
                continue
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            table = Base.metadata.tables[table_name]
            for name in names:
                if name not in existing:
                    ddl = str(CreateColumn(table.c[name]).compile(dialect=bind.dialect))
                    conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN {ddl}'))
        # New nullable keys contain no legacy values; safe without backfill.
        if "pending_sheet_syncs" in tables:
            conn.execute(
                text("CREATE UNIQUE INDEX IF NOT EXISTS uq_sheet_sync_operation ON pending_sheet_syncs(operation_key)")
            )
        if "notifications" in tables:
            conn.execute(
                text("CREATE UNIQUE INDEX IF NOT EXISTS uq_notifications_delivery_key ON notifications(delivery_key)")
            )
        if "game_player_results" in tables:
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_game_result_participant ON game_player_results(game_record_id, participant_id)"
                )
            )


def init_db():
    """Initialize database tables"""
    try:
        # Import all models to ensure they're registered with SQLAlchemy
        from . import models  # noqa: F401

        # Create all tables
        Base.metadata.create_all(bind=engine)
        expand_round_identity_schema(engine)
        # Preserve existing local data when upgrading the group-posting audit field.
        # Production PostgreSQL uses add_member_round_submitter_postgres.sql.
        if engine.dialect.name == "sqlite":
            preference_columns = {column["name"] for column in inspect(engine).get_columns("email_preferences")}
            if "same_day_signups_enabled" not in preference_columns:
                with engine.begin() as connection:
                    connection.execute(
                        text("ALTER TABLE email_preferences ADD COLUMN same_day_signups_enabled INTEGER DEFAULT 0")
                    )
            columns = {column["name"] for column in inspect(engine).get_columns("legacy_rounds")}
            if "submitted_by_profile_id" not in columns:
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            "ALTER TABLE legacy_rounds ADD COLUMN submitted_by_profile_id "
                            "INTEGER REFERENCES player_profiles(id)"
                        )
                    )
        # Round stories and reactions are new tables; create_all covers fresh
        # SQLite. Production PostgreSQL uses add_round_comments_postgres.sql and
        # add_round_reactions_postgres.sql.
        # Legacy remains the default serving authority until accepted activation.
        # View DDL is compatibility, never identity backfill or contraction.
        ensure_legacy_rounds_official_view(engine)
        ensure_canonical_round_results_view(engine)
        logger.info("Database initialized successfully")

        # Test database connection
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
