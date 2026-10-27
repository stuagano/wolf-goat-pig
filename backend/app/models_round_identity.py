"""Identity evidence on the existing string-UUID game root.

Foreign keys into pre-existing game/social data remain staged until orphan
accounting. New evidence tables can safely constrain their own references.
Observations and resolutions are append-only through ORM unit-of-work writes.
"""

from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String, UniqueConstraint, event

from .database import Base
from .utils.time import utc_now


def new_id():
    return str(uuid4())


def timestamp():
    return utc_now().isoformat()


class RoundSource(Base):
    __tablename__ = "round_sources"
    __table_args__ = (UniqueConstraint("kind", "scope", "round_token", name="uq_round_source_token"),)
    id = Column(String, primary_key=True, default=new_id)
    kind = Column(String, nullable=False)
    scope = Column(String, nullable=False)
    round_token = Column(String, nullable=False)
    game_id = Column(String, nullable=True, index=True)
    binding_evidence = Column(JSON, nullable=True)
    bound_by_profile_id = Column(Integer, nullable=True)
    bound_at = Column(String, nullable=True)
    revision = Column(Integer, nullable=False, default=0, server_default="0")
    latest_observation_key = Column(String, nullable=True)
    snapshot_fingerprint = Column(String, nullable=True)
    created_at = Column(String, nullable=False, default=timestamp)


class RoundObservation(Base):
    __tablename__ = "round_observations"
    __table_args__ = (UniqueConstraint("source_id", "observation_key", name="uq_round_observation_event"),)
    id = Column(String, primary_key=True, default=new_id)
    source_id = Column(String, ForeignKey("round_sources.id"), nullable=False)
    observation_key = Column(String, nullable=False)
    participant_id = Column(String, nullable=True)
    raw_payload = Column(JSON, nullable=False)
    parsed_values = Column(JSON, nullable=True)
    present_fields = Column(JSON, nullable=False, default=dict)
    parse_status = Column(String, nullable=False, default="valid")
    source_revision = Column(String, nullable=True)
    snapshot_fingerprint = Column(String, nullable=True)
    content_fingerprint = Column(String, nullable=True)
    continuity_verified = Column(Boolean, nullable=False, default=False)
    observed_at = Column(String, nullable=False, default=timestamp)


class RoundFieldHead(Base):
    __tablename__ = "round_field_heads"
    __table_args__ = (UniqueConstraint("source_id", "participant_id", "field", name="uq_round_field_head"),)
    id = Column(String, primary_key=True, default=new_id)
    source_id = Column(String, ForeignKey("round_sources.id"), nullable=False)
    # Empty token denotes a round-level field; NULL would defeat uniqueness.
    participant_id = Column(String, nullable=False, default="", server_default="")
    field = Column(String, nullable=False)
    observation_id = Column(String, ForeignKey("round_observations.id"), nullable=True)
    revision = Column(Integer, nullable=False, default=0, server_default="0")
    accepted_revision = Column(Integer, nullable=False, default=0, server_default="0")
    raw_present = Column(Boolean, nullable=False, default=False)
    raw_value = Column(JSON, nullable=True)
    accepted_present = Column(Boolean, nullable=False, default=False)
    accepted_value = Column(JSON, nullable=True)
    proposed_present = Column(Boolean, nullable=False, default=False)
    proposed_value = Column(JSON, nullable=True)
    updated_at = Column(String, nullable=False, default=timestamp)


class RoundIssue(Base):
    __tablename__ = "round_issues"
    id = Column(String, primary_key=True, default=new_id)
    source_id = Column(String, ForeignKey("round_sources.id"), nullable=False)
    game_id = Column(String, nullable=True, index=True)
    kind = Column(String, nullable=False)
    participant_id = Column(String, nullable=False, default="")
    field = Column(String, nullable=True)
    candidate_game_ids = Column(JSON, nullable=False, default=list)
    fingerprint = Column(String, nullable=False)
    status = Column(String, nullable=False, default="open")
    generation = Column(Integer, nullable=False, default=1)
    revision = Column(Integer, nullable=False, default=1)
    head_revision = Column(Integer, nullable=False, default=0)
    baseline_revision = Column(Integer, nullable=False, default=0)
    observation_id = Column(String, ForeignKey("round_observations.id"), nullable=True)
    accepted_present = Column(Boolean, nullable=False, default=False)
    accepted_value = Column(JSON, nullable=True)
    proposed_present = Column(Boolean, nullable=False, default=False)
    proposed_value = Column(JSON, nullable=True)
    created_at = Column(String, nullable=False, default=timestamp)
    last_seen_at = Column(String, nullable=False, default=timestamp)


class RoundResolution(Base):
    __tablename__ = "round_resolutions"
    id = Column(String, primary_key=True, default=new_id)
    issue_id = Column(String, ForeignKey("round_issues.id"), nullable=False)
    actor_profile_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    value_present = Column(Boolean, nullable=False, default=False)
    value = Column(JSON, nullable=True)
    target_game_id = Column(String, nullable=True)
    game_revision = Column(Integer, nullable=True)
    issue_revision = Column(Integer, nullable=False, default=0)
    head_revision = Column(Integer, nullable=False, default=0)
    baseline_revision = Column(Integer, nullable=False, default=0)
    observation_ids = Column(JSON, nullable=False, default=list)
    created_at = Column(String, nullable=False, default=timestamp)


class RoundAlias(Base):
    __tablename__ = "round_aliases"
    __table_args__ = (UniqueConstraint("date_key", "group", "location", "game_id", name="uq_round_alias_target"),)
    id = Column(String, primary_key=True, default=new_id)
    date_key = Column(String, nullable=False)
    group = Column(String, nullable=False)
    location = Column(String, nullable=False)
    game_id = Column(String, nullable=False, index=True)
    evidence = Column(JSON, nullable=True)
    created_at = Column(String, nullable=False, default=timestamp)


class RoundRequest(Base):
    __tablename__ = "round_requests"
    __table_args__ = (UniqueConstraint("actor_profile_id", "request_key", name="uq_round_request_actor_key"),)
    id = Column(String, primary_key=True, default=new_id)
    actor_profile_id = Column(Integer, nullable=False)
    request_key = Column(String, nullable=False)
    fingerprint = Column(String, nullable=False)
    game_id = Column(String, nullable=True)
    outcome = Column(JSON, nullable=True)
    created_at = Column(String, nullable=False, default=timestamp)


class RoundDelivery(Base):
    __tablename__ = "round_deliveries"
    __table_args__ = (
        UniqueConstraint("issue_event_key", "recipient_profile_id", "channel", name="uq_round_delivery_event"),
    )
    id = Column(String, primary_key=True, default=new_id)
    issue_id = Column(String, ForeignKey("round_issues.id"), nullable=True)
    issue_event_key = Column(String, nullable=False)
    recipient_profile_id = Column(Integer, nullable=False)
    channel = Column(String, nullable=False)
    delivery_key = Column(String, nullable=True, unique=True)
    status = Column(String, nullable=False, default="pending")
    attempts = Column(Integer, nullable=False, default=0)
    lease_owner = Column(String, nullable=True)
    lease_expires_at = Column(String, nullable=True)
    provider_receipt = Column(String, nullable=True)
    error = Column(String, nullable=True)
    created_at = Column(String, nullable=False, default=timestamp)
    delivered_at = Column(String, nullable=True)


class RoundIdentityLease(Base):
    __tablename__ = "round_identity_leases"
    key = Column(String, primary_key=True)
    owner = Column(String, nullable=True)
    epoch = Column(Integer, nullable=False, default=0)
    expires_at = Column(String, nullable=True)
    snapshot_fingerprint = Column(String, nullable=True)
    source_version = Column(String, nullable=True)


class RoundMigrationCheckpoint(Base):
    __tablename__ = "round_migration_checkpoints"
    __table_args__ = (
        UniqueConstraint("manifest_checksum", "game_id", "operation_key", name="uq_round_migration_operation"),
    )
    id = Column(String, primary_key=True, default=new_id)
    manifest_checksum = Column(String, nullable=False)
    game_id = Column(String, nullable=False)
    operation_key = Column(String, nullable=False)
    outcome = Column(JSON, nullable=True)
    created_at = Column(String, nullable=False, default=timestamp)


def _reject_evidence_mutation(mapper, connection, target):
    raise ValueError("Round evidence is immutable; append a new event instead")


for _model in (RoundObservation, RoundResolution):
    event.listen(_model, "before_update", _reject_evidence_mutation)
    event.listen(_model, "before_delete", _reject_evidence_mutation)
