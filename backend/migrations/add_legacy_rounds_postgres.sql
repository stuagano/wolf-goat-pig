-- Migration: create legacy_rounds table for sheet-synced historical data
CREATE TABLE IF NOT EXISTS legacy_rounds (
    id          SERIAL PRIMARY KEY,
    date        VARCHAR NOT NULL,
    "group"     VARCHAR,
    member      VARCHAR NOT NULL,
    score       INTEGER NOT NULL,
    location    VARCHAR,
    source      VARCHAR DEFAULT 'sheet',
    synced_at   VARCHAR
);

CREATE INDEX IF NOT EXISTS ix_legacy_rounds_date   ON legacy_rounds (date);
CREATE INDEX IF NOT EXISTS ix_legacy_rounds_member ON legacy_rounds (member);
