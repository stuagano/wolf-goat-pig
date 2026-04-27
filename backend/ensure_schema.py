#!/usr/bin/env python3
"""
Database Schema Sync

Ensures all schema definitions are applied on startup.
Each .sql file is idempotent (uses IF NOT EXISTS / safely skips duplicates).
Auto-discovers files from backend/schema/ by database type.
Supports both PostgreSQL (production) and SQLite (development).
"""

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


def ensure_schema():
    """Apply all schema definitions. Idempotent — safe to run on every startup."""
    schema_dir = Path(__file__).parent / "schema"

    if not schema_dir.exists():
        print("No schema directory found - skipping")
        return True

    db_type = get_database_type()
    print(f"Database type: {db_type}")

    # Auto-discover schema files by database type.
    # PostgreSQL files end with _postgres.sql; SQLite uses the rest.
    all_sql = sorted(f.name for f in schema_dir.glob("*.sql"))

    if db_type == "postgresql":
        schema_files = [f for f in all_sql if f.endswith("_postgres.sql")]
    elif db_type == "sqlite":
        schema_files = [f for f in all_sql if not f.endswith("_postgres.sql")]
    else:
        print(f"Unknown database type: {db_type}")
        return False

    print(f"Found {len(schema_files)} schema file(s) to apply")

    connection = engine.connect()
    trans = connection.begin()

    try:
        for filename in schema_files:
            filepath = schema_dir / filename

            if not filepath.exists():
                print(f"  Schema file not found: {filename} - skipping")
                continue

            print(f"  Applying: {filename}")

            with open(filepath, "r") as f:
                sql = f.read()

                # Note: don't filter out segments that start with '--'. A leading
                # comment is part of the next statement, e.g. `-- intro\nALTER ...`,
                # and stripping it here would silently drop the entire ALTER.
                # PostgreSQL parses leading comments natively; let it.
                statements = [s.strip() for s in sql.split(";") if s.strip()]

                for statement in statements:
                    if statement:
                        try:
                            connection.execute(text(statement))
                        except Exception as e:
                            error_msg = str(e).lower()
                            if any(
                                phrase in error_msg
                                for phrase in [
                                    "already exists",
                                    "duplicate column",
                                    "duplicate key",
                                    "column already exists",
                                    'near "exists"',
                                ]
                            ):
                                print(f"    Skipping (already applied): {statement[:50]}...")
                            else:
                                print(f"    Error: {e}")
                                print(f"    Statement: {statement[:100]}...")
                                raise

            print(f"    Done: {filename}")

        trans.commit()
        print("Schema sync complete")
        return True

    except Exception as e:
        trans.rollback()
        print(f"Schema sync failed: {e}")
        return False

    finally:
        connection.close()


if __name__ == "__main__":
    print("Ensuring database schema...")
    success = ensure_schema()
    sys.exit(0 if success else 1)
