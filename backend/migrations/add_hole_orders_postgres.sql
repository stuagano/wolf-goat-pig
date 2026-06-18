-- Hitting order per hole — editable any time, last-write-wins.
-- captain_id is hitting_order[0] for quick lookups.
CREATE TABLE IF NOT EXISTS hole_orders (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR NOT NULL,
    hole_number INTEGER NOT NULL,
    hitting_order JSONB NOT NULL,
    captain_id VARCHAR,
    recorded_at VARCHAR NOT NULL,
    CONSTRAINT uq_hole_orders_game_hole UNIQUE (game_id, hole_number)
);

CREATE INDEX IF NOT EXISTS ix_hole_orders_game_id ON hole_orders (game_id);
