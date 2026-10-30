-- Separate upgrade also protects tables whose original audit migration is recorded.
-- Octal semicolons keep the function body compatible with the simple SQL splitter.
-- Runtime roles must not own the table/function or have DDL rights to remove guards.
CREATE OR REPLACE FUNCTION participant_correction_reject_mutation() RETURNS trigger
LANGUAGE plpgsql AS E'BEGIN RAISE EXCEPTION ''Participant correction audit is immutable''\073 END\073';
DROP TRIGGER IF EXISTS immutable_participant_audit ON participant_correction_audits;
CREATE TRIGGER immutable_participant_audit BEFORE UPDATE OR DELETE OR TRUNCATE
ON participant_correction_audits FOR EACH STATEMENT
EXECUTE FUNCTION participant_correction_reject_mutation();
