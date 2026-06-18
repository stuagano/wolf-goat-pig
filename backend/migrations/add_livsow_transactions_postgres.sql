-- LivSow roster snapshots + auto-derived transaction log.
-- Snapshots are a change-log: a row is stored only when the compacted
-- roster (names + roles) differs from the latest confirmed snapshot.
CREATE TABLE IF NOT EXISTS livsow_roster_snapshots (
    id SERIAL PRIMARY KEY,
    taken_at VARCHAR,
    season VARCHAR,
    status VARCHAR DEFAULT 'pending',
    roster_hash VARCHAR,
    player_count INTEGER,
    roster JSONB
);
CREATE INDEX IF NOT EXISTS ix_livsow_snapshots_status ON livsow_roster_snapshots (status, taken_at);
CREATE INDEX IF NOT EXISTS ix_livsow_snapshots_hash ON livsow_roster_snapshots (roster_hash);

CREATE TABLE IF NOT EXISTS livsow_transactions (
    id SERIAL PRIMARY KEY,
    detected_at VARCHAR,
    season VARCHAR,
    week_label VARCHAR,
    snapshot_id INTEGER,
    type VARCHAR,
    player_name VARCHAR,
    from_team VARCHAR,
    to_team VARCHAR,
    from_role VARCHAR,
    to_role VARCHAR,
    details JSONB,
    deleted BOOLEAN DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS ix_livsow_txn_player ON livsow_transactions (player_name);
CREATE INDEX IF NOT EXISTS ix_livsow_txn_detected ON livsow_transactions (season, detected_at);
CREATE INDEX IF NOT EXISTS ix_livsow_txn_snapshot ON livsow_transactions (snapshot_id);
