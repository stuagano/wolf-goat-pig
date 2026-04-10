-- Add Venmo handle to player profiles for payment settlement
ALTER TABLE player_profiles ADD COLUMN IF NOT EXISTS venmo_handle VARCHAR;
