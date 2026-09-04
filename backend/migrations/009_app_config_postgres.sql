CREATE TABLE IF NOT EXISTS app_config (
    name VARCHAR PRIMARY KEY,
    value JSONB NOT NULL DEFAULT '{}'
);

INSERT INTO app_config (name, value)
VALUES ('features', '{"foretees": false, "scorecard_scan": true, "livsow": true, "commissioner_chat": true}')
ON CONFLICT (name) DO NOTHING;
