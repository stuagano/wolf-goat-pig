-- Per-player-per-hole score and quarters log.
-- score and quarters are independently updatable.
-- Zero-sum invariant (SUM(quarters) == 0 per hole) is checked at finalization.
CREATE TABLE IF NOT EXISTS hole_events (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR NOT NULL,
    hole_number INTEGER NOT NULL,
    player_id VARCHAR NOT NULL,
    score INTEGER,
    quarters FLOAT NOT NULL DEFAULT 0,
    recorded_at VARCHAR NOT NULL,
    CONSTRAINT uq_hole_events_game_hole_player UNIQUE (game_id, hole_number, player_id)
);

CREATE INDEX IF NOT EXISTS ix_hole_events_game_id ON hole_events (game_id);
