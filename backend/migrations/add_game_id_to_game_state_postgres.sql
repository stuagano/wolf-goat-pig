-- Migration: Add game_id and timestamps to game_state table (PostgreSQL version)
-- Date: 2025-11-09
-- Purpose: Support multiple active games with unique identifiers and permanent game history

-- Add new columns to game_state table
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS game_id UUID;
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS created_at VARCHAR;
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS updated_at VARCHAR;

-- Create unique index on game_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_game_state_game_id ON game_state(game_id);

-- Update existing records to have a game_id (if any exist)
-- Note: Application code will set these values when creating new games

-- Note: The game_records and game_player_results tables should already exist
-- from previous migrations. If not, they will be created automatically by
-- SQLAlchemy on first use.