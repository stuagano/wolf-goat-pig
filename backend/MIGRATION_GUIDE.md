# Database Migration Guide

## Overview

The Wolf-Goat-Pig application includes automatic database migrations that run on startup. This guide explains how migrations work and how to run them manually if needed.

## Automatic Migrations

Migrations run automatically when the FastAPI application starts up. The startup sequence is:

1. Initialize database tables (create tables if they don't exist)
2. Run migrations to add any missing columns to existing tables
3. Verify schema is correct
4. Continue with application startup

### What Gets Migrated

The current migrations add the following columns to the `game_state` table if they don't exist:

- `game_id` (VARCHAR, unique, indexed) - Unique identifier for each game
- `created_at` (VARCHAR) - Timestamp when the game was created
- `updated_at` (VARCHAR) - Timestamp when the game was last updated

## Manual Migration

If you need to run migrations manually (e.g., if the application isn't starting or you need to verify schema changes), you can use the standalone migration script:

### Option 1: Using the fix_game_state_schema.py script

```bash
cd backend
python fix_game_state_schema.py
```

This script:
- Detects the database type (PostgreSQL or SQLite)
- Checks for missing columns
- Adds missing columns if needed
- Updates existing records with default values
- Verifies the final schema

### Option 2: Using the startup.py script

```bash
cd backend
python -c "import asyncio; from startup import BootstrapManager; asyncio.run(BootstrapManager().initialize_database())"
```

### Option 3: Manual SQL (for advanced users)

If you have direct access to the database, you can run these SQL commands:

#### For PostgreSQL:

```sql
-- Add game_id column
ALTER TABLE game_state ADD COLUMN game_id VARCHAR;
CREATE UNIQUE INDEX IF NOT EXISTS idx_game_state_game_id ON game_state(game_id);
UPDATE game_state SET game_id = 'legacy-game-' || CAST(id AS VARCHAR) WHERE game_id IS NULL;

-- Add created_at column
ALTER TABLE game_state ADD COLUMN created_at VARCHAR;
UPDATE game_state SET created_at = NOW()::text WHERE created_at IS NULL;

-- Add updated_at column
ALTER TABLE game_state ADD COLUMN updated_at VARCHAR;
UPDATE game_state SET updated_at = NOW()::text WHERE updated_at IS NULL;
```

#### For SQLite:

```sql
-- Add game_id column
ALTER TABLE game_state ADD COLUMN game_id VARCHAR;
CREATE UNIQUE INDEX IF NOT EXISTS idx_game_state_game_id ON game_state(game_id);
UPDATE game_state SET game_id = 'legacy-game-' || CAST(id AS VARCHAR) WHERE game_id IS NULL;

-- Add created_at column
ALTER TABLE game_state ADD COLUMN created_at VARCHAR;
UPDATE game_state SET created_at = datetime('now') WHERE created_at IS NULL;

-- Add updated_at column
ALTER TABLE game_state ADD COLUMN updated_at VARCHAR;
UPDATE game_state SET updated_at = datetime('now') WHERE updated_at IS NULL;
```

## Verifying Schema

To verify that the schema is correct:

### Using Python:

```python
from sqlalchemy import inspect
from app.database import engine

inspector = inspect(engine)
columns = [col['name'] for col in inspector.get_columns('game_state')]
print(f"game_state columns: {columns}")
```

Expected columns should include: `id`, `game_id`, `join_code`, `creator_user_id`, `game_status`, `state`, `created_at`, `updated_at`

### Using SQL:

#### PostgreSQL:
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'game_state'
ORDER BY ordinal_position;
```

#### SQLite:
```sql
PRAGMA table_info(game_state);
```

## Troubleshooting

### Error: "column game_state.game_id does not exist"

This error occurs when:
1. The database schema is outdated
2. Migrations haven't run yet
3. Migrations failed during startup

**Solution:**
1. Restart the application to trigger automatic migrations
2. If that doesn't work, run the manual migration script: `python backend/fix_game_state_schema.py`

### Error: "table game_state does not exist"

This error occurs when the database hasn't been initialized yet.

**Solution:**
1. Ensure the DATABASE_URL environment variable is set correctly
2. Start the application normally - it will create all tables automatically

### Migrations Not Running on Startup

Check the application logs for migration messages. You should see:
- "🔄 Running database migrations..."
- "Missing columns detected: ..." (if migrations are needed)
- "✅ Successfully applied X migration(s)" (if migrations ran)
- "✅ Schema is up-to-date - no migrations needed" (if no migrations needed)

If you don't see these messages:
1. Check that the `startup()` function in `main.py` is being called
2. Verify the database connection is working
3. Check for any errors in the startup logs

## Database Environment Variables

The application uses these environment variables for database configuration:

- `DATABASE_URL` - Full database connection URL
  - PostgreSQL format: `postgresql://user:password@host:port/dbname`
  - SQLite format: `sqlite:///./wolf_goat_pig.db` (or omit for default)

- `POSTGRES_DB` - PostgreSQL database name (for Docker)
- `POSTGRES_USER` - PostgreSQL username (for Docker)
- `POSTGRES_PASSWORD` - PostgreSQL password (for Docker)

## Related Files

- `backend/app/main.py` - FastAPI startup handler (lines 296-367)
- `backend/startup.py` - Bootstrap manager and migration utilities (lines 360-451)
- `backend/fix_game_state_schema.py` - Standalone migration script
- `backend/app/models.py` - Database model definitions (GameStateModel)
- `backend/migrate_game_state.py` - Legacy migration script (deprecated, use fix_game_state_schema.py instead)
