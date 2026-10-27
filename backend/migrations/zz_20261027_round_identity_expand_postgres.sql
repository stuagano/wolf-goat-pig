-- Additive expansion only. Never activate canonical mode or backfill at boot.
-- Existing game/profile foreign keys and legacy index retirement await accounting.
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS revision INTEGER NOT NULL DEFAULT 0;
ALTER TABLE game_records ADD COLUMN IF NOT EXISTS played_on DATE;
ALTER TABLE game_records ADD COLUMN IF NOT EXISTS raw_date VARCHAR;
ALTER TABLE game_records ADD COLUMN IF NOT EXISTS "group" VARCHAR;
ALTER TABLE game_records ADD COLUMN IF NOT EXISTS detail_coverage VARCHAR;
ALTER TABLE game_records ADD COLUMN IF NOT EXISTS roster_complete BOOLEAN;
ALTER TABLE game_records ADD COLUMN IF NOT EXISTS score_eligible BOOLEAN;
ALTER TABLE game_records ADD COLUMN IF NOT EXISTS accepted_revision INTEGER NOT NULL DEFAULT 0;
ALTER TABLE game_records ALTER COLUMN total_holes_played DROP NOT NULL;
ALTER TABLE game_records ALTER COLUMN total_holes_played DROP DEFAULT;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS participant_id VARCHAR;
ALTER TABLE game_player_results ALTER COLUMN final_position DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN total_earnings DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN total_earnings DROP DEFAULT;
ALTER TABLE game_player_results ALTER COLUMN holes_won DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN holes_won DROP DEFAULT;
ALTER TABLE game_player_results ALTER COLUMN successful_bets DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN successful_bets DROP DEFAULT;
ALTER TABLE game_player_results ALTER COLUMN total_bets DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN total_bets DROP DEFAULT;
ALTER TABLE game_player_results ALTER COLUMN partnerships_formed DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN partnerships_formed DROP DEFAULT;
ALTER TABLE game_player_results ALTER COLUMN partnerships_won DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN partnerships_won DROP DEFAULT;
ALTER TABLE game_player_results ALTER COLUMN solo_attempts DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN solo_attempts DROP DEFAULT;
ALTER TABLE game_player_results ALTER COLUMN solo_wins DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN solo_wins DROP DEFAULT;
ALTER TABLE game_player_results ALTER COLUMN ping_pongs DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN ping_pongs DROP DEFAULT;
ALTER TABLE game_player_results ALTER COLUMN ping_pongs_won DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN ping_pongs_won DROP DEFAULT;
ALTER TABLE game_player_results ALTER COLUMN invisible_aardvark_holes DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN invisible_aardvark_holes DROP DEFAULT;
ALTER TABLE game_player_results ALTER COLUMN invisible_aardvark_holes_won DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN invisible_aardvark_holes_won DROP DEFAULT;
ALTER TABLE game_player_results ALTER COLUMN duncan_attempts DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN duncan_attempts DROP DEFAULT;
ALTER TABLE game_player_results ALTER COLUMN duncan_wins DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN duncan_wins DROP DEFAULT;
ALTER TABLE game_player_results ALTER COLUMN tunkarri_attempts DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN tunkarri_attempts DROP DEFAULT;
ALTER TABLE game_player_results ALTER COLUMN tunkarri_wins DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN tunkarri_wins DROP DEFAULT;
ALTER TABLE game_player_results ALTER COLUMN big_dick_attempts DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN big_dick_attempts DROP DEFAULT;
ALTER TABLE game_player_results ALTER COLUMN big_dick_wins DROP NOT NULL;
ALTER TABLE game_player_results ALTER COLUMN big_dick_wins DROP DEFAULT;
ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS game_id VARCHAR;
ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS participant_id VARCHAR;
ALTER TABLE round_comments ADD COLUMN IF NOT EXISTS game_id VARCHAR;
ALTER TABLE round_reactions ADD COLUMN IF NOT EXISTS game_id VARCHAR;
ALTER TABLE pending_sheet_syncs ADD COLUMN IF NOT EXISTS game_id VARCHAR;
ALTER TABLE pending_sheet_syncs ADD COLUMN IF NOT EXISTS source_round_token VARCHAR;
ALTER TABLE pending_sheet_syncs ADD COLUMN IF NOT EXISTS source_scope VARCHAR;
ALTER TABLE pending_sheet_syncs ADD COLUMN IF NOT EXISTS operation_key VARCHAR;
ALTER TABLE pending_sheet_syncs ADD COLUMN IF NOT EXISTS expected_revision INTEGER;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS delivery_key VARCHAR;
CREATE UNIQUE INDEX IF NOT EXISTS uq_notifications_delivery_key ON notifications(delivery_key);
-- Both new keys are nullable on old rows, so no legacy-data uniqueness assumption.
CREATE UNIQUE INDEX IF NOT EXISTS uq_game_result_participant ON game_player_results(game_record_id, participant_id);
CREATE TABLE IF NOT EXISTS round_sources (
    id VARCHAR PRIMARY KEY, kind VARCHAR NOT NULL, scope VARCHAR NOT NULL,
    round_token VARCHAR NOT NULL, game_id VARCHAR, binding_evidence JSON,
    bound_by_profile_id INTEGER, bound_at VARCHAR, revision INTEGER NOT NULL DEFAULT 0,
    latest_observation_key VARCHAR, snapshot_fingerprint VARCHAR, created_at VARCHAR NOT NULL,
    CONSTRAINT uq_round_source_token UNIQUE(kind, scope, round_token)
);
CREATE TABLE IF NOT EXISTS round_observations (
    id VARCHAR PRIMARY KEY, source_id VARCHAR NOT NULL REFERENCES round_sources(id),
    observation_key VARCHAR NOT NULL, participant_id VARCHAR, raw_payload JSON NOT NULL,
    parsed_values JSON, present_fields JSON NOT NULL, parse_status VARCHAR NOT NULL,
    source_revision VARCHAR, snapshot_fingerprint VARCHAR, content_fingerprint VARCHAR,
    continuity_verified BOOLEAN NOT NULL, observed_at VARCHAR NOT NULL,
    CONSTRAINT uq_round_observation_event UNIQUE(source_id, observation_key)
);
CREATE TABLE IF NOT EXISTS round_field_heads (
    id VARCHAR PRIMARY KEY, source_id VARCHAR NOT NULL REFERENCES round_sources(id),
    participant_id VARCHAR NOT NULL DEFAULT '', field VARCHAR NOT NULL,
    observation_id VARCHAR REFERENCES round_observations(id), revision INTEGER NOT NULL DEFAULT 0,
    accepted_revision INTEGER NOT NULL DEFAULT 0, raw_present BOOLEAN NOT NULL, raw_value JSON,
    accepted_present BOOLEAN NOT NULL, accepted_value JSON, proposed_present BOOLEAN NOT NULL,
    proposed_value JSON, updated_at VARCHAR NOT NULL,
    CONSTRAINT uq_round_field_head UNIQUE(source_id, participant_id, field)
);
CREATE TABLE IF NOT EXISTS round_issues (
    id VARCHAR PRIMARY KEY, source_id VARCHAR NOT NULL REFERENCES round_sources(id), game_id VARCHAR,
    kind VARCHAR NOT NULL, participant_id VARCHAR NOT NULL, field VARCHAR,
    candidate_game_ids JSON NOT NULL, fingerprint VARCHAR NOT NULL, status VARCHAR NOT NULL,
    generation INTEGER NOT NULL, revision INTEGER NOT NULL, head_revision INTEGER NOT NULL,
    baseline_revision INTEGER NOT NULL, observation_id VARCHAR REFERENCES round_observations(id),
    accepted_present BOOLEAN NOT NULL, accepted_value JSON, proposed_present BOOLEAN NOT NULL,
    proposed_value JSON, created_at VARCHAR NOT NULL, last_seen_at VARCHAR NOT NULL
);
CREATE TABLE IF NOT EXISTS round_resolutions (
    id VARCHAR PRIMARY KEY, issue_id VARCHAR NOT NULL REFERENCES round_issues(id),
    actor_profile_id INTEGER NOT NULL, action VARCHAR NOT NULL, reason VARCHAR NOT NULL,
    value_present BOOLEAN NOT NULL, value JSON, target_game_id VARCHAR, game_revision INTEGER,
    issue_revision INTEGER NOT NULL, head_revision INTEGER NOT NULL, baseline_revision INTEGER NOT NULL,
    observation_ids JSON NOT NULL, created_at VARCHAR NOT NULL
);
CREATE TABLE IF NOT EXISTS round_aliases (
    id VARCHAR PRIMARY KEY, date_key VARCHAR NOT NULL, "group" VARCHAR NOT NULL,
    location VARCHAR NOT NULL, game_id VARCHAR NOT NULL, evidence JSON, created_at VARCHAR NOT NULL,
    CONSTRAINT uq_round_alias_target UNIQUE(date_key, "group", location, game_id)
);
CREATE TABLE IF NOT EXISTS round_requests (
    id VARCHAR PRIMARY KEY, actor_profile_id INTEGER NOT NULL, request_key VARCHAR NOT NULL,
    fingerprint VARCHAR NOT NULL, game_id VARCHAR, outcome JSON, created_at VARCHAR NOT NULL,
    CONSTRAINT uq_round_request_actor_key UNIQUE(actor_profile_id, request_key)
);
CREATE TABLE IF NOT EXISTS round_deliveries (
    id VARCHAR PRIMARY KEY, issue_id VARCHAR REFERENCES round_issues(id), issue_event_key VARCHAR NOT NULL,
    recipient_profile_id INTEGER, channel VARCHAR NOT NULL, delivery_key VARCHAR NOT NULL UNIQUE,
    status VARCHAR NOT NULL, attempts INTEGER NOT NULL, lease_owner VARCHAR, lease_expires_at VARCHAR,
    provider_receipt VARCHAR, error VARCHAR, created_at VARCHAR NOT NULL, delivered_at VARCHAR,
    CONSTRAINT uq_round_delivery_event UNIQUE(issue_event_key, recipient_profile_id, channel)
);
CREATE TABLE IF NOT EXISTS round_identity_leases (
    key VARCHAR PRIMARY KEY, owner VARCHAR, epoch INTEGER NOT NULL, expires_at VARCHAR,
    snapshot_fingerprint VARCHAR, source_version VARCHAR
);
CREATE TABLE IF NOT EXISTS round_migration_checkpoints (
    id VARCHAR PRIMARY KEY, manifest_checksum VARCHAR NOT NULL, game_id VARCHAR NOT NULL,
    operation_key VARCHAR NOT NULL, outcome JSON, created_at VARCHAR NOT NULL,
    CONSTRAINT uq_round_migration_operation UNIQUE(manifest_checksum, game_id, operation_key)
);
ALTER TABLE game_records ADD COLUMN IF NOT EXISTS is_retracted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS is_retracted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE round_deliveries ALTER COLUMN recipient_profile_id DROP NOT NULL;
-- Never fabricate missing keys on existing intents. Offline accounting is required.
ALTER TABLE round_deliveries ALTER COLUMN delivery_key SET NOT NULL;
CREATE INDEX IF NOT EXISTS ix_round_sources_game_id ON round_sources(game_id);
CREATE INDEX IF NOT EXISTS ix_round_issues_game_id ON round_issues(game_id);
CREATE INDEX IF NOT EXISTS ix_round_aliases_game_id ON round_aliases(game_id);
-- PostgreSQL SELECT * views freeze their columns. Appending new columns is safe
-- with CREATE OR REPLACE, including when init_db ran before this expansion.
CREATE OR REPLACE VIEW legacy_rounds_official AS SELECT * FROM legacy_rounds WHERE status <> 'pending';
