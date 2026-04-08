from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from .players import PlayerProfileResponse


# Daily Sign-up System Schemas
class DailySignupCreate(BaseModel):
    date: str  # YYYY-MM-DD format
    player_profile_id: int
    player_name: str
    preferred_start_time: str | None = None
    notes: str | None = None

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")


class DailySignupUpdate(BaseModel):
    preferred_start_time: str | None = None
    notes: str | None = None
    status: str | None = None


class DailySignupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: str
    player_profile_id: int
    player_name: str
    signup_time: str
    preferred_start_time: str | None
    notes: str | None
    status: str
    created_at: str
    updated_at: str


class PlayerAvailabilityCreate(BaseModel):
    player_profile_id: int
    day_of_week: int  # 0-6
    available_from_time: str | None = None
    available_to_time: str | None = None
    is_available: int = 1  # 1=available, 0=not available
    notes: str | None = None

    @field_validator("day_of_week")
    @classmethod
    def validate_day_of_week(cls, v):
        if not 0 <= v <= 6:
            raise ValueError("Day of week must be between 0 (Monday) and 6 (Sunday)")
        return v


class PlayerAvailabilityUpdate(BaseModel):
    available_from_time: str | None = None
    available_to_time: str | None = None
    is_available: int | None = None  # 1=available, 0=not available
    notes: str | None = None


class PlayerAvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_profile_id: int
    day_of_week: int
    available_from_time: str | None
    available_to_time: str | None
    is_available: bool
    notes: str | None
    created_at: str
    updated_at: str


class PlayerAvailabilityWithMatchesResponse(BaseModel):
    """Response for availability save that includes any new matches found."""

    availability: PlayerAvailabilityResponse
    new_matches: list[dict[str, Any]] = []
    matches_notified: int = 0


# Match Suggestion Schemas
class MatchPlayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    match_suggestion_id: int
    player_profile_id: int
    player_name: str
    player_email: str
    response: str | None = None
    responded_at: str | None = None
    created_at: str


class MatchSuggestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    day_of_week: int
    suggested_date: str | None = None
    overlap_start: str
    overlap_end: str
    suggested_tee_time: str
    match_quality_score: float
    status: str
    notification_sent: bool = False
    created_at: str
    expires_at: str
    players: list[MatchPlayerResponse] = []


class MatchResponseRequest(BaseModel):
    """Request body for accepting/declining a match suggestion."""

    response: str  # "accepted" or "declined"

    @field_validator("response")
    @classmethod
    def validate_response(cls, v):
        allowed = ["accepted", "declined"]
        if v not in allowed:
            raise ValueError(f"Response must be one of: {', '.join(allowed)}")
        return v


class EmailPreferencesCreate(BaseModel):
    player_profile_id: int
    daily_signups_enabled: bool = True
    signup_confirmations_enabled: bool = True
    signup_reminders_enabled: bool = True
    game_invitations_enabled: bool = True
    weekly_summary_enabled: bool = True
    email_frequency: str = "daily"  # daily, weekly, monthly, never
    preferred_notification_time: str = "8:00 AM"

    @field_validator("email_frequency")
    @classmethod
    def validate_email_frequency(cls, v):
        allowed_frequencies = ["daily", "weekly", "monthly", "never"]
        if v not in allowed_frequencies:
            raise ValueError(f"Email frequency must be one of: {', '.join(allowed_frequencies)}")
        return v


class EmailPreferencesUpdate(BaseModel):
    daily_signups_enabled: bool | None = None
    signup_confirmations_enabled: bool | None = None
    signup_reminders_enabled: bool | None = None
    game_invitations_enabled: bool | None = None
    weekly_summary_enabled: bool | None = None
    email_frequency: str | None = None
    preferred_notification_time: str | None = None

    @field_validator("email_frequency")
    @classmethod
    def validate_email_frequency(cls, v):
        if v is not None:
            allowed_frequencies = ["daily", "weekly", "monthly", "never"]
            if v not in allowed_frequencies:
                raise ValueError(f"Email frequency must be one of: {', '.join(allowed_frequencies)}")
        return v


class EmailPreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_profile_id: int
    daily_signups_enabled: bool
    signup_confirmations_enabled: bool
    signup_reminders_enabled: bool
    game_invitations_enabled: bool
    weekly_summary_enabled: bool
    email_frequency: str
    preferred_notification_time: str
    created_at: str
    updated_at: str


# Composite schemas for frontend
class DailySignupSummary(BaseModel):
    date: str
    signups: list[DailySignupResponse]
    total_count: int


class WeeklySignupView(BaseModel):
    week_start: str  # YYYY-MM-DD for the Monday
    daily_summaries: list[DailySignupSummary]


class PlayerWithAvailability(BaseModel):
    profile: PlayerProfileResponse
    availability: list[PlayerAvailabilityResponse]
    email_preferences: EmailPreferencesResponse | None = None


# Daily Message schemas
class DailyMessageCreate(BaseModel):
    date: str  # YYYY-MM-DD format
    message: str
    player_profile_id: int | None = None
    player_name: str | None = None


class DailyMessageUpdate(BaseModel):
    message: str | None = None


class DailyMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: str
    player_profile_id: int
    player_name: str
    message: str
    message_time: str
    is_active: int
    created_at: str
    updated_at: str


# Extended daily summary to include messages
class DailySignupWithMessages(BaseModel):
    date: str
    signups: list[DailySignupResponse]
    total_count: int
    messages: list[DailyMessageResponse]
    message_count: int


class WeeklySignupWithMessagesView(BaseModel):
    week_start: str  # YYYY-MM-DD for the Monday
    daily_summaries: list[DailySignupWithMessages]


# Game Banner Schemas
class GameBannerCreate(BaseModel):
    title: str | None = None
    message: str
    banner_type: str = "info"  # info, warning, announcement, rules
    is_active: bool = True
    background_color: str = "#3B82F6"  # Blue
    text_color: str = "#FFFFFF"  # White
    show_icon: bool = True
    dismissible: bool = False

    @field_validator("banner_type")
    @classmethod
    def validate_banner_type(cls, v):
        allowed_types = ["info", "warning", "announcement", "rules"]
        if v not in allowed_types:
            raise ValueError(f"Banner type must be one of: {', '.join(allowed_types)}")
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError("Banner message cannot be empty")
        if len(v) > 500:
            raise ValueError("Banner message cannot exceed 500 characters")
        return v.strip()


class GameBannerUpdate(BaseModel):
    title: str | None = None
    message: str | None = None
    banner_type: str | None = None
    is_active: bool | None = None
    background_color: str | None = None
    text_color: str | None = None
    show_icon: bool | None = None
    dismissible: bool | None = None

    @field_validator("banner_type")
    @classmethod
    def validate_banner_type(cls, v):
        if v is not None:
            allowed_types = ["info", "warning", "announcement", "rules"]
            if v not in allowed_types:
                raise ValueError(f"Banner type must be one of: {', '.join(allowed_types)}")
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError("Banner message cannot be empty")
            if len(v) > 500:
                raise ValueError("Banner message cannot exceed 500 characters")
            return v.strip()
        return v


class GameBannerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None
    message: str
    banner_type: str
    is_active: bool
    background_color: str
    text_color: str
    show_icon: bool
    dismissible: bool
    created_at: str
    updated_at: str | None
