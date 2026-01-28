-- Migration: Add legacy_name column to player_profiles
-- This column stores the player's name in the legacy tee sheet system (thousand-cranes.com)

-- Add column (will error if exists, which is handled by migration runner)
ALTER TABLE player_profiles ADD COLUMN IF NOT EXISTS legacy_name VARCHAR(255);

-- Create index if it doesn't exist
CREATE INDEX IF NOT EXISTS ix_player_profiles_legacy_name ON player_profiles(legacy_name);
