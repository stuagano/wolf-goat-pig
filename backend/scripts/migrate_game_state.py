#!/usr/bin/env python3
"""
Migration script to add game_id column to game_state table.

This script handles both PostgreSQL and SQLite databases and adds the necessary
columns for supporting multiple games with unique identifiers.
"""

import os
import sys
from datetime import datetime


def migrate_postgresql():
    """Migrate PostgreSQL database."""
    import psycopg2

    database_url = os.getenv('DATABASE_URL', '')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set for PostgreSQL migration")

    # Fix postgres:// to postgresql:// if needed
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    print(f"Connecting to PostgreSQL database...")
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    try:
        # Check if game_id column exists
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='game_state' AND column_name='game_id'
        """)

        game_id_exists = cursor.fetchone() is not None

        if not game_id_exists:
            print("Adding game_id column to game_state table...")

            # Add game_id column
            cursor.execute("ALTER TABLE game_state ADD COLUMN game_id VARCHAR")
            print("✅ Added game_id column")

            # Create unique index on game_id
            cursor.execute("CREATE UNIQUE INDEX idx_game_state_game_id ON game_state(game_id)")
            print("✅ Created unique index on game_id")

            # Update existing records to have a game_id
            cursor.execute("UPDATE game_state SET game_id = 'legacy-game-' || id WHERE game_id IS NULL")
            print("✅ Updated existing records with game_id")
        else:
            print("⚠️  game_id column already exists")

        # Check if created_at column exists
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='game_state' AND column_name='created_at'
        """)

        created_at_exists = cursor.fetchone() is not None

        if not created_at_exists:
            print("Adding created_at column to game_state table...")
            cursor.execute("ALTER TABLE game_state ADD COLUMN created_at VARCHAR")
            cursor.execute("UPDATE game_state SET created_at = NOW() WHERE created_at IS NULL")
            print("✅ Added created_at column")
        else:
            print("⚠️  created_at column already exists")

        # Check if updated_at column exists
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='game_state' AND column_name='updated_at'
        """)

        updated_at_exists = cursor.fetchone() is not None

        if not updated_at_exists:
            print("Adding updated_at column to game_state table...")
            cursor.execute("ALTER TABLE game_state ADD COLUMN updated_at VARCHAR")
            cursor.execute("UPDATE game_state SET updated_at = NOW() WHERE updated_at IS NULL")
            print("✅ Added updated_at column")
        else:
            print("⚠️  updated_at column already exists")

        # Commit changes
        conn.commit()
        print("\n✅ PostgreSQL migration completed successfully!")

    except Exception as e:
        print(f"❌ Error during PostgreSQL migration: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def migrate_sqlite():
    """Migrate SQLite database."""
    import sqlite3

    db_path = 'wolf_goat_pig.db'
    print(f"Connecting to SQLite database at {db_path}...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(game_state)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        print(f"Existing columns: {existing_columns}")

        # Add game_id column if it doesn't exist
        if 'game_id' not in existing_columns:
            print("Adding game_id column to game_state table...")
            cursor.execute("ALTER TABLE game_state ADD COLUMN game_id VARCHAR")
            print("✅ Added game_id column")

            # Create unique index on game_id
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_game_state_game_id ON game_state(game_id)")
            print("✅ Created unique index on game_id")

            # Update existing records
            cursor.execute("UPDATE game_state SET game_id = 'legacy-game-' || id WHERE game_id IS NULL")
            print("✅ Updated existing records with game_id")
        else:
            print("⚠️  game_id column already exists")

        # Add created_at column if it doesn't exist
        if 'created_at' not in existing_columns:
            print("Adding created_at column to game_state table...")
            cursor.execute("ALTER TABLE game_state ADD COLUMN created_at VARCHAR")
            cursor.execute("UPDATE game_state SET created_at = datetime('now') WHERE created_at IS NULL")
            print("✅ Added created_at column")
        else:
            print("⚠️  created_at column already exists")

        # Add updated_at column if it doesn't exist
        if 'updated_at' not in existing_columns:
            print("Adding updated_at column to game_state table...")
            cursor.execute("ALTER TABLE game_state ADD COLUMN updated_at VARCHAR")
            cursor.execute("UPDATE game_state SET updated_at = datetime('now') WHERE updated_at IS NULL")
            print("✅ Added updated_at column")
        else:
            print("⚠️  updated_at column already exists")

        # Commit changes
        conn.commit()
        print("\n✅ SQLite migration completed successfully!")

        # Verify the schema
        cursor.execute("PRAGMA table_info(game_state)")
        final_columns = cursor.fetchall()
        print("\nFinal schema:")
        for col in final_columns:
            print(f"  - {col[1]} ({col[2]})")

    except Exception as e:
        print(f"❌ Error during SQLite migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    """Run the appropriate migration based on DATABASE_URL."""
    database_url = os.getenv('DATABASE_URL', '')

    print("=" * 60)
    print("Game State Table Migration")
    print("=" * 60)
    print()

    if database_url and ('postgresql://' in database_url or 'postgres://' in database_url):
        print("Detected PostgreSQL database")
        try:
            import psycopg2
        except ImportError:
            print("❌ psycopg2 is not installed. Install with: pip install psycopg2-binary")
            sys.exit(1)

        migrate_postgresql()
    else:
        print("Detected SQLite database (or DATABASE_URL not set)")
        migrate_sqlite()

    print()
    print("=" * 60)
    print("Migration Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
