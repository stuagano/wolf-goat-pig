-- Migration: Add tee_order column to game_players table
-- This allows tracking the playing order after tee toss independently from seat position

-- Add tee_order column (nullable since existing records won't have it set)
ALTER TABLE game_players ADD COLUMN IF NOT EXISTS tee_order INTEGER;

-- Add index on tee_order for faster ordering queries
CREATE INDEX IF NOT EXISTS idx_game_players_tee_order ON game_players(game_id, tee_order);

-- Note: For existing games in "setup" status, tee_order will remain NULL until set via /games/{game_id}/tee-order endpoint
-- This is intentional as tee order is only set after the tee toss is complete
