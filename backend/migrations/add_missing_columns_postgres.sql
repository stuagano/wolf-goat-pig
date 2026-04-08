-- Add missing columns to legacy_rounds table
ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS duration VARCHAR;
ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS hole_scores JSONB DEFAULT '{}';
ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS betting_history JSONB DEFAULT '[]';
ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS performance_metrics JSONB DEFAULT '{}';
ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS created_at VARCHAR;

-- Add missing columns to game_player_results table
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS hole_scores JSONB;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS betting_history JSONB;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS performance_metrics JSONB;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS created_at VARCHAR;
