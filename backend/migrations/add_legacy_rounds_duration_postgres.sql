-- Add duration column to legacy_rounds table
ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS duration VARCHAR;
