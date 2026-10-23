-- Opt-in flag + dedup/audit log for same-day signup alerts
-- (auto-applied once at startup by app/migrations_runner.py)

-- Per-player opt-in: "email me when someone signs up for today's game".
-- Separate from signup_confirmations_enabled (your own signup receipt), and
-- defaults off so nobody is enrolled without asking.
ALTER TABLE email_preferences ADD COLUMN IF NOT EXISTS same_day_signups_enabled INTEGER DEFAULT 0;

-- One row per (signup, recipient) successfully emailed, so a retried or
-- concurrent delivery pass never double-alerts about the same signup.
CREATE TABLE IF NOT EXISTS same_day_signup_notifications (
    id SERIAL PRIMARY KEY,
    signup_id INTEGER NOT NULL,
    recipient_profile_id INTEGER NOT NULL,
    sent_at VARCHAR,
    CONSTRAINT uq_same_day_signup_recipient UNIQUE (signup_id, recipient_profile_id)
);

CREATE INDEX IF NOT EXISTS ix_same_day_signup_notifications_signup_id
    ON same_day_signup_notifications (signup_id);
