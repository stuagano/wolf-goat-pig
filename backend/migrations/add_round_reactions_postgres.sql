-- Slack-style emoji on a round, and on an individual comment (comment_id set).
-- COALESCE makes "no comment" unique, since Postgres treats NULL as distinct.
CREATE TABLE IF NOT EXISTS round_reactions (
    id SERIAL PRIMARY KEY,
    round_date VARCHAR NOT NULL,
    round_group VARCHAR NOT NULL,
    location VARCHAR NOT NULL DEFAULT '',
    comment_id INTEGER REFERENCES round_comments(id) ON DELETE CASCADE,
    profile_id INTEGER NOT NULL REFERENCES player_profiles(id),
    emoji VARCHAR NOT NULL,
    created_at VARCHAR NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_round_reactions_player_emoji
    ON round_reactions (round_date, round_group, location, COALESCE(comment_id, 0), profile_id, emoji);
CREATE INDEX IF NOT EXISTS ix_round_reactions_round
    ON round_reactions (round_date, round_group, location);
CREATE INDEX IF NOT EXISTS ix_round_reactions_profile
    ON round_reactions (profile_id);
CREATE INDEX IF NOT EXISTS ix_round_reactions_comment
    ON round_reactions (comment_id);
