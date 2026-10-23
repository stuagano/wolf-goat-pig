-- SQLite: ensure_schema.py skips the duplicate-column error on subsequent runs.
ALTER TABLE email_preferences ADD COLUMN same_day_signups_enabled INTEGER DEFAULT 0;

CREATE TABLE IF NOT EXISTS same_day_signup_notifications (
    id INTEGER PRIMARY KEY,
    signup_id INTEGER NOT NULL,
    recipient_profile_id INTEGER NOT NULL,
    sent_at VARCHAR,
    CONSTRAINT uq_same_day_signup_recipient UNIQUE (signup_id, recipient_profile_id)
);

CREATE INDEX IF NOT EXISTS ix_same_day_signup_notifications_signup_id
    ON same_day_signup_notifications (signup_id);
