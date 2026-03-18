-- Migration: Add special event stats columns for ping pong, invisible aardvark, and solo types
-- These allow tracking year-end stats like "Steve ping ponged 47 times this year"

-- Add special event columns to player_statistics table
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS ping_pong_count INTEGER DEFAULT 0;
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS ping_pong_wins INTEGER DEFAULT 0;
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS invisible_aardvark_appearances INTEGER DEFAULT 0;
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS invisible_aardvark_wins INTEGER DEFAULT 0;

-- Add specific solo type columns to player_statistics table
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS duncan_attempts INTEGER DEFAULT 0;
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS duncan_wins INTEGER DEFAULT 0;
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS tunkarri_attempts INTEGER DEFAULT 0;
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS tunkarri_wins INTEGER DEFAULT 0;
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS big_dick_attempts INTEGER DEFAULT 0;
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS big_dick_wins INTEGER DEFAULT 0;

-- Add per-game special event columns to game_player_results table
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS ping_pongs INTEGER DEFAULT 0;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS ping_pongs_won INTEGER DEFAULT 0;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS invisible_aardvark_holes INTEGER DEFAULT 0;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS invisible_aardvark_holes_won INTEGER DEFAULT 0;

-- Add per-game solo type columns to game_player_results table
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS duncan_attempts INTEGER DEFAULT 0;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS duncan_wins INTEGER DEFAULT 0;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS tunkarri_attempts INTEGER DEFAULT 0;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS tunkarri_wins INTEGER DEFAULT 0;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS big_dick_attempts INTEGER DEFAULT 0;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS big_dick_wins INTEGER DEFAULT 0;

-- Note: Existing rows will have default values of 0 for these new columns
-- Stats will start accumulating from games played after this migration
