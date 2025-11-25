"""
TypedDict Response Models

Provides strongly-typed response models to replace Dict[str, Any]
for better IDE support and type checking.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict, Union


# ============================================================================
# Common Response Types
# ============================================================================

class PaginationMeta(TypedDict):
    """Pagination metadata for list responses."""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class SuccessResponse(TypedDict, total=False):
    """Standard success response structure."""
    success: bool
    message: str
    data: Any
    timestamp: str
    meta: Dict[str, Any]


class ErrorResponse(TypedDict):
    """Standard error response structure."""
    success: bool
    message: str
    code: str
    details: Dict[str, Any]
    status_code: int
    timestamp: str


# ============================================================================
# Player Response Types
# ============================================================================

class PlayerInfo(TypedDict, total=False):
    """Basic player information."""
    id: str
    name: str
    handicap: float
    profile_id: Optional[int]
    tee_order: Optional[int]


class PlayerProfileResponse(TypedDict, total=False):
    """Full player profile response."""
    id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    handicap: float
    ghin_number: Optional[str]
    home_course: Optional[str]
    created_at: str
    updated_at: str
    is_active: bool
    last_played: Optional[str]


class PlayerStatisticsResponse(TypedDict, total=False):
    """Player statistics response."""
    player_id: int
    games_played: int
    wins: int
    losses: int
    total_earnings: float
    average_score: float
    best_score: int
    holes_won: int
    solo_attempts: int
    solo_wins: int
    partnerships_formed: int
    partnerships_won: int


# ============================================================================
# Game Response Types
# ============================================================================

class HoleInfo(TypedDict):
    """Golf hole information."""
    number: int
    par: int
    yards: int
    handicap_index: int


class CourseInfo(TypedDict, total=False):
    """Golf course information."""
    id: int
    name: str
    par: int
    holes: List[HoleInfo]
    total_yards: int
    slope_rating: Optional[float]
    course_rating: Optional[float]


class GameLobbyResponse(TypedDict):
    """Game lobby state response."""
    game_id: str
    join_code: str
    status: str
    course_name: Optional[str]
    max_players: int
    players_joined: int
    players: List[PlayerInfo]
    tee_order_set: bool
    created_at: str


class HoleScores(TypedDict):
    """Scores for a single hole."""
    hole_number: int
    scores: Dict[str, int]  # player_id -> gross score
    net_scores: Dict[str, float]  # player_id -> net score
    winner: Optional[str]
    wager: int
    points_changes: Dict[str, int]


class GameStateResponse(TypedDict, total=False):
    """Current game state response."""
    game_id: str
    status: str
    current_hole: int
    players: List[PlayerInfo]
    rotation_order: List[str]
    current_wolf: str
    scores: Dict[str, Dict[int, int]]  # player_id -> hole -> score
    points: Dict[str, int]  # player_id -> points
    hole_history: List[HoleScores]
    active: bool
    game_complete: bool


class HoleResultResponse(TypedDict):
    """Result of completing a hole."""
    success: bool
    message: str
    hole_number: int
    winners: List[str]
    points_changes: Dict[str, int]
    current_standings: Dict[str, int]
    next_wolf: Optional[str]


class GameCompletionResponse(TypedDict):
    """Game completion summary."""
    game_id: str
    status: str
    final_standings: List[Dict[str, Any]]
    total_holes: int
    winner: str
    winner_points: int
    duration_minutes: int
    completed_at: str


# ============================================================================
# Betting Response Types
# ============================================================================

class BetInfo(TypedDict, total=False):
    """Information about a bet."""
    bet_id: str
    bet_type: str
    amount: int
    player_id: str
    hole_number: int
    status: str
    created_at: str


class BettingStateResponse(TypedDict):
    """Current betting state."""
    base_wager: int
    current_multiplier: int
    active_presses: List[BetInfo]
    total_at_risk: int
    can_press: bool


class BettingOddsResponse(TypedDict):
    """Betting odds calculation response."""
    hole_number: int
    players: Dict[str, float]  # player_id -> win probability
    recommended_action: str
    expected_value: float


# ============================================================================
# Analytics Response Types
# ============================================================================

class AnalyticsSummary(TypedDict, total=False):
    """Analytics summary response."""
    period_start: str
    period_end: str
    games_analyzed: int
    total_holes: int
    average_score: float
    scoring_distribution: Dict[str, int]
    best_performance: Dict[str, Any]
    trends: Dict[str, Any]


class HoleAnalytics(TypedDict):
    """Per-hole analytics."""
    hole_number: int
    par: int
    average_score: float
    birdie_rate: float
    par_rate: float
    bogey_rate: float
    double_plus_rate: float


# ============================================================================
# Simulation Response Types
# ============================================================================

class SimulationSetupResponse(TypedDict):
    """Simulation setup response."""
    simulation_id: str
    players: List[PlayerInfo]
    course: CourseInfo
    config: Dict[str, Any]
    status: str


class SimulationStateResponse(TypedDict, total=False):
    """Current simulation state."""
    simulation_id: str
    current_hole: int
    game_state: GameStateResponse
    betting_state: BettingStateResponse
    ai_recommendations: Dict[str, Any]
    probabilities: Dict[str, float]


class SimulationResultResponse(TypedDict):
    """Simulation result response."""
    simulation_id: str
    outcome: str
    final_scores: Dict[str, int]
    winner: str
    statistics: Dict[str, Any]
    duration_ms: int


# ============================================================================
# Health & Status Response Types
# ============================================================================

class HealthCheckResponse(TypedDict):
    """Health check response."""
    status: str
    timestamp: str
    version: str
    database: str
    cache: str
    uptime_seconds: int


class ServiceStatusResponse(TypedDict):
    """Service status response."""
    service: str
    status: str
    last_check: str
    details: Dict[str, Any]


# ============================================================================
# Type Aliases for Common Patterns
# ============================================================================

# Generic ID to value mapping
IdValueMap = Dict[str, Any]

# Player ID to score mapping
PlayerScoreMap = Dict[str, int]

# Hole number to score mapping
HoleScoreMap = Dict[int, int]

# Full score matrix: player -> hole -> score
ScoreMatrix = Dict[str, Dict[int, int]]
