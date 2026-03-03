import sqlite3
import traceback

def migrate():
    print("Starting migration...")
    try:
        db_path = 'wolf_goat_pig.db'
        print(f"Connecting to database at: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("Database connection successful.")

        # Get existing columns
        print("Fetching existing columns from player_profiles table...")
        cursor.execute("PRAGMA table_info(player_profiles)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Existing columns: {columns}")

        # Columns to add: column_name -> column_type
        cols_to_add = {
            'ghin_id': 'VARCHAR',
            'ghin_last_updated': 'VARCHAR',
            'is_ai': 'BOOLEAN',
            'playing_style': 'VARCHAR',
            'description': 'VARCHAR',
            'personality_traits': 'TEXT', # JSON stored as TEXT in SQLite
            'strengths': 'TEXT',
            'weaknesses': 'TEXT',
            'created_at': 'VARCHAR',
            'updated_at': 'VARCHAR'
        }

        for col, col_type in cols_to_add.items():
            if col not in columns:
                print(f"Adding {col} column to player_profiles...")
                cursor.execute(f"ALTER TABLE player_profiles ADD COLUMN {col} {col_type}")
                print(f"Successfully added {col} column.")
        
        if 'created_date' in columns:
            print("Dropping created_date column...")
            # SQLite doesn't support dropping columns directly, so we have to do it the hard way.
            # 1. Create a new table with the correct schema
            cursor.execute("""
            CREATE TABLE player_profiles_new (
                id INTEGER NOT NULL, 
                name VARCHAR, 
                handicap FLOAT, 
                avatar_url VARCHAR, 
                last_played VARCHAR, 
                preferences TEXT, 
                is_active INTEGER, 
                ghin_id VARCHAR, 
                ghin_last_updated VARCHAR, 
                is_ai BOOLEAN, 
                playing_style VARCHAR, 
                description VARCHAR, 
                personality_traits TEXT, 
                strengths TEXT, 
                weaknesses TEXT, 
                created_at VARCHAR, 
                updated_at VARCHAR, 
                PRIMARY KEY (id)
            )
            """)
            # 2. Copy the data from the old table to the new table
            cursor.execute("""
            INSERT INTO player_profiles_new (id, name, handicap, avatar_url, last_played, preferences, is_active, ghin_id, ghin_last_updated, is_ai, playing_style, description, personality_traits, strengths, weaknesses, created_at, updated_at)
            SELECT id, name, handicap, avatar_url, last_played, preferences, is_active, ghin_id, ghin_last_updated, is_ai, playing_style, description, personality_traits, strengths, weaknesses, created_date, updated_at FROM player_profiles
            """)
            # 3. Drop the old table
            cursor.execute("DROP TABLE player_profiles")
            # 4. Rename the new table to the old table's name
            cursor.execute("ALTER TABLE player_profiles_new RENAME TO player_profiles")
            print("Successfully dropped created_date column and recreated table.")


        conn.commit()
        conn.close()
        print("Migration complete.")
    except Exception as e:
        print("An error occurred during migration:")
        print(traceback.format_exc())

if __name__ == "__main__":
    migrate()
