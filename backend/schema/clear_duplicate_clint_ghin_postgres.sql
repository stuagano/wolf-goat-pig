-- Clear GHIN ID from soft-deleted duplicate player record (id=61)
-- so it can be assigned to the real Clint Knudsen record (id=19)
UPDATE player_profiles SET ghin_id = NULL WHERE id = 61 AND is_active = 0;
