-- Add special event tracking columns to game_player_results table
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS ping_pongs INTEGER DEFAULT 0;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS ping_pongs_won INTEGER DEFAULT 0;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS invisible_aardvark_holes INTEGER DEFAULT 0;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS invisible_aardvark_holes_won INTEGER DEFAULT 0;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS duncan_attempts INTEGER DEFAULT 0;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS duncan_wins INTEGER DEFAULT 0;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS tunkarri_attempts INTEGER DEFAULT 0;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS tunkarri_wins INTEGER DEFAULT 0;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS big_dick_attempts INTEGER DEFAULT 0;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS big_dick_wins INTEGER DEFAULT 0;
