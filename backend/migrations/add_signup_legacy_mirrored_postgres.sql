-- Which signups were written to the old tee sheet. Cancel still removes
-- that row after the player clears their roster link.
-- (auto-applied once at startup by app/migrations_runner.py)

ALTER TABLE daily_signups ADD COLUMN IF NOT EXISTS legacy_mirrored INTEGER NOT NULL DEFAULT 0;

-- Signups that already exist were created under a roster link.
UPDATE daily_signups SET legacy_mirrored = 1 WHERE legacy_mirrored = 0;
