import logging
import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

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
is_postgresql = DATABASE_URL and (DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://"))

if is_postgresql and DATABASE_URL:
    # Production database (PostgreSQL)
    if DATABASE_URL.startswith("postgres://"):
        # Fix for newer SQLAlchemy versions
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # Pool sizing is env-tunable. Defaults match the Render free tier; Cloud SQL
    # (Phase 2) can afford a larger pool — bump DB_POOL_SIZE/DB_MAX_OVERFLOW via
    # env without a code change. The Cloud SQL Auth Proxy / Unix-socket form
    # (postgresql://user:pass@/db?host=/cloudsql/CONN) works unchanged here:
    # it stays on the postgresql:// branch and psycopg2 reads host from the query.
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=_int_env("DB_POOL_RECYCLE", 300),  # Recycle connections every 5 minutes
        pool_size=_int_env("DB_POOL_SIZE", 5),  # Maximum pool size (Render free tier default)
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
    except Exception as e:
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
    Safe to call on every boot: ``CREATE OR REPLACE`` / ``CREATE IF NOT EXISTS``.
    Skips when the ``status`` column is missing (pre-attestation schema).
    """
    dialect = bind.dialect.name
    with bind.begin() as conn:
        if dialect == "postgresql":
            has_status = conn.execute(
                text(
                    "SELECT 1 FROM information_schema.columns "
                    "WHERE table_name = 'legacy_rounds' AND column_name = 'status'"
                )
            ).first()
            if not has_status:
                logger.warning("Skipping legacy_rounds_official view — legacy_rounds.status column missing")
                return
            conn.execute(
                text(
                    "CREATE OR REPLACE VIEW legacy_rounds_official AS "
                    "SELECT * FROM legacy_rounds WHERE status <> 'pending'"
                )
            )
            return

        # SQLite (dev/test)
        conn.execute(
            text(
                "CREATE VIEW IF NOT EXISTS legacy_rounds_official AS "
                "SELECT * FROM legacy_rounds WHERE status <> 'pending'"
            )
        )


def init_db():
    """Initialize database tables"""
    try:
        # Import all models to ensure they're registered with SQLAlchemy
        from . import models  # noqa: F401

        # Create all tables
        Base.metadata.create_all(bind=engine)
        # Filtered view used by Commissioner SQL reads (SQLite dev; Postgres gets
        # it from the attestation migration).
        ensure_legacy_rounds_official_view(engine)
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
