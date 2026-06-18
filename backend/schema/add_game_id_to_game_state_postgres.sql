-- Migration: Add game_id and timestamps to game_state table (PostgreSQL version)
-- Date: 2025-11-09
-- Purpose: Support multiple active games with unique identifiers and permanent game history

-- Add new columns to game_state table
-- Note: Remove DEFAULT to avoid dependency issues - we'll set UUIDs in UPDATE statement
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS game_id UUID;
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS game_id UUID;
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS created_at VARCHAR;
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS updated_at VARCHAR;

-- Create unique index on game_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_game_state_game_id ON game_state(game_id);

-- Update existing records to have a game_id (if any exist)
UPDATE game_state SET game_id = gen_random_uuid() WHERE game_id IS NULL;
UPDATE game_state SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;
UPDATE game_state SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;
-- Note: Application code will set these values when creating new games

-- Note: The game_records and game_player_results tables should already exist
-- from previous migrations. If not, they will be created automatically by
-- SQLAlchemy on first use.