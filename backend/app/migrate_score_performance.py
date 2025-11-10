#!/usr/bin/env python3
"""
Database Migration Script for Score Performance Metrics

This script adds new columns to the player_statistics table for tracking
score performance (eagles, birdies, pars, bogeys, doubles, etc.)

Usage:
    python -m app.migrate_score_performance
"""

import logging
from sqlalchemy import text
from .database import engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table (supports both SQLite and PostgreSQL)."""
    try:
        with engine.connect() as conn:
            # Detect database type from connection
            dialect_name = conn.dialect.name

            if dialect_name == 'sqlite':
                # SQLite-specific query
                result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                columns = [row[1] for row in result.fetchall()]
                return column_name in columns
            elif dialect_name == 'postgresql':
                # PostgreSQL-specific query
                result = conn.execute(text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = :table_name AND column_name = :column_name
                """), {"table_name": table_name, "column_name": column_name})
                return result.fetchone() is not None
            else:
                logger.warning(f"Unknown database dialect: {dialect_name}")
                return False
    except Exception as e:
        logger.error(f"Error checking if column {column_name} exists: {e}")
        return False

def add_score_performance_columns():
    """Add score performance columns to player_statistics table."""
    logger.info("Starting score performance metrics migration...")

    columns_to_add = [
        ("eagles", "INTEGER DEFAULT 0"),
        ("birdies", "INTEGER DEFAULT 0"),
        ("pars", "INTEGER DEFAULT 0"),
        ("bogeys", "INTEGER DEFAULT 0"),
        ("double_bogeys", "INTEGER DEFAULT 0"),
        ("worse_than_double", "INTEGER DEFAULT 0"),
    ]

    try:
        with engine.connect() as conn:
            for column_name, column_type in columns_to_add:
                if check_column_exists(engine, "player_statistics", column_name):
                    logger.info(f"Column '{column_name}' already exists, skipping...")
                    continue

                logger.info(f"Adding column '{column_name}' to player_statistics table...")
                conn.execute(text(
                    f"ALTER TABLE player_statistics ADD COLUMN {column_name} {column_type}"
                ))
                logger.info(f"✓ Added column '{column_name}'")

            conn.commit()

        logger.info("Score performance metrics migration completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_migration():
    """Verify that the migration was successful."""
    try:
        logger.info("Verifying migration...")

        columns_to_check = [
            "eagles", "birdies", "pars", "bogeys", "double_bogeys", "worse_than_double"
        ]

        all_exist = True
        for column_name in columns_to_check:
            exists = check_column_exists(engine, "player_statistics", column_name)
            status = "✓" if exists else "✗"
            logger.info(f"{status} Column '{column_name}' exists: {exists}")
            if not exists:
                all_exist = False

        if all_exist:
            logger.info("✅ Migration verification passed!")
        else:
            logger.error("❌ Migration verification failed - some columns are missing")

        return all_exist

    except Exception as e:
        logger.error(f"Error during verification: {e}")
        return False

def main():
    """Main migration function."""
    try:
        logger.info("=" * 60)
        logger.info("Score Performance Metrics Migration")
        logger.info("=" * 60)

        success = add_score_performance_columns()

        if success:
            success = verify_migration()

        if success:
            logger.info("✅ Migration completed successfully!")
            return True
        else:
            logger.error("❌ Migration failed!")
            return False

    except Exception as e:
        logger.error(f"Fatal error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
