-- Migration: Add legacy_name column to player_profiles
-- This column stores the player's name in the legacy tee sheet system (thousand-cranes.com)

-- Add column if it doesn't exist (PostgreSQL 9.6+)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'player_profiles' AND column_name = 'legacy_name'
    ) THEN
        ALTER TABLE player_profiles ADD COLUMN legacy_name VARCHAR(255);
    END IF;
END $$;

-- Create index if it doesn't exist
CREATE INDEX IF NOT EXISTS ix_player_profiles_legacy_name ON player_profiles(legacy_name);
