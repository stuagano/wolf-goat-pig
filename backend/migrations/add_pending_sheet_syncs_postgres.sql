-- Queue table for background sheet sync with deduplication
CREATE TABLE IF NOT EXISTS pending_sheet_syncs (
    id SERIAL PRIMARY KEY,
    date VARCHAR NOT NULL,
    "group" VARCHAR NOT NULL,
    location VARCHAR NOT NULL,
    duration VARCHAR,
    player_scores JSONB NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'pending',
    dedup_action VARCHAR,
    created_at VARCHAR,
    processed_at VARCHAR,
    error VARCHAR
);

CREATE INDEX IF NOT EXISTS ix_pending_sheet_syncs_date ON pending_sheet_syncs (date);
CREATE INDEX IF NOT EXISTS ix_pending_sheet_syncs_status ON pending_sheet_syncs (status);
