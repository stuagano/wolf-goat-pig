"""
Migration script to add missing columns to player_statistics table.

This script adds columns that exist in the SQLAlchemy model but are missing
from the production database.

Run this migration to fix the Google Sheets sync error:
  "column player_statistics.ping_pong_count does not exist"

Usage:
  python -m app.migrations.add_missing_statistics_columns

Or via API endpoint:
  POST /admin/run-migration?migration=add_statistics_columns
"""

import logging
from typing import Dict, Any, List, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import ProgrammingError, OperationalError

from ..database import SessionLocal

logger = logging.getLogger(__name__)

# List of columns to add: (column_name, column_type, default_value)
MISSING_COLUMNS: List[Tuple[str, str, str]] = [
    # Special event tracking
    ("ping_pong_count", "INTEGER", "0"),
    ("ping_pong_wins", "INTEGER", "0"),
    ("invisible_aardvark_appearances", "INTEGER", "0"),
    ("invisible_aardvark_wins", "INTEGER", "0"),
    # Specific solo type tracking
    ("duncan_attempts", "INTEGER", "0"),
    ("duncan_wins", "INTEGER", "0"),
    ("tunkarri_attempts", "INTEGER", "0"),
    ("tunkarri_wins", "INTEGER", "0"),
    ("big_dick_attempts", "INTEGER", "0"),
    ("big_dick_wins", "INTEGER", "0"),
    # Score performance tracking
    ("eagles", "INTEGER", "0"),
    ("birdies", "INTEGER", "0"),
    ("pars", "INTEGER", "0"),
    ("bogeys", "INTEGER", "0"),
    ("double_bogeys", "INTEGER", "0"),
    ("worse_than_double", "INTEGER", "0"),
    # Streak tracking
    ("current_win_streak", "INTEGER", "0"),
    ("current_loss_streak", "INTEGER", "0"),
    ("best_win_streak", "INTEGER", "0"),
    ("worst_loss_streak", "INTEGER", "0"),
    # Role tracking
    ("times_as_wolf", "INTEGER", "0"),
    ("times_as_goat", "INTEGER", "0"),
    ("times_as_pig", "INTEGER", "0"),
    ("times_as_aardvark", "INTEGER", "0"),
    # Additional performance fields
    ("favorite_game_mode", "VARCHAR(50)", "NULL"),
    ("preferred_player_count", "INTEGER", "4"),
    ("best_hole_performance", "TEXT", "NULL"),  # JSON stored as text
    ("worst_hole_performance", "TEXT", "NULL"),  # JSON stored as text
    ("performance_trends", "TEXT", "NULL"),  # JSON stored as text
    ("head_to_head_records", "TEXT", "NULL"),  # JSON stored as text
    ("last_updated", "VARCHAR(50)", "NULL"),
    # Additional earnings fields
    ("avg_earnings_per_game", "FLOAT", "0.0"),
    ("win_percentage", "FLOAT", "0.0"),
]


def column_exists(db: Session, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table (works for both PostgreSQL and SQLite)."""
    try:
        # Try PostgreSQL method first
        result = db.execute(
            text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = :table_name AND column_name = :column_name
        """),
            {"table_name": table_name, "column_name": column_name},
        )
        return result.fetchone() is not None
    except (ProgrammingError, OperationalError):
        # Fall back to SQLite method
        try:
            result = db.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in result.fetchall()]
            return column_name in columns
        except Exception as e:
            logger.warning(f"Could not check column existence: {e}")
            return False


def add_column_postgresql(db: Session, table_name: str, column_name: str, column_type: str, default_value: str) -> bool:
    """Add a column to a PostgreSQL table."""
    try:
        # PostgreSQL syntax
        if default_value == "NULL":
            sql = f'ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS "{column_name}" {column_type}'
        else:
            sql = f'ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS "{column_name}" {column_type} DEFAULT {default_value}'

        db.execute(text(sql))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add column {column_name}: {e}")
        return False


def add_column_sqlite(db: Session, table_name: str, column_name: str, column_type: str, default_value: str) -> bool:
    """Add a column to a SQLite table."""
    try:
        # SQLite syntax (doesn't support IF NOT EXISTS for columns)
        if default_value == "NULL":
            sql = f'ALTER TABLE {table_name} ADD COLUMN "{column_name}" {column_type}'
        else:
            sql = f'ALTER TABLE {table_name} ADD COLUMN "{column_name}" {column_type} DEFAULT {default_value}'

        db.execute(text(sql))
        db.commit()
        return True
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            logger.info(f"Column {column_name} already exists")
            return True
        db.rollback()
        logger.error(f"Failed to add column {column_name}: {e}")
        return False


def run_migration(db: Session = None) -> Dict[str, Any]:
    """
    Run the migration to add missing columns to player_statistics table.

    Returns:
        Dict with migration results
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    results = {
        "status": "success",
        "columns_added": [],
        "columns_skipped": [],
        "columns_failed": [],
        "is_postgresql": False,
    }

    try:
        # Detect database type
        try:
            db.execute(text("SELECT version()"))
            is_postgresql = True
            results["is_postgresql"] = True
            logger.info("Detected PostgreSQL database")
        except (ProgrammingError, OperationalError):
            is_postgresql = False
            logger.info("Detected SQLite database")

        table_name = "player_statistics"

        for column_name, column_type, default_value in MISSING_COLUMNS:
            # Check if column already exists
            if column_exists(db, table_name, column_name):
                results["columns_skipped"].append(column_name)
                logger.info(f"Column {column_name} already exists, skipping")
                continue

            # Add the column
            if is_postgresql:
                success = add_column_postgresql(db, table_name, column_name, column_type, default_value)
            else:
                success = add_column_sqlite(db, table_name, column_name, column_type, default_value)

            if success:
                results["columns_added"].append(column_name)
                logger.info(f"Added column {column_name}")
            else:
                results["columns_failed"].append(column_name)

        if results["columns_failed"]:
            results["status"] = "partial"

        logger.info(
            f"Migration complete: {len(results['columns_added'])} added, "
            f"{len(results['columns_skipped'])} skipped, "
            f"{len(results['columns_failed'])} failed"
        )

        return results

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "columns_added": results.get("columns_added", []),
            "columns_failed": results.get("columns_failed", []),
        }
    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_migration()
    print(f"Migration result: {result}")
