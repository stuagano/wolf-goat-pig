#!/usr/bin/env python3
"""
Direct database migration to fix game_state schema.

This script adds the missing game_id column and ensures the schema matches
the GameStateModel definition. It can be run independently or as part of startup.
"""

import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError, ProgrammingError


def get_database_url():
    """Get the database URL from environment or use default."""
    db_url = os.getenv('DATABASE_URL', '')

    # Fix postgres:// to postgresql:// if needed
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    # If no DATABASE_URL, use SQLite
    if not db_url:
        db_url = "sqlite:///./wolf_goat_pig.db"

    return db_url


def fix_game_state_schema():
    """Add missing columns to game_state table."""
    database_url = get_database_url()
    is_postgresql = 'postgresql://' in database_url
    is_sqlite = 'sqlite://' in database_url

    print("=" * 70)
    print("Game State Schema Fix")
    print("=" * 70)
    print(f"Database type: {'PostgreSQL' if is_postgresql else 'SQLite'}")
    print(f"Database URL: {database_url.split('@')[0]}@..." if '@' in database_url else database_url[:50])
    print()

    try:
        # Create engine
        engine = create_engine(database_url)

        with engine.connect() as conn:
            # Check if game_state table exists
            inspector = inspect(engine)

            if 'game_state' not in inspector.get_table_names():
                print("⚠️  game_state table does not exist yet")
                print("    It will be created when the application initializes the database.")
                return True

            # Get existing columns
            existing_columns = [col['name'] for col in inspector.get_columns('game_state')]
            print(f"Existing columns: {', '.join(existing_columns)}")
            print()

            migrations_applied = []

            # Migration 1: Add game_id column
            if 'game_id' not in existing_columns:
                print("🔧 Adding game_id column...")
                try:
                    conn.execute(text("ALTER TABLE game_state ADD COLUMN game_id VARCHAR"))
                    conn.commit()
                    print("  ✅ Added game_id column")

                    # Create unique index
                    print("🔧 Creating unique index on game_id...")
                    if is_postgresql:
                        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_game_state_game_id ON game_state(game_id)"))
                    else:
                        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_game_state_game_id ON game_state(game_id)"))
                    conn.commit()
                    print("  ✅ Created unique index")

                    # Update existing records with default game_id values
                    print("🔧 Updating existing records...")
                    conn.execute(text("UPDATE game_state SET game_id = 'legacy-game-' || CAST(id AS VARCHAR) WHERE game_id IS NULL"))
                    conn.commit()
                    print("  ✅ Updated existing records")

                    migrations_applied.append("game_id")
                except Exception as e:
                    print(f"  ❌ Failed to add game_id column: {e}")
                    conn.rollback()
                    raise
            else:
                print("✓ game_id column already exists")

            # Migration 2: Add created_at column
            if 'created_at' not in existing_columns:
                print("🔧 Adding created_at column...")
                try:
                    conn.execute(text("ALTER TABLE game_state ADD COLUMN created_at VARCHAR"))
                    if is_postgresql:
                        conn.execute(text("UPDATE game_state SET created_at = NOW()::text WHERE created_at IS NULL"))
                    else:
                        conn.execute(text("UPDATE game_state SET created_at = datetime('now') WHERE created_at IS NULL"))
                    conn.commit()
                    print("  ✅ Added created_at column")
                    migrations_applied.append("created_at")
                except Exception as e:
                    print(f"  ❌ Failed to add created_at column: {e}")
                    conn.rollback()
                    raise
            else:
                print("✓ created_at column already exists")

            # Migration 3: Add updated_at column
            if 'updated_at' not in existing_columns:
                print("🔧 Adding updated_at column...")
                try:
                    conn.execute(text("ALTER TABLE game_state ADD COLUMN updated_at VARCHAR"))
                    if is_postgresql:
                        conn.execute(text("UPDATE game_state SET updated_at = NOW()::text WHERE updated_at IS NULL"))
                    else:
                        conn.execute(text("UPDATE game_state SET updated_at = datetime('now') WHERE updated_at IS NULL"))
                    conn.commit()
                    print("  ✅ Added updated_at column")
                    migrations_applied.append("updated_at")
                except Exception as e:
                    print(f"  ❌ Failed to add updated_at column: {e}")
                    conn.rollback()
                    raise
            else:
                print("✓ updated_at column already exists")

            print()

            if migrations_applied:
                print(f"✅ Successfully applied {len(migrations_applied)} migration(s): {', '.join(migrations_applied)}")
            else:
                print("✅ Schema is already up-to-date - no migrations needed")

            # Verify final schema
            print()
            print("Final schema:")
            final_columns = [col['name'] for col in inspector.get_columns('game_state')]
            for col in final_columns:
                print(f"  • {col}")

            print()
            print("=" * 70)
            print("✅ Schema fix completed successfully!")
            print("=" * 70)

            return True

    except OperationalError as e:
        print(f"❌ Database connection error: {e}")
        print()
        print("Possible causes:")
        print("  1. Database server is not running")
        print("  2. DATABASE_URL is incorrect")
        print("  3. Database credentials are invalid")
        return False

    except ProgrammingError as e:
        print(f"❌ Database programming error: {e}")
        print()
        print("Possible causes:")
        print("  1. Table structure is different than expected")
        print("  2. SQL syntax error")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = fix_game_state_schema()
    sys.exit(0 if success else 1)
