#!/usr/bin/env python3
"""
Database migration script to add new columns for AI players and fix schema issues.
"""

import sqlite3
import json
from datetime import datetime

def migrate_database():
    """Add missing columns to player_profiles table."""
    
    conn = sqlite3.connect('wolf_goat_pig.db')
    cursor = conn.cursor()
    
    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(player_profiles)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        print(f"Existing columns: {existing_columns}")
        
        # Add missing columns one by one
        columns_to_add = [
            ("is_ai", "INTEGER", "0"),
            ("playing_style", "TEXT", "NULL"),
            ("description", "TEXT", "NULL"),
            ("personality_traits", "TEXT", "NULL"),
            ("strengths", "TEXT", "NULL"),
            ("weaknesses", "TEXT", "NULL"),
            ("updated_at", "TEXT", "NULL")
        ]
        
        for col_name, col_type, default_val in columns_to_add:
            if col_name not in existing_columns:
                try:
                    if default_val == "NULL":
                        cursor.execute(f"ALTER TABLE player_profiles ADD COLUMN {col_name} {col_type}")
                    else:
                        cursor.execute(f"ALTER TABLE player_profiles ADD COLUMN {col_name} {col_type} DEFAULT {default_val}")
                    print(f"✅ Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"⚠️  Column {col_name} already exists")
                    else:
                        raise
            else:
                print(f"⚠️  Column {col_name} already exists")
        
        # Rename created_date to created_at if needed
        if "created_date" in existing_columns and "created_at" not in existing_columns:
            # SQLite doesn't support direct column rename, need to recreate table
            print("Renaming created_date to created_at...")
            
            # Get the current table schema
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='player_profiles'")
            create_sql = cursor.fetchone()[0]
            
            # Simple column rename for SQLite
            cursor.execute("""
                CREATE TABLE player_profiles_new AS 
                SELECT 
                    id,
                    name,
                    handicap,
                    ghin_id,
                    ghin_last_updated,
                    avatar_url,
                    created_date as created_at,
                    last_played,
                    preferences,
                    is_active,
                    COALESCE(is_ai, 0) as is_ai,
                    playing_style,
                    description,
                    personality_traits,
                    strengths,
                    weaknesses,
                    updated_at
                FROM player_profiles
            """)
            
            cursor.execute("DROP TABLE player_profiles")
            cursor.execute("ALTER TABLE player_profiles_new RENAME TO player_profiles")
            print("✅ Renamed created_date to created_at")
        
        # Commit changes
        conn.commit()
        print("\n✅ Database migration completed successfully!")
        
        # Verify the schema
        cursor.execute("PRAGMA table_info(player_profiles)")
        final_columns = cursor.fetchall()
        print("\nFinal schema:")
        for col in final_columns:
            print(f"  - {col[1]} ({col[2]})")
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting database migration...")
    migrate_database()