-- Narrative log of a hole — betting arc, play context, and resolution.
-- log_data stores the full structured JSON story.
-- box, winner, total_quarters are extracted for efficient querying.
CREATE TABLE IF NOT EXISTS hole_logs (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR NOT NULL,
    hole_number INTEGER NOT NULL,
    log_data JSONB NOT NULL,
    recorded_at VARCHAR NOT NULL,
    CONSTRAINT uq_hole_logs_game_hole UNIQUE (game_id, hole_number)
);

CREATE INDEX IF NOT EXISTS ix_hole_logs_game_id ON hole_logs (game_id);
