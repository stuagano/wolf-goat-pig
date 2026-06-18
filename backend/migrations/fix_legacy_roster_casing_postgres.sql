-- Correct three player names to match the canonical tee-sheet dropdown spelling.
-- The Jan-2026 seed snapshot had stale casing/spelling; the dropdown is the
-- source of truth. All statements are guarded so a re-run (or an already-correct
-- row) is a harmless no-op.

-- Dave Mcgrath -> Dave McGrath
UPDATE player_profiles SET legacy_name = 'Dave McGrath' WHERE legacy_name = 'Dave Mcgrath';
UPDATE legacy_roster SET name = 'Dave McGrath' WHERE name = 'Dave Mcgrath' AND NOT EXISTS (SELECT 1 FROM legacy_roster r WHERE r.name = 'Dave McGrath');

-- Doug Mccombs -> Doug McCombs
UPDATE player_profiles SET legacy_name = 'Doug McCombs' WHERE legacy_name = 'Doug Mccombs';
UPDATE legacy_roster SET name = 'Doug McCombs' WHERE name = 'Doug Mccombs' AND NOT EXISTS (SELECT 1 FROM legacy_roster r WHERE r.name = 'Doug McCombs');

-- Josh Trey -> Josh Treyve (the correct spelling is already canonical via the
-- round-history sync, so remap any profile then drop the stale truncated row).
UPDATE player_profiles SET legacy_name = 'Josh Treyve' WHERE legacy_name = 'Josh Trey';
DELETE FROM legacy_roster WHERE name = 'Josh Trey';
