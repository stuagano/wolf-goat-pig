from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


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


class PlayerProfileResponse(PlayerProfileBase):
    id: int
    created_at: str
    updated_at: str | None = None
    model_config = ConfigDict(from_attributes=True)

    last_played: str | None = None
    is_active: bool = True
    is_ai: bool = False
    ghin_id: str | None = None
    playing_style: str | None = None
    description: str | None = None


# Player Statistics Schemas
class PlayerStatisticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int
    games_played: int
    games_won: int
    total_earnings: float
    holes_played: int
    holes_won: int
    avg_earnings_per_hole: float
    betting_success_rate: float
    successful_bets: int
    total_bets: int
    partnership_success_rate: float
    partnerships_formed: int
    partnerships_won: int
    solo_attempts: int
    solo_wins: int
    # Special event stats
    ping_pong_count: int = 0
    ping_pong_wins: int = 0
    invisible_aardvark_appearances: int = 0
    invisible_aardvark_wins: int = 0
    # Specific solo type stats
    duncan_attempts: int = 0
    duncan_wins: int = 0
    tunkarri_attempts: int = 0
    tunkarri_wins: int = 0
    big_dick_attempts: int = 0
    big_dick_wins: int = 0
    # Score performance metrics
    eagles: int = 0
    birdies: int = 0
    pars: int = 0
    bogeys: int = 0
    double_bogeys: int = 0
    worse_than_double: int = 0
    # Streak tracking
    current_win_streak: int = 0
    current_loss_streak: int = 0
    best_win_streak: int = 0
    worst_loss_streak: int = 0
    # Role tracking
    times_as_wolf: int = 0
    times_as_goat: int = 0
    times_as_pig: int = 0
    times_as_aardvark: int = 0
    favorite_game_mode: str
    preferred_player_count: int
    best_hole_performance: list[dict[str, Any]]
    worst_hole_performance: list[dict[str, Any]]
    performance_trends: list[dict[str, Any]]
    head_to_head_records: dict[str, Any] = {}
    last_updated: str


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
    avg_earnings: float
    total_earnings: float
    partnership_success: float
