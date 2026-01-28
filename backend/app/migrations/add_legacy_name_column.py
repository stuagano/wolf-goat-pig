"""Migration to add legacy_name column to player_profiles table.

This column stores the player's name in the legacy tee sheet system (thousand-cranes.com).
"""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def check_column_exists(db: Session, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    try:
        # Works for PostgreSQL
        result = db.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = :table AND column_name = :column
            """),
            {"table": table, "column": column},
        )
        return result.fetchone() is not None
    except Exception as e:
        logger.warning(f"Error checking column existence: {e}")
        return False


def run_migration(db: Session) -> dict:
    """Add legacy_name column to player_profiles if it doesn't exist."""
    results = {"migration": "add_legacy_name_column", "changes": [], "errors": []}

    try:
        # Check if column already exists
        if check_column_exists(db, "player_profiles", "legacy_name"):
            results["changes"].append("legacy_name column already exists - skipping")
            return results

        # Add the column
        db.execute(
            text("""
            ALTER TABLE player_profiles
            ADD COLUMN legacy_name VARCHAR(255) NULL
        """)
        )

        # Add index for faster lookups
        db.execute(
            text("""
            CREATE INDEX IF NOT EXISTS ix_player_profiles_legacy_name
            ON player_profiles (legacy_name)
        """)
        )

        db.commit()
        results["changes"].append("Added legacy_name column to player_profiles")
        results["changes"].append("Created index ix_player_profiles_legacy_name")
        logger.info("Successfully added legacy_name column to player_profiles")

    except Exception as e:
        db.rollback()
        error_msg = f"Failed to add legacy_name column: {str(e)}"
        results["errors"].append(error_msg)
        logger.error(error_msg)

    return results


def rollback_migration(db: Session) -> dict:
    """Remove legacy_name column from player_profiles."""
    results = {"migration": "add_legacy_name_column (rollback)", "changes": [], "errors": []}

    try:
        # Drop index first
        db.execute(
            text("""
            DROP INDEX IF EXISTS ix_player_profiles_legacy_name
        """)
        )

        # Drop column
        db.execute(
            text("""
            ALTER TABLE player_profiles
            DROP COLUMN IF EXISTS legacy_name
        """)
        )

        db.commit()
        results["changes"].append("Dropped legacy_name column and index")

    except Exception as e:
        db.rollback()
        error_msg = f"Failed to rollback: {str(e)}"
        results["errors"].append(error_msg)
        logger.error(error_msg)

    return results
