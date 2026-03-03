#!/usr/bin/env python3
"""
Fix PostgreSQL sequence for game_state table.

This script resets the id sequence to the correct value after migrations.
"""

import os
from sqlalchemy import create_engine, text

def fix_game_state_sequence():
    """Reset the game_state id sequence to match the current max ID."""

    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False

    # Connect to database
    engine = create_engine(database_url)

    try:
        with engine.connect() as conn:
            # Check current max ID
            result = conn.execute(text("SELECT MAX(id) FROM game_state"))
            max_id = result.scalar()
            print(f"📊 Current max ID in game_state: {max_id}")

            if max_id is None:
                print("✅ Table is empty, no sequence fix needed")
                return True

            # Reset the sequence
            conn.execute(text(f"SELECT setval('game_state_id_seq', {max_id})"))
            conn.commit()

            # Verify the fix
            result = conn.execute(text("SELECT last_value FROM game_state_id_seq"))
            sequence_value = result.scalar()
            print(f"✅ Sequence reset to: {sequence_value}")
            print(f"✅ Next ID will be: {sequence_value + 1}")

            return True

    except Exception as e:
        print(f"❌ Error fixing sequence: {e}")
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    print("🔧 Fixing game_state id sequence...")
    success = fix_game_state_sequence()
    exit(0 if success else 1)
