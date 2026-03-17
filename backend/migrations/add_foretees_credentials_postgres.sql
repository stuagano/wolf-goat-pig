-- Add per-user ForeTees credentials to player_profiles (PostgreSQL)
ALTER TABLE player_profiles ADD COLUMN IF NOT EXISTS foretees_username VARCHAR(255);
ALTER TABLE player_profiles ADD COLUMN IF NOT EXISTS foretees_password_encrypted TEXT;
