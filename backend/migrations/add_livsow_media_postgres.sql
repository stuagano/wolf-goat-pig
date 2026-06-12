-- LivSow media archive: videos/images harvested from the GroupMe group.
CREATE TABLE IF NOT EXISTS livsow_media (
    id SERIAL PRIMARY KEY,
    groupme_message_id VARCHAR UNIQUE,
    kind VARCHAR,
    url VARCHAR,
    preview_url VARCHAR,
    archived_url VARCHAR,
    author VARCHAR,
    caption VARCHAR,
    posted_at VARCHAR,
    harvested_at VARCHAR,
    likes INTEGER DEFAULT 0,
    featured BOOLEAN DEFAULT FALSE,
    deleted BOOLEAN DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS ix_livsow_media_kind_posted ON livsow_media (kind, posted_at);
CREATE INDEX IF NOT EXISTS ix_livsow_media_author ON livsow_media (author);
