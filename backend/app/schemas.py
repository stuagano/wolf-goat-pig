from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Rule(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str


class HoleInfo(BaseModel):
    hole_number: int
    par: int
    yards: int
    handicap: int  # Stroke index (1-18)
    description: str | None = None
    tee_box: str = "regular"

    @field_validator("par")
    @classmethod
    def validate_par(cls, v):
        if not 3 <= v <= 6:
            raise ValueError("Par must be between 3 and 6")
        return v

    @field_validator("handicap")
    @classmethod
    def validate_handicap(cls, v):
        if not 1 <= v <= 18:
            raise ValueError("Handicap must be between 1 and 18")
        return v

    @field_validator("yards")
    @classmethod
    def validate_yards(cls, v):
        if v < 100:
            raise ValueError("Yards must be at least 100")
        if v > 700:
            raise ValueError("Yards cannot exceed 700")
        return v


class CourseCreate(BaseModel):
    name: str
    description: str | None = None
    holes: list[HoleInfo]

    @field_validator("holes")
    @classmethod
    def validate_holes(cls, v):
        if len(v) != 18:
            raise ValueError("Course must have exactly 18 holes")

        # Check for unique handicaps
        handicaps = [hole.handicap for hole in v]
        if len(set(handicaps)) != 18:
            raise ValueError("All handicaps must be unique (1-18)")

        # Check for unique hole numbers
        hole_numbers = [hole.hole_number for hole in v]
        if sorted(hole_numbers) != list(range(1, 19)):
            raise ValueError("Hole numbers must be 1-18 and unique")

        # Validate total par
        total_par = sum(hole.par for hole in v)
        if not 70 <= total_par <= 74:
            raise ValueError("Total par must be between 70 and 74")

        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError("Course name must be at least 3 characters")
        return v.strip()


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    total_par: int
    total_yards: int
    course_rating: float | None
    slope_rating: float | None
    holes: list[HoleInfo]
    created_at: str
    updated_at: str


class CourseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    holes: list[HoleInfo] | None = None

    @field_validator("holes")
    @classmethod
    def validate_holes_update(cls, v):
        if v is not None:
            # Same validation as CourseCreate
            if len(v) != 18:
                raise ValueError("Course must have exactly 18 holes")

            handicaps = [hole.handicap for hole in v]
            if len(set(handicaps)) != 18:
                raise ValueError("All handicaps must be unique (1-18)")

            hole_numbers = [hole.hole_number for hole in v]
            if sorted(hole_numbers) != list(range(1, 19)):
                raise ValueError("Hole numbers must be 1-18 and unique")

            total_par = sum(hole.par for hole in v)
            if not 70 <= total_par <= 74:
                raise ValueError("Total par must be between 70 and 74")

        return v


class CourseList(BaseModel):
    courses: list[CourseResponse]


class CourseStats(BaseModel):
    total_par: int
    total_yards: int
    par_3_count: int
    par_4_count: int
    par_5_count: int
    average_yards_per_hole: float
    longest_hole: HoleInfo
    shortest_hole: HoleInfo
    difficulty_rating: float


class CourseComparison(BaseModel):
    course1: CourseResponse
    course2: CourseResponse
    stats1: CourseStats
    stats2: CourseStats


class CourseImportRequest(BaseModel):
    course_name: str
    state: str | None = None
    city: str | None = None


# SimulationCourseData schema removed - simulation mode deprecated


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


# Game Record Schemas
class GameRecordCreate(BaseModel):
    game_id: str
    course_name: str
    game_mode: str = "wolf_goat_pig"
    player_count: int
    game_settings: dict[str, Any] | None = None


class GameRecordUpdate(BaseModel):
    completed_at: str | None = None
    game_duration_minutes: int | None = None
    final_scores: dict[str, Any] | None = None


class GameRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    game_id: str
    course_name: str
    game_mode: str
    player_count: int
    total_holes_played: int
    game_duration_minutes: int | None
    created_at: str
    completed_at: str | None
    game_settings: dict[str, Any]
    final_scores: dict[str, Any]


# Game Player Result Schemas
class GamePlayerResultCreate(BaseModel):
    game_record_id: int
    player_profile_id: int
    player_name: str
    final_position: int
    total_earnings: float = 0.0
    holes_won: int = 0
    successful_bets: int = 0
    total_bets: int = 0
    partnerships_formed: int = 0
    partnerships_won: int = 0
    solo_attempts: int = 0
    solo_wins: int = 0
    # Special event tracking per game
    ping_pongs: int = 0
    ping_pongs_won: int = 0
    invisible_aardvark_holes: int = 0
    invisible_aardvark_holes_won: int = 0
    # Specific solo types per game
    duncan_attempts: int = 0
    duncan_wins: int = 0
    tunkarri_attempts: int = 0
    tunkarri_wins: int = 0
    big_dick_attempts: int = 0
    big_dick_wins: int = 0
    hole_scores: dict[str, Any] | None = None
    betting_history: list[dict[str, Any]] | None = None
    performance_metrics: dict[str, Any] | None = None


class GamePlayerResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    game_record_id: int
    player_profile_id: int
    player_name: str
    final_position: int
    total_earnings: float
    holes_won: int
    successful_bets: int
    total_bets: int
    partnerships_formed: int
    partnerships_won: int
    solo_attempts: int
    solo_wins: int
    # Special event tracking per game
    ping_pongs: int = 0
    ping_pongs_won: int = 0
    invisible_aardvark_holes: int = 0
    invisible_aardvark_holes_won: int = 0
    # Specific solo types per game
    duncan_attempts: int = 0
    duncan_wins: int = 0
    tunkarri_attempts: int = 0
    tunkarri_wins: int = 0
    big_dick_attempts: int = 0
    big_dick_wins: int = 0
    hole_scores: dict[str, Any]
    betting_history: list[dict[str, Any]]
    performance_metrics: dict[str, Any]
    created_at: str


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


# Game Setup and Simulation Schemas
class GameSetupRequest(BaseModel):
    players: list[str]
    course_name: str
    game_settings: dict[str, Any] | None = None


class OddsCalculationRequest(BaseModel):
    players: list[dict[str, Any]]
    hole_info: dict[str, Any]
    current_state: dict[str, Any] | None = None


class MonteCarloRequest(BaseModel):
    players: list[dict[str, Any]]
    hole_info: dict[str, Any]
    simulation_params: dict[str, Any] | None = None


class ShotAnalysisRequest(BaseModel):
    player_id: str
    distance_to_pin: float
    lie_type: str
    club_options: list[str]


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


# Join Game Schemas
class JoinGameRequest(BaseModel):
    player_name: str
    handicap: float = 18.0
    user_id: str | None = None
    player_profile_id: int | None = None

    @field_validator("player_name")
    @classmethod
    def validate_player_name(cls, v):
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


# ============================================================================
# Action API Models (moved from main.py)
# ============================================================================


class ActionRequest(BaseModel):
    """Unified action request for all game interactions"""

    model_config = {"extra": "allow"}  # Allow extra fields for backward compatibility
    action_type: str  # INITIALIZE_GAME, PLAY_SHOT, REQUEST_PARTNERSHIP, etc.
    payload: dict[str, Any] | None = None


class ActionResponse(BaseModel):
    """Standard response structure for all actions"""

    game_state: dict[str, Any]
    log_message: str
    available_actions: list[dict[str, Any]]
    timeline_event: dict[str, Any] | None = None


class HoleTeams(BaseModel):
    """Team configuration for a hole"""

    type: str  # 'partners' or 'solo'
    team1: list[str] | None = None  # Player IDs for team 1 (partners mode)
    team2: list[str] | None = None  # Player IDs for team 2 (partners mode)
    captain: str | None = None  # Captain player ID (solo mode)
    opponents: list[str] | None = None  # Opponent player IDs (solo mode)


class ManualPointsOverride(BaseModel):
    """Manual override for a single player's quarters on a hole"""

    player_id: str
    quarters: float


class CompleteHoleRequest(BaseModel):
    """Request to complete a hole with all data at once - for scorekeeper mode"""

    hole_number: int = Field(..., ge=1, le=18)
    rotation_order: list[str] = Field(..., description="Hitting order for this hole")
    captain_index: int = Field(0, ge=0, description="Index in rotation_order who is captain")
    phase: str | None = Field("normal", description="Game phase: 'normal' or 'hoepfinger'")
    joes_special_wager: int | None = Field(None, description="Wager set by Goat (2, 4, or 8) during Hoepfinger")
    option_turned_off: bool | None = Field(False, description="Captain proactively turned off The Option")
    duncan_invoked: bool | None = Field(False, description="Captain went solo before hitting (3-for-2 payout)")
    tunkarri_invoked: bool | None = Field(False, description="Aardvark went solo before Captain hit (3-for-2 payout)")
    teams: HoleTeams
    final_wager: float = Field(..., gt=0)
    winner: str  # 'team1', 'team2', 'captain', 'opponents', or 'push' for completed holes; 'team1_flush', 'team2_flush', 'captain_flush', 'opponents_flush' for folded holes
    scores: dict[str, int] = Field(..., description="Player ID to strokes mapping")
    hole_par: int | None = Field(4, ge=3, le=5)
    float_invoked_by: str | None = Field(None, description="Player ID who invoked float on this hole")
    option_invoked_by: str | None = Field(None, description="Player ID who triggered option on this hole")
    carry_over_applied: bool | None = Field(False, description="Whether carry-over was applied to this hole")
    doubles_history: list[dict] | None = Field(None, description="Pre-hole doubles offered and accepted")
    big_dick_invoked_by: str | None = Field(None, description="Player ID who invoked The Big Dick on hole 18")
    # Phase 5: The Aardvark (5-man game mechanics)
    aardvark_requested_team: str | None = Field(
        None, description="Team Aardvark requested to join ('team1' or 'team2')"
    )
    aardvark_tossed: bool | None = Field(False, description="Whether Aardvark was tossed by requested team")
    aardvark_ping_ponged: bool | None = Field(
        False, description="Whether Aardvark was re-tossed (ping-ponged) by second team"
    )
    aardvark_solo: bool | None = Field(False, description="Whether Aardvark went solo (1v4)")
    # Manual override controls
    manual_points_override: ManualPointsOverride | None = Field(
        None, description="Manual override for a player's quarters"
    )
    # Interactive betting tracking
    betting_narrative: str | None = Field(
        None,
        description="Human-readable narrative of betting actions (e.g., 'Stuart doubles -> accepted')",
    )
    betting_events: list[dict] | None = Field(None, description="List of betting events for this hole")


class RotationSelectionRequest(BaseModel):
    """Request to select rotation position - for 5-man games on holes 16-18"""

    hole_number: int = Field(..., ge=16, le=18, description="Hole number (16, 17, or 18)")
    goat_player_id: str = Field(..., description="Player ID of the Goat (lowest points)")
    selected_position: int = Field(..., ge=1, le=5, description="Desired position in rotation (1-5)")
