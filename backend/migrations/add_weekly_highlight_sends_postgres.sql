-- Dedup log for the weekly league highlights email
-- (auto-applied once at startup by app/migrations_runner.py)

-- One row per (week, player) successfully emailed, so a retried job never double-sends
CREATE TABLE IF NOT EXISTS weekly_highlight_sends (
    id SERIAL PRIMARY KEY,
    week_start VARCHAR NOT NULL,
    player_profile_id INTEGER NOT NULL,
    sent_at VARCHAR,
    CONSTRAINT uq_weekly_highlight_week_player UNIQUE (week_start, player_profile_id)
);

CREATE INDEX IF NOT EXISTS ix_weekly_highlight_sends_week_start ON weekly_highlight_sends (week_start);
