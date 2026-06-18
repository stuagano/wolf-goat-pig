-- Opt-in flag + dedup/audit log for headcount callouts
-- (auto-applied once at startup by app/migrations_runner.py)

-- Per-player opt-in: "call me when a game is short of a full foursome"
ALTER TABLE email_preferences ADD COLUMN IF NOT EXISTS callout_list_enabled INTEGER DEFAULT 0;

-- One row per (game_date, window) that fired, so we never double-call a window
CREATE TABLE IF NOT EXISTS callout_notifications (
    id SERIAL PRIMARY KEY,
    game_date VARCHAR NOT NULL,
    callout_window VARCHAR NOT NULL,
    signup_count INTEGER,
    target INTEGER,
    shortfall INTEGER,
    recipient_count INTEGER,
    sent_at VARCHAR
);

CREATE INDEX IF NOT EXISTS ix_callout_notifications_date_window
    ON callout_notifications (game_date, callout_window);
