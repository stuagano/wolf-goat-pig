# Database Migrations

This directory contains SQL migration files for the Wolf Goat Pig database schema.

## Running Migrations

### Production (PostgreSQL on Render.com)

1. **Connect to production database:**
   ```bash
   # Get DATABASE_URL from Render.com dashboard environment variables
   psql $DATABASE_URL
   ```

2. **Run migrations:**
   ```sql
   \i backend/migrations/add_game_id_to_game_state.sql
   \i backend/migrations/add_join_codes_postgres.sql
   ```

   Or copy-paste the SQL directly into the psql prompt.

### Local Development (SQLite)

Migrations run automatically when the backend starts via:
1. `Base.metadata.create_all()` - Creates new tables
2. `startup.py::run_migrations()` - Adds missing columns to existing tables

For manual migration:
```bash
cd backend
python3 -c "from app.database import engine, Base; from app import models; Base.metadata.create_all(bind=engine)"
```

## Migration Files

- `add_game_id_to_game_state.sql` - Adds `game_id` column to `game_state` table
- `add_join_codes_and_player_linking.sql` - SQLite version (for local dev)
- `add_join_codes_postgres.sql` - PostgreSQL version (for production)
- `add_tee_order_to_game_players.sql` - Adds `tee_order` column to `game_players` table (PostgreSQL)

## Creating New Migrations

1. Make changes to `app/models.py`
2. Create a new SQL file in this directory
3. Add both SQLite and PostgreSQL versions if syntax differs
4. Update this README with the new migration
5. Document migration in commit message

## Notes

- Production uses PostgreSQL (`SERIAL` for auto-increment)
- Local dev uses SQLite (`AUTOINCREMENT` for auto-increment)
- Always use `IF NOT EXISTS` and `ADD COLUMN IF NOT EXISTS` for idempotency
