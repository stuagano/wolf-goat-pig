CREATE TABLE IF NOT EXISTS account_claims (
    id SERIAL PRIMARY KEY,
    requester_profile_id INTEGER NOT NULL,
    target_profile_id INTEGER NOT NULL,
    canonical_name VARCHAR NOT NULL,
    requester_email VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'pending',
    created_at VARCHAR,
    resolved_at VARCHAR,
    resolved_by VARCHAR
);
CREATE INDEX IF NOT EXISTS ix_account_claims_requester_profile_id ON account_claims (requester_profile_id);
CREATE INDEX IF NOT EXISTS ix_account_claims_target_profile_id ON account_claims (target_profile_id);
CREATE INDEX IF NOT EXISTS ix_account_claims_status ON account_claims (status);
