-- Migration: Add streak tracking, role tracking, and head-to-head records to player_statistics
-- Date: 2025-11-28
-- Description: Enhances player statistics with win/loss streaks, role counts, and H2H records

-- Add streak tracking columns
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS current_win_streak INTEGER DEFAULT 0;
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS current_loss_streak INTEGER DEFAULT 0;
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS best_win_streak INTEGER DEFAULT 0;
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS worst_loss_streak INTEGER DEFAULT 0;

-- Add role tracking columns
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS times_as_wolf INTEGER DEFAULT 0;
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS times_as_goat INTEGER DEFAULT 0;
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS times_as_pig INTEGER DEFAULT 0;
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS times_as_aardvark INTEGER DEFAULT 0;

-- Add head-to-head records (stored as JSON)
ALTER TABLE player_statistics ADD COLUMN IF NOT EXISTS head_to_head_records TEXT DEFAULT '{}';

-- Initialize existing records with default values
UPDATE player_statistics SET current_win_streak = 0 WHERE current_win_streak IS NULL;
UPDATE player_statistics SET current_loss_streak = 0 WHERE current_loss_streak IS NULL;
UPDATE player_statistics SET best_win_streak = 0 WHERE best_win_streak IS NULL;
UPDATE player_statistics SET worst_loss_streak = 0 WHERE worst_loss_streak IS NULL;
UPDATE player_statistics SET times_as_wolf = 0 WHERE times_as_wolf IS NULL;
UPDATE player_statistics SET times_as_goat = 0 WHERE times_as_goat IS NULL;
UPDATE player_statistics SET times_as_pig = 0 WHERE times_as_pig IS NULL;
UPDATE player_statistics SET times_as_aardvark = 0 WHERE times_as_aardvark IS NULL;
UPDATE player_statistics SET head_to_head_records = '{}' WHERE head_to_head_records IS NULL;
