-- Dedicated transactional audit; does not rewrite original round evidence.
CREATE TABLE IF NOT EXISTS participant_correction_audits (
    id VARCHAR PRIMARY KEY,
    actor_profile_id INTEGER NOT NULL,
    request_key VARCHAR NOT NULL,
    fingerprint VARCHAR NOT NULL,
    result_id INTEGER NOT NULL,
    game_record_id INTEGER NOT NULL,
    game_id VARCHAR NOT NULL,
    old_profile_id INTEGER,
    new_profile_id INTEGER NOT NULL,
    reason VARCHAR NOT NULL,
    before JSON NOT NULL,
    after JSON NOT NULL,
    created_at VARCHAR NOT NULL,
    CONSTRAINT uq_participant_correction_request UNIQUE (actor_profile_id, request_key)
);
