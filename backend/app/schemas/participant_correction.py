"""Strict bounded correction input: no client actor or arbitrary fields."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ParticipantCorrection(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    replacement_profile_id: int = Field(gt=0)
    expected_old_profile_id: int | None
    expected_epoch: int = Field(ge=0)
    expected_snapshot: str = Field(min_length=64, max_length=64)
    reason: str = Field(min_length=1, max_length=1000)
    confirmed: Literal[True]
    request_key: str = Field(min_length=1, max_length=200)

    @field_validator("confirmed", mode="before")
    @classmethod
    def explicit_confirmation(cls, value):
        if value is not True:
            raise ValueError("Explicit true confirmation required")
        return value

    @field_validator("reason", "request_key")
    @classmethod
    def non_blank(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Must not be blank")
        return value
