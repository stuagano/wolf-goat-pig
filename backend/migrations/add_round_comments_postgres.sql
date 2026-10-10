-- Notes on a historical foursome. Keyed by date + group + location because
-- sheet rounds (the Oct 6 game, for example) have no GameRecord id.
CREATE TABLE IF NOT EXISTS round_comments (
    id SERIAL PRIMARY KEY,
    round_date VARCHAR NOT NULL,
    round_group VARCHAR NOT NULL,
    location VARCHAR NOT NULL DEFAULT '',
    author_profile_id INTEGER NOT NULL REFERENCES player_profiles(id),
    body TEXT NOT NULL,
    created_at VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_round_comments_round
    ON round_comments (round_date, round_group, location);
CREATE INDEX IF NOT EXISTS ix_round_comments_author
    ON round_comments (author_profile_id);
