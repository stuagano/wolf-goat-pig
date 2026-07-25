-- Migration: track handicap provenance and email-delivery state.
--
-- issue #320: handicap_source distinguishes an authoritative GHIN handicap
--   from the 18.0 placeholder so the UI can show "pending" instead of a fake 18.
-- issue #318: welcome_email_sent_at records when the first-login welcome email
--   was accepted by the provider (null = safe to retry).
-- issue #317: confirmation_email_sent_at dedupes signup confirmation emails.

ALTER TABLE player_profiles ADD COLUMN IF NOT EXISTS handicap_source VARCHAR;
ALTER TABLE player_profiles ADD COLUMN IF NOT EXISTS welcome_email_sent_at VARCHAR;
ALTER TABLE daily_signups ADD COLUMN IF NOT EXISTS confirmation_email_sent_at VARCHAR;

-- Backfill: existing profiles whose handicap is the exact 18.0 placeholder and
-- have never synced GHIN are "default" (unknown); everything else with a value
-- we treat as manually set so we don't mislabel real 18.0 golfers as unknown.
UPDATE player_profiles
   SET handicap_source = 'default'
 WHERE handicap_source IS NULL
   AND ghin_last_updated IS NULL
   AND handicap = 18.0;

UPDATE player_profiles
   SET handicap_source = 'ghin'
 WHERE handicap_source IS NULL
   AND ghin_last_updated IS NOT NULL;

UPDATE player_profiles
   SET handicap_source = 'manual'
 WHERE handicap_source IS NULL;
