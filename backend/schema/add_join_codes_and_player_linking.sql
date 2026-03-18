-- Migration: Add join codes and player linking for authenticated game joining
-- Date: 2025-01-XX
-- Purpose: Enable authenticated users to join games via codes and track their progress

-- Add join code and auth columns to game_state table
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS join_code VARCHAR;
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS creator_user_id VARCHAR;
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS game_status VARCHAR DEFAULT 'setup';

-- Create unique index on join_code
CREATE UNIQUE INDEX IF NOT EXISTS idx_game_state_join_code ON game_state(join_code);

-- Create game_players table to track authenticated players in games
CREATE TABLE IF NOT EXISTS game_players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id VARCHAR NOT NULL,
    player_slot_id VARCHAR NOT NULL,
    user_id VARCHAR,
    player_profile_id INTEGER,
    player_name VARCHAR NOT NULL,
    handicap REAL NOT NULL,
    join_status VARCHAR DEFAULT 'pending',
    joined_at VARCHAR,
    created_at VARCHAR NOT NULL
);

-- Create indexes for game_players
CREATE INDEX IF NOT EXISTS idx_game_players_game_id ON game_players(game_id);
CREATE INDEX IF NOT EXISTS idx_game_players_user_id ON game_players(user_id);
CREATE INDEX IF NOT EXISTS idx_game_players_profile_id ON game_players(player_profile_id);

-- Ensure game_player_results can be linked to authenticated users
-- (The player_profile_id column should already exist, but ensure it's indexed)
CREATE INDEX IF NOT EXISTS idx_game_player_results_profile_id ON game_player_results(player_profile_id);
