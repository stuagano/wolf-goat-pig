"""Shared identity contracts. Missing values never imply zero or removal."""

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy.orm import Session


class RoundParticipant(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    participant_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    profile_id: int | None = None
    quarters: float | None = None

    @field_validator("quarters", mode="before")
    @classmethod
    def representable_total(cls, value):
        if value is None:
            return None
        try:
            number = float(value)
            exact = Decimal(str(value))
            if isinstance(value, bool) or not exact.is_finite() or Decimal(str(number)) != exact:
                raise ValueError("Quarters must be finite and representable without precision loss")
        except (TypeError, OverflowError, InvalidOperation) as exc:
            raise ValueError("Invalid quarter total") from exc
        return number


class RoundDraft(BaseModel):
    played_on: date | None = None
    raw_date: str | None = None
    course_name: str | None = None
    group: str | None = None
    players: list[RoundParticipant] = Field(default_factory=list)
    roster_complete: bool = False
    detail_coverage: Literal["totals_only", "partial", "per_hole_complete"] = "totals_only"
    hole_history: list[dict] = Field(default_factory=list)
    actor_profile_id: int | None = None
    clear_fields: list[str] = Field(default_factory=list)
    removed_participant_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_participants(self):
        tokens = [p.participant_id for p in self.players]
        profiles = [p.profile_id for p in self.players if p.profile_id is not None]
        if len(tokens) != len(set(tokens)) or len(profiles) != len(set(profiles)):
            raise ValueError("Duplicate participant token or profile ID")
        allowed = {"played_on", "raw_date", "course_name", "group"}
        allowed.update(f"players.{token}.{field}" for token in tokens for field in ("quarters", "profile_id"))
        if len(self.clear_fields) != len(set(self.clear_fields)) or not set(self.clear_fields) <= allowed:
            raise ValueError("Unknown or duplicate explicit clear field")
        if len(self.removed_participant_ids) != len(set(self.removed_participant_ids)) or not set(
            self.removed_participant_ids
        ) <= set(tokens):
            raise ValueError("Removal requires distinct known stable participant slots")
        if any("." in token for token in tokens):
            raise ValueError("Participant tokens cannot contain a field-path separator")
        return self


class SourceRef(BaseModel):
    kind: str
    scope: str
    round_token: str


class IngestOutcome(BaseModel):
    status: Literal["accepted", "unchanged", "held"]
    game_id: str | None = None
    issue_ids: list[str] = Field(default_factory=list)
    revision: int | None = None


class ResolutionDecision(BaseModel):
    action: Literal["keep", "accept", "correct", "bind_existing", "confirm_distinct", "retract"]
    value: object | None = None
    target_game_id: str | None = None
    reason: str = Field(min_length=1)
    expected_game_revision: int | None = None
    expected_target_game_revision: int | None = Field(default=None, ge=0, strict=True)
    expected_issue_revision: int
    expected_head_revision: int


class RoundIdentityConfig(BaseModel):
    """Non-secret writer fence and routing state; absence never activates it."""

    mode: Literal["legacy", "paused", "canonical"] = "legacy"
    epoch: int = Field(default=0, ge=0)
    season: int | None = None
    reviewer_profile_id: int | None = None
    routing_confirmed: bool = False
    routing_confirmed_by_profile_id: int | None = None
    routing_confirmed_at: str | None = None
    routing_linkage_evidence: dict = Field(default_factory=dict)


def read_round_identity_config(db: Session) -> RoundIdentityConfig:
    from app.models import AppConfig

    row = db.get(AppConfig, "round_identity")
    return RoundIdentityConfig.model_validate(row.value if row else {})
