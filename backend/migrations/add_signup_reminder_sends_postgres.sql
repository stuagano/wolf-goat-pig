-- Dedup log for the Thursday "Sunday's game" signup nudge
-- (auto-applied once at startup by app/migrations_runner.py)

-- One row per (Sunday, player) successfully emailed, so a retried job never double-sends
CREATE TABLE IF NOT EXISTS signup_reminder_sends (
    id SERIAL PRIMARY KEY,
    game_date VARCHAR NOT NULL,
    player_profile_id INTEGER NOT NULL,
    sent_at VARCHAR,
    CONSTRAINT uq_signup_reminder_date_player UNIQUE (game_date, player_profile_id)
);

CREATE INDEX IF NOT EXISTS ix_signup_reminder_sends_game_date ON signup_reminder_sends (game_date);
