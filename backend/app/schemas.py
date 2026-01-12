from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


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
    description: Optional[str] = None
    tee_box: str = "regular"

    @field_validator('par')
    @classmethod
    def validate_par(cls, v):
        if not 3 <= v <= 6:
            raise ValueError('Par must be between 3 and 6')
        return v

    @field_validator('handicap')
    @classmethod
    def validate_handicap(cls, v):
        if not 1 <= v <= 18:
            raise ValueError('Handicap must be between 1 and 18')
        return v

    @field_validator('yards')
    @classmethod
    def validate_yards(cls, v):
        if v < 100:
            raise ValueError('Yards must be at least 100')
        if v > 700:
            raise ValueError('Yards cannot exceed 700')
        return v

class CourseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    holes: List[HoleInfo]

    @field_validator('holes')
    @classmethod
    def validate_holes(cls, v):
        if len(v) != 18:
            raise ValueError('Course must have exactly 18 holes')

        # Check for unique handicaps
        handicaps = [hole.handicap for hole in v]
        if len(set(handicaps)) != 18:
            raise ValueError('All handicaps must be unique (1-18)')

        # Check for unique hole numbers
        hole_numbers = [hole.hole_number for hole in v]
        if sorted(hole_numbers) != list(range(1, 19)):
            raise ValueError('Hole numbers must be 1-18 and unique')

        # Validate total par
        total_par = sum(hole.par for hole in v)
        if not 70 <= total_par <= 74:
            raise ValueError('Total par must be between 70 and 74')

        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Course name must be at least 3 characters')
        return v.strip()

class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    total_par: int
    total_yards: int
    course_rating: Optional[float]
    slope_rating: Optional[float]
    holes: List[HoleInfo]
    created_at: str
    updated_at: str

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    holes: Optional[List[HoleInfo]] = None

    @field_validator('holes')
    @classmethod
    def validate_holes_update(cls, v):
        if v is not None:
            # Same validation as CourseCreate
            if len(v) != 18:
                raise ValueError('Course must have exactly 18 holes')

            handicaps = [hole.handicap for hole in v]
            if len(set(handicaps)) != 18:
                raise ValueError('All handicaps must be unique (1-18)')

            hole_numbers = [hole.hole_number for hole in v]
            if sorted(hole_numbers) != list(range(1, 19)):
                raise ValueError('Hole numbers must be 1-18 and unique')

            total_par = sum(hole.par for hole in v)
            if not 70 <= total_par <= 74:
                raise ValueError('Total par must be between 70 and 74')

        return v

class CourseList(BaseModel):
    courses: List[CourseResponse]

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
    state: Optional[str] = None
    city: Optional[str] = None

# SimulationCourseData schema removed - simulation mode deprecated

# Player Profile Schemas
class PlayerProfileBase(BaseModel):
    name: str
    handicap: float = 18.0
    avatar_url: Optional[str] = None
    email: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class PlayerProfileCreate(PlayerProfileBase):
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Player name must be at least 2 characters')
        if len(v.strip()) > 50:
            raise ValueError('Player name cannot exceed 50 characters')
        return v.strip()

    @field_validator('handicap')
    @classmethod
    def validate_handicap(cls, v):
        if v < 0:
            raise ValueError('Handicap cannot be negative')
        if v > 54:
            raise ValueError('Handicap cannot exceed 54')
        return v

class PlayerProfileUpdate(BaseModel):
    name: Optional[str] = None
    handicap: Optional[float] = None
    avatar_url: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    last_played: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            if len(v.strip()) < 2:
                raise ValueError('Player name must be at least 2 characters')
            if len(v.strip()) > 50:
                raise ValueError('Player name cannot exceed 50 characters')
            return v.strip()
        return v

    @field_validator('handicap')
    @classmethod
    def validate_handicap(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError('Handicap cannot be negative')
            if v > 54:
                raise ValueError('Handicap cannot exceed 54')
        return v

class PlayerProfileResponse(PlayerProfileBase):
    id: int
    created_at: str
    updated_at: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    last_played: Optional[str] = None
    is_active: bool = True
    is_ai: bool = False
    playing_style: Optional[str] = None
    description: Optional[str] = None

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
    best_hole_performance: List[Dict[str, Any]]
    worst_hole_performance: List[Dict[str, Any]]
    performance_trends: List[Dict[str, Any]]
    head_to_head_records: Dict[str, Any] = {}
    last_updated: str

# Game Record Schemas
class GameRecordCreate(BaseModel):
    game_id: str
    course_name: str
    game_mode: str = "wolf_goat_pig"
    player_count: int
    game_settings: Optional[Dict[str, Any]] = None

class GameRecordUpdate(BaseModel):
    completed_at: Optional[str] = None
    game_duration_minutes: Optional[int] = None
    final_scores: Optional[Dict[str, Any]] = None

class GameRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    game_id: str
    course_name: str
    game_mode: str
    player_count: int
    total_holes_played: int
    game_duration_minutes: Optional[int]
    created_at: str
    completed_at: Optional[str]
    game_settings: Dict[str, Any]
    final_scores: Dict[str, Any]

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
    hole_scores: Optional[Dict[str, Any]] = None
    betting_history: Optional[List[Dict[str, Any]]] = None
    performance_metrics: Optional[Dict[str, Any]] = None

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
    hole_scores: Dict[str, Any]
    betting_history: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
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
    game_record_id: Optional[int]
    achievement_data: Dict[str, Any]

# Composite Schemas
class PlayerProfileWithStats(BaseModel):
    profile: PlayerProfileResponse
    statistics: PlayerStatisticsResponse
    recent_achievements: List[PlayerAchievementResponse] = []

class PlayerPerformanceAnalytics(BaseModel):
    player_id: int
    player_name: str
    performance_summary: Dict[str, Any]
    trend_analysis: Dict[str, Any]
    strength_analysis: Dict[str, Any]
    improvement_recommendations: List[str]
    comparative_analysis: Dict[str, Any]

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
    players: List[str]
    course_name: str
    game_settings: Optional[Dict[str, Any]] = None

class OddsCalculationRequest(BaseModel):
    players: List[Dict[str, Any]]
    hole_info: Dict[str, Any]
    current_state: Optional[Dict[str, Any]] = None

class MonteCarloRequest(BaseModel):
    players: List[Dict[str, Any]]
    hole_info: Dict[str, Any]
    simulation_params: Optional[Dict[str, Any]] = None

class ShotAnalysisRequest(BaseModel):
    player_id: str
    distance_to_pin: float
    lie_type: str
    club_options: List[str]

# Daily Sign-up System Schemas
class DailySignupCreate(BaseModel):
    date: str  # YYYY-MM-DD format
    player_profile_id: int
    player_name: str
    preferred_start_time: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')

class DailySignupUpdate(BaseModel):
    preferred_start_time: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class DailySignupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: str
    player_profile_id: int
    player_name: str
    signup_time: str
    preferred_start_time: Optional[str]
    notes: Optional[str]
    status: str
    created_at: str
    updated_at: str

class PlayerAvailabilityCreate(BaseModel):
    player_profile_id: int
    day_of_week: int  # 0-6
    available_from_time: Optional[str] = None
    available_to_time: Optional[str] = None
    is_available: bool = True
    notes: Optional[str] = None

    @field_validator('day_of_week')
    @classmethod
    def validate_day_of_week(cls, v):
        if not 0 <= v <= 6:
            raise ValueError('Day of week must be between 0 (Monday) and 6 (Sunday)')
        return v

class PlayerAvailabilityUpdate(BaseModel):
    available_from_time: Optional[str] = None
    available_to_time: Optional[str] = None
    is_available: Optional[bool] = None
    notes: Optional[str] = None

class PlayerAvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_profile_id: int
    day_of_week: int
    available_from_time: Optional[str]
    available_to_time: Optional[str]
    is_available: bool
    notes: Optional[str]
    created_at: str
    updated_at: str

class EmailPreferencesCreate(BaseModel):
    player_profile_id: int
    daily_signups_enabled: bool = True
    signup_confirmations_enabled: bool = True
    signup_reminders_enabled: bool = True
    game_invitations_enabled: bool = True
    weekly_summary_enabled: bool = True
    email_frequency: str = "daily"  # daily, weekly, monthly, never
    preferred_notification_time: str = "8:00 AM"

    @field_validator('email_frequency')
    @classmethod
    def validate_email_frequency(cls, v):
        allowed_frequencies = ['daily', 'weekly', 'monthly', 'never']
        if v not in allowed_frequencies:
            raise ValueError(f'Email frequency must be one of: {", ".join(allowed_frequencies)}')
        return v

class EmailPreferencesUpdate(BaseModel):
    daily_signups_enabled: Optional[bool] = None
    signup_confirmations_enabled: Optional[bool] = None
    signup_reminders_enabled: Optional[bool] = None
    game_invitations_enabled: Optional[bool] = None
    weekly_summary_enabled: Optional[bool] = None
    email_frequency: Optional[str] = None
    preferred_notification_time: Optional[str] = None

    @field_validator('email_frequency')
    @classmethod
    def validate_email_frequency(cls, v):
        if v is not None:
            allowed_frequencies = ['daily', 'weekly', 'monthly', 'never']
            if v not in allowed_frequencies:
                raise ValueError(f'Email frequency must be one of: {", ".join(allowed_frequencies)}')
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
    signups: List[DailySignupResponse]
    total_count: int

class WeeklySignupView(BaseModel):
    week_start: str  # YYYY-MM-DD for the Monday
    daily_summaries: List[DailySignupSummary]

class PlayerWithAvailability(BaseModel):
    profile: PlayerProfileResponse
    availability: List[PlayerAvailabilityResponse]
    email_preferences: Optional[EmailPreferencesResponse] = None

# Daily Message schemas
class DailyMessageCreate(BaseModel):
    date: str  # YYYY-MM-DD format
    message: str
    player_profile_id: Optional[int] = None
    player_name: Optional[str] = None

class DailyMessageUpdate(BaseModel):
    message: Optional[str] = None

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
    signups: List[DailySignupResponse]
    total_count: int
    messages: List[DailyMessageResponse]
    message_count: int

class WeeklySignupWithMessagesView(BaseModel):
    week_start: str  # YYYY-MM-DD for the Monday
    daily_summaries: List[DailySignupWithMessages]

# Game Banner Schemas
class GameBannerCreate(BaseModel):
    title: Optional[str] = None
    message: str
    banner_type: str = "info"  # info, warning, announcement, rules
    is_active: bool = True
    background_color: str = "#3B82F6"  # Blue
    text_color: str = "#FFFFFF"  # White
    show_icon: bool = True
    dismissible: bool = False

    @field_validator('banner_type')
    @classmethod
    def validate_banner_type(cls, v):
        allowed_types = ['info', 'warning', 'announcement', 'rules']
        if v not in allowed_types:
            raise ValueError(f'Banner type must be one of: {", ".join(allowed_types)}')
        return v

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('Banner message cannot be empty')
        if len(v) > 500:
            raise ValueError('Banner message cannot exceed 500 characters')
        return v.strip()

class GameBannerUpdate(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    banner_type: Optional[str] = None
    is_active: Optional[bool] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    show_icon: Optional[bool] = None
    dismissible: Optional[bool] = None

    @field_validator('banner_type')
    @classmethod
    def validate_banner_type(cls, v):
        if v is not None:
            allowed_types = ['info', 'warning', 'announcement', 'rules']
            if v not in allowed_types:
                raise ValueError(f'Banner type must be one of: {", ".join(allowed_types)}')
        return v

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError('Banner message cannot be empty')
            if len(v) > 500:
                raise ValueError('Banner message cannot exceed 500 characters')
            return v.strip()
        return v

class GameBannerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: Optional[str]
    message: str
    banner_type: str
    is_active: bool
    background_color: str
    text_color: str
    show_icon: bool
    dismissible: bool
    created_at: str
    updated_at: Optional[str]

# Join Game Schemas
class JoinGameRequest(BaseModel):
    player_name: str
    handicap: float = 18.0
    user_id: Optional[str] = None
    player_profile_id: Optional[int] = None

    @field_validator('player_name')
    @classmethod
    def validate_player_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Player name must be at least 2 characters')
        if len(v.strip()) > 50:
            raise ValueError('Player name cannot exceed 50 characters')
        return v.strip()

    @field_validator('handicap')
    @classmethod
    def validate_handicap(cls, v):
        if v < 0:
            raise ValueError('Handicap cannot be negative')
        if v > 54:
            raise ValueError('Handicap cannot exceed 54')
        return v
