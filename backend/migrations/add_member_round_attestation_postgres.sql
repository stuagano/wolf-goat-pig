-- Member round-posting + peer attestation on legacy_rounds.
-- All additive/nullable so existing sheet rows are untouched. Existing rows get
-- status='attested' via the column default, keeping current reads unchanged.
-- Sorts after add_legacy_rounds*_postgres.sql, so the table already exists.

ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS player_profile_id INTEGER REFERENCES player_profiles(id);
ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS status VARCHAR(16) NOT NULL DEFAULT 'attested';
ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS attested_by_profile_id INTEGER REFERENCES player_profiles(id);
ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS attested_at TIMESTAMP NULL;
ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS foursome JSON NULL;

-- One member-posted round per member per calendar day (member self-posts only).
CREATE UNIQUE INDEX IF NOT EXISTS ux_member_round_per_day
    ON legacy_rounds (member, date)
    WHERE source = 'member';
