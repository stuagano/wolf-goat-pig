#!/usr/bin/env python3
"""
Database Migration Runner
Automatically runs SQL migrations on the database.
Supports both PostgreSQL (production) and SQLite (development).
"""

import os
import sys
from pathlib import Path

from sqlalchemy import text

from app.database import engine


def get_database_type():
    """Determine if we're using PostgreSQL or SQLite."""
    db_url = str(engine.url)
    if "postgresql" in db_url or "postgres" in db_url:
        return "postgresql"
    elif "sqlite" in db_url:
        return "sqlite"
    else:
        return "unknown"


def run_migrations():
    """Run all pending migrations."""
    migrations_dir = Path(__file__).parent / "migrations"

    if not migrations_dir.exists():
        print("✅ No migrations directory found - skipping")
        return True

    db_type = get_database_type()
    print(f"📊 Database type: {db_type}")

    # Auto-discover migration files by database type.
    # PostgreSQL migrations end with _postgres.sql; SQLite uses the rest.
    all_sql = sorted(f.name for f in migrations_dir.glob("*.sql"))

    if db_type == "postgresql":
        migration_files = [f for f in all_sql if f.endswith("_postgres.sql")]
    elif db_type == "sqlite":
        migration_files = [f for f in all_sql if not f.endswith("_postgres.sql")]
    else:
        print(f"❌ Unknown database type: {db_type}")
        return False

    print(f"📋 Found {len(migration_files)} migration(s) to run")

    # Run each migration
    connection = engine.connect()
    trans = connection.begin()

    try:
        for filename in migration_files:
            filepath = migrations_dir / filename

            if not filepath.exists():
                print(f"⚠️  Migration file not found: {filename} - skipping")
                continue

            print(f"🔄 Running migration: {filename}")

            # Read and execute migration
            with open(filepath, "r") as f:
                sql = f.read()

                # Split on semicolons and execute each statement
                statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]

                for statement in statements:
                    if statement:
                        try:
                            connection.execute(text(statement))
                        except Exception as e:
                            # Check if error is "already exists" which we can safely ignore
                            error_msg = str(e).lower()
                            if any(
                                phrase in error_msg
                                for phrase in [
                                    "already exists",
                                    "duplicate column",
                                    "duplicate key",
                                    "column already exists",
                                    'near "exists"',  # SQLite doesn't support IF NOT EXISTS with ALTER TABLE ADD COLUMN
                                ]
                            ):
                                print(f"   ℹ️  Skipping (already applied): {statement[:50]}...")
                            else:
                                print(f"   ❌ Error: {e}")
                                print(f"   Statement: {statement[:100]}...")
                                raise

            print(f"   ✅ Completed: {filename}")

        trans.commit()
        print("✅ All migrations completed successfully")
        return True

    except Exception as e:
        trans.rollback()
        print(f"❌ Migration failed: {e}")
        return False

    finally:
        connection.close()


if __name__ == "__main__":
    print("🚀 Running database migrations...")
    success = run_migrations()
    sys.exit(0 if success else 1)
