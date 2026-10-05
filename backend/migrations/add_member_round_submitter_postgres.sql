-- Keep the authenticated submitter separate from the player credited with a result.
ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS submitted_by_profile_id INTEGER REFERENCES player_profiles(id);
