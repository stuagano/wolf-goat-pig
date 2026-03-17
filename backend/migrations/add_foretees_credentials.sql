-- Add per-user ForeTees credentials to player_profiles (SQLite)
ALTER TABLE player_profiles ADD COLUMN foretees_username TEXT;
ALTER TABLE player_profiles ADD COLUMN foretees_password_encrypted TEXT;
