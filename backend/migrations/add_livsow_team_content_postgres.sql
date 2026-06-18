-- LivSow team page content: captain-editable franchise-page fields.
CREATE TABLE IF NOT EXISTS livsow_team_content (
    id SERIAL PRIMARY KEY,
    team_slug VARCHAR,
    season VARCHAR,
    motto VARCHAR,
    about VARCHAR,
    announcement VARCHAR,
    logo_url VARCHAR,
    updated_by VARCHAR,
    updated_at VARCHAR
);
CREATE INDEX IF NOT EXISTS ix_livsow_team_content_slug ON livsow_team_content (team_slug, season);
