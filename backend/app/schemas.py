from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class Rule(BaseModel):
    id: int
    title: str
    description: str

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

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
    difficulty_difference: float
    yard_difference: int

class SimulationCourseData(BaseModel):
    course_name: str
    holes: List[HoleInfo]
    difficulty_factors: List[float]  # Per-hole difficulty multipliers
    distance_factors: List[float]    # Per-hole distance impact factors

# Player Profile Schemas
class PlayerProfileBase(BaseModel):
    name: str
    handicap: float = 18.0
    avatar_url: Optional[str] = None
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
    created_date: str
    last_played: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True

# Player Statistics Schemas
class PlayerStatisticsResponse(BaseModel):
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
    favorite_game_mode: str
    preferred_player_count: int
    best_hole_performance: List[Dict[str, Any]]
    worst_hole_performance: List[Dict[str, Any]]
    performance_trends: List[Dict[str, Any]]
    last_updated: str

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

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
    hole_scores: Optional[Dict[str, Any]] = None
    betting_history: Optional[List[Dict[str, Any]]] = None
    performance_metrics: Optional[Dict[str, Any]] = None

class GamePlayerResultResponse(BaseModel):
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
    hole_scores: Dict[str, Any]
    betting_history: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    created_at: str

    class Config:
        from_attributes = True

# Player Achievement Schemas
class PlayerAchievementResponse(BaseModel):
    id: int
    player_profile_id: int
    achievement_type: str
    achievement_name: str
    description: str
    earned_date: str
    game_record_id: Optional[int]
    achievement_data: Dict[str, Any]

    class Config:
        from_attributes = True

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
    player_name: str
    games_played: int
    win_percentage: float
    avg_earnings: float
    total_earnings: float
    partnership_success: float 