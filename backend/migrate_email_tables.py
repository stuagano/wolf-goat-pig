"""
Database migration script to add email-related tables and fields
"""

import sqlite3
import sys
import os
from datetime import datetime

def migrate_database():
    """Add email field to PlayerProfile and create EmailPreferences table"""
    
    db_path = "wolf_goat_pig.db"
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if email column exists in player_profiles
        cursor.execute("PRAGMA table_info(player_profiles)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'email' not in columns:
            print("Adding email column to player_profiles table...")
            cursor.execute("""
                ALTER TABLE player_profiles 
                ADD COLUMN email VARCHAR
            """)
            print("✅ Email column added to player_profiles")
        else:
            print("✅ Email column already exists in player_profiles")
        
        # Check if email_preferences table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='email_preferences'
        """)
        
        if not cursor.fetchone():
            print("Creating email_preferences table...")
            cursor.execute("""
                CREATE TABLE email_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_profile_id INTEGER,
                    daily_signups_enabled INTEGER DEFAULT 1,
                    signup_confirmations_enabled INTEGER DEFAULT 1,
                    signup_reminders_enabled INTEGER DEFAULT 1,
                    game_invitations_enabled INTEGER DEFAULT 1,
                    weekly_summary_enabled INTEGER DEFAULT 1,
                    email_frequency VARCHAR DEFAULT 'daily',
                    preferred_notification_time VARCHAR DEFAULT '8:00 AM',
                    created_at VARCHAR,
                    updated_at VARCHAR,
                    FOREIGN KEY (player_profile_id) REFERENCES player_profiles(id)
                )
            """)
            
            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX idx_email_preferences_player_id 
                ON email_preferences(player_profile_id)
            """)
            
            print("✅ email_preferences table created")
            
            # Create default email preferences for existing players
            cursor.execute("SELECT id, name FROM player_profiles")
            players = cursor.fetchall()
            
            now = datetime.now().isoformat()
            for player_id, player_name in players:
                cursor.execute("""
                    INSERT INTO email_preferences 
                    (player_profile_id, created_at, updated_at)
                    VALUES (?, ?, ?)
                """, (player_id, now, now))
                print(f"  Created default email preferences for {player_name}")
            
        else:
            print("✅ email_preferences table already exists")
        
        # Commit changes
        conn.commit()
        print("\n✅ Database migration completed successfully!")
        
        # Show summary
        cursor.execute("SELECT COUNT(*) FROM player_profiles")
        player_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM email_preferences")
        prefs_count = cursor.fetchone()[0]
        
        print(f"\n📊 Summary:")
        print(f"  - Player profiles: {player_count}")
        print(f"  - Email preferences: {prefs_count}")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {str(e)}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)