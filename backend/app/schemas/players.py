from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Player Profile Schemas
class PlayerProfileBase(BaseModel):
    name: str
    legacy_name: str | None = None  # Name in legacy tee sheet system (thousand-cranes.com)
    handicap: float = 18.0
    avatar_url: str | None = None
    email: str | None = None
    preferences: dict[str, Any] | None = None


class PlayerProfileCreate(PlayerProfileBase):
    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("Player name must be at least 2 characters")
        if len(v.strip()) > 50:
            raise ValueError("Player name cannot exceed 50 characters")
        return v.strip()

    @field_validator("handicap")
    @classmethod
    def validate_handicap(cls, v):
        if v < 0:
            raise ValueError("Handicap cannot be negative")
        if v > 54:
            raise ValueError("Handicap cannot exceed 54")
        return v


class PlayerProfileUpdate(BaseModel):
    name: str | None = None
    legacy_name: str | None = None  # Name in legacy tee sheet system
    handicap: float | None = None
    avatar_url: str | None = None
    email: str | None = None
    ghin_id: str | None = None
    preferences: dict[str, Any] | None = None
    last_played: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            if len(v.strip()) < 2:
                raise ValueError("Player name must be at least 2 characters")
            if len(v.strip()) > 50:
                raise ValueError("Player name cannot exceed 50 characters")
            return v.strip()
        return v

    @field_validator("handicap")
    @classmethod
    def validate_handicap(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError("Handicap cannot be negative")
            if v > 54:
                raise ValueError("Handicap cannot exceed 54")
        return v


class PendingClaimInfo(BaseModel):
    """A claim this player made on an original profile, waiting for an admin."""

    canonical_name: str
    created_at: str | None = None


class PlayerProfileResponse(PlayerProfileBase):
    id: int
    created_at: str
    updated_at: str | None = None
    model_config = ConfigDict(from_attributes=True)

    last_played: str | None = None
    is_active: bool = True
    is_ai: bool = False
    ghin_id: str | None = None
    ghin_last_updated: str | None = None  # when the GHIN handicap was last synced (#320)
    # Provenance of `handicap`: "default" (18.0 placeholder / unknown), "ghin"
    # (authoritative), or "manual". Lets the UI distinguish unknown from a real
    # 18.0. See issue #320.
    handicap_source: str | None = None
    venmo_handle: str | None = None
    playing_style: str | None = None
    description: str | None = None
    has_avatar_image: bool = False
    # Computed, not stored. Populated by GET /players/me only.
    # A non-authoritative fuzzy legacy-name suggestion to confirm in onboarding;
    # never auto-persisted to legacy_name. See issue #322.
    legacy_name_suggestion: str | None = None
    # Computed in GET /players/me only; never an ORM attribute (see PR #373).
    pending_claim: PendingClaimInfo | None = None
    # Computed authorization fields returned only by GET /players/me.
    role: Literal["normal", "admin", "super_admin"] = "normal"
    is_super_admin: bool = False
    # Backwards-compatible alias while older clients still read is_admin.
    is_admin: bool = False


class PublicPlayerProfileResponse(PlayerProfileResponse):
    """Profile for unauthenticated reads (lists, name lookup): never exposes email."""

    email: str | None = Field(default=None, exclude=True)


# Player Statistics Schemas
class PlayerStatisticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int
    games_played: int
    games_won: int
    known_participation_count: int = 0
    incomplete_round_count: int = 0
    total_earnings: float
    holes_played: int | None
    holes_won: int | None
    avg_earnings_per_hole: float | None
    betting_success_rate: float | None
    successful_bets: int | None
    total_bets: int | None
    partnership_success_rate: float | None
    partnerships_formed: int | None
    partnerships_won: int | None
    solo_attempts: int | None
    solo_wins: int | None
    # Special event stats
    ping_pong_count: int | None = None
    ping_pong_wins: int | None = None
    invisible_aardvark_appearances: int | None = None
    invisible_aardvark_wins: int | None = None
    # Specific solo type stats
    duncan_attempts: int | None = None
    duncan_wins: int | None = None
    tunkarri_attempts: int | None = None
    tunkarri_wins: int | None = None
    big_dick_attempts: int | None = None
    big_dick_wins: int | None = None
    # Score performance metrics
    eagles: int | None = None
    birdies: int | None = None
    pars: int | None = None
    bogeys: int | None = None
    double_bogeys: int | None = None
    worse_than_double: int | None = None
    # Streak tracking
    current_win_streak: int = 0
    current_loss_streak: int = 0
    best_win_streak: int = 0
    worst_loss_streak: int = 0
    # Role tracking
    times_as_wolf: int | None = None
    times_as_goat: int | None = None
    times_as_pig: int | None = None
    times_as_aardvark: int | None = None
    favorite_game_mode: str
    preferred_player_count: int
    best_hole_performance: list[dict[str, Any]] = []
    worst_hole_performance: list[dict[str, Any]] = []
    performance_trends: list[dict[str, Any]] = []
    head_to_head_records: dict[str, Any] = {}
    last_updated: str

    # Rows written before these JSON columns existed store SQL NULL, which
    # Pydantic rejects because a field default never applies to an explicit
    # None. Coerce so historical stats stay readable instead of 500ing.
    @field_validator(
        "best_hole_performance",
        "worst_hole_performance",
        "performance_trends",
        mode="before",
    )
    @classmethod
    def default_empty_list(cls, v):
        return [] if v is None else v

    @field_validator("head_to_head_records", mode="before")
    @classmethod
    def default_empty_dict(cls, v):
        return {} if v is None else v


# Player Achievement Schemas
class PlayerAchievementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_profile_id: int
    achievement_type: str
    achievement_name: str
    description: str
    earned_date: str
    game_record_id: int | None
    achievement_data: dict[str, Any]


# Composite Schemas
class PlayerProfileWithStats(BaseModel):
    profile: PlayerProfileResponse
    statistics: PlayerStatisticsResponse
    recent_achievements: list[PlayerAchievementResponse] = []


class PlayerPerformanceAnalytics(BaseModel):
    player_id: int
    player_name: str
    performance_summary: dict[str, Any]
    trend_analysis: dict[str, Any]
    strength_analysis: dict[str, Any]
    improvement_recommendations: list[str]
    comparative_analysis: dict[str, Any]


class LeaderboardEntry(BaseModel):
    rank: int
    player_id: int
    player_name: str
    games_played: int
    win_percentage: float
    avg_earnings: float | None
    total_earnings: float
    partnership_success: float | None
