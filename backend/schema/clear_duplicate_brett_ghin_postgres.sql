-- Clear GHIN ID from soft-deleted duplicate player record (id=62)
-- so it can be assigned to the real Brett Saks record (id=9)
UPDATE player_profiles SET ghin_id = NULL WHERE id = 62 AND is_active = 0;
