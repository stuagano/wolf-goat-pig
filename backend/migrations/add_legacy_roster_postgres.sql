-- Canonical roster + pending-capture queue for player onboarding.
-- legacy_roster mirrors Jeff Green's legacy tee-sheet dropdown (the canonical
-- set of valid player names). pending_legacy_players queues self-signed-up
-- golfers who have no canonical match yet, kept separate so they can never
-- leak into canonical reads and falsely validate. See app/models.py.
CREATE TABLE IF NOT EXISTS legacy_roster (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE,
    source VARCHAR DEFAULT 'seed',
    added_at VARCHAR,
    notes VARCHAR
);
CREATE INDEX IF NOT EXISTS ix_legacy_roster_name ON legacy_roster (name);

CREATE TABLE IF NOT EXISTS pending_legacy_players (
    id SERIAL PRIMARY KEY,
    name VARCHAR,
    email VARCHAR,
    player_profile_id INTEGER,
    status VARCHAR DEFAULT 'pending',
    created_at VARCHAR,
    resolved_at VARCHAR,
    notes VARCHAR
);
CREATE INDEX IF NOT EXISTS ix_pending_legacy_players_name ON pending_legacy_players (name);
CREATE INDEX IF NOT EXISTS ix_pending_legacy_players_email ON pending_legacy_players (email);
CREATE INDEX IF NOT EXISTS ix_pending_legacy_players_status ON pending_legacy_players (status);
