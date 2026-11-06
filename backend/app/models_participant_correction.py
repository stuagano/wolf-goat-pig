"""Append-only audit for bounded pre-canonical saved-result link corrections."""

from sqlalchemy import DDL, JSON, Column, Integer, String, UniqueConstraint, event

from .database import Base
from .models_round_identity import _reject_evidence_mutation, new_id, timestamp


class ParticipantCorrectionAudit(Base):
    __tablename__ = "participant_correction_audits"
    __table_args__ = (UniqueConstraint("actor_profile_id", "request_key", name="uq_participant_correction_request"),)
    id = Column(String, primary_key=True, default=new_id)
    actor_profile_id = Column(Integer, nullable=False)
    request_key = Column(String, nullable=False)
    fingerprint = Column(String, nullable=False)
    result_id = Column(Integer, nullable=False)
    game_record_id = Column(Integer, nullable=False)
    game_id = Column(String, nullable=False)
    old_profile_id = Column(Integer, nullable=True)
    new_profile_id = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    before = Column(JSON, nullable=False)
    after = Column(JSON, nullable=False)
    created_at = Column(String, nullable=False, default=timestamp)


event.listen(ParticipantCorrectionAudit, "before_update", _reject_evidence_mutation)
event.listen(ParticipantCorrectionAudit, "before_delete", _reject_evidence_mutation)

# Fresh metadata-created schemas need the same physical boundary as upgrades.
# Owners/superusers can remove triggers; runtime roles must not own this table
# or have schema/function DDL privileges. SQLite cannot isolate DDL privileges.
for operation in ("UPDATE", "DELETE"):
    event.listen(
        ParticipantCorrectionAudit.__table__,
        "after_create",
        DDL(
            f"CREATE TRIGGER immutable_participant_audit_{operation.lower()} "
            f"BEFORE {operation} ON participant_correction_audits BEGIN "
            "SELECT RAISE(ABORT, 'Participant correction audit is immutable'); END"
        ).execute_if(dialect="sqlite"),
    )

for statement in (
    "CREATE OR REPLACE FUNCTION participant_correction_reject_mutation() RETURNS trigger "
    "LANGUAGE plpgsql AS 'BEGIN RAISE EXCEPTION ''Participant correction audit is immutable''; END;'",
    "CREATE TRIGGER immutable_participant_audit BEFORE UPDATE OR DELETE OR TRUNCATE "
    "ON participant_correction_audits FOR EACH STATEMENT "
    "EXECUTE FUNCTION participant_correction_reject_mutation()",
):
    event.listen(ParticipantCorrectionAudit.__table__, "after_create", DDL(statement).execute_if(dialect="postgresql"))
