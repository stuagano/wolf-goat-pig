# Database Schema

Idempotent SQL files that define the database schema. Applied automatically on
every startup via `ensure_schema.py`. Safe to re-run — uses `IF NOT EXISTS` and
skips "already exists" errors.

## How it works

1. `render-startup.py` calls `ensure_schema.py` before starting the server
2. `ensure_schema.py` auto-discovers `.sql` files from this directory
3. PostgreSQL: runs `*_postgres.sql` files. SQLite: runs all other `.sql` files
4. Files are sorted alphabetically for deterministic order

## Adding a new schema change

1. Update `app/models.py` with the new columns/tables
2. Add a `.sql` file here (and a `_postgres.sql` variant if syntax differs)
3. Use `IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS` for idempotency
4. That's it — no registration step needed
