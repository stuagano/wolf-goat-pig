"""
TypedDict Response Models

Provides strongly-typed response models to replace Dict[str, Any]
for better IDE support and type checking.
"""

from typing import Any, TypedDict

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
    meta: dict[str, Any]


class ErrorResponse(TypedDict):
    """Standard error response structure."""

    success: bool
    message: str
    code: str
    details: dict[str, Any]
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
    profile_id: int | None
    tee_order: int | None


class PlayerProfileResponse(TypedDict, total=False):
    """Full player profile response."""

    id: int
    name: str
    email: str | None
    phone: str | None
    handicap: float
    ghin_number: str | None
    home_course: str | None
    created_at: str
    updated_at: str
    is_active: bool
    last_played: str | None


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
    holes: list[HoleInfo]
    total_yards: int
    slope_rating: float | None
    course_rating: float | None


class GameLobbyResponse(TypedDict):
    """Game lobby state response."""

    game_id: str
    join_code: str
    status: str
    course_name: str | None
    max_players: int
    players_joined: int
    players: list[PlayerInfo]
    tee_order_set: bool
    created_at: str


class HoleScores(TypedDict):
    """Scores for a single hole."""

    hole_number: int
    scores: dict[str, int]  # player_id -> gross score
    net_scores: dict[str, float]  # player_id -> net score
    winner: str | None
    wager: int
    points_changes: dict[str, int]


class GameStateResponse(TypedDict, total=False):
    """Current game state response."""

    game_id: str
    status: str
    current_hole: int
    players: list[PlayerInfo]
    rotation_order: list[str]
    current_wolf: str
    scores: dict[str, dict[int, int]]  # player_id -> hole -> score
    points: dict[str, int]  # player_id -> points
    hole_history: list[HoleScores]
    active: bool
    game_complete: bool


class HoleResultResponse(TypedDict):
    """Result of completing a hole."""

    success: bool
    message: str
    hole_number: int
    winners: list[str]
    points_changes: dict[str, int]
    current_standings: dict[str, int]
    next_wolf: str | None


class GameCompletionResponse(TypedDict):
    """Game completion summary."""

    game_id: str
    status: str
    final_standings: list[dict[str, Any]]
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
    active_presses: list[BetInfo]
    total_at_risk: int
    can_press: bool


class BettingOddsResponse(TypedDict):
    """Betting odds calculation response."""

    hole_number: int
    players: dict[str, float]  # player_id -> win probability
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
    scoring_distribution: dict[str, int]
    best_performance: dict[str, Any]
    trends: dict[str, Any]


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
    details: dict[str, Any]


# ============================================================================
# Type Aliases for Common Patterns
# ============================================================================

# Generic ID to value mapping
IdValueMap = dict[str, Any]

# Player ID to score mapping
PlayerScoreMap = dict[str, int]

# Hole number to score mapping
HoleScoreMap = dict[int, int]

# Full score matrix: player -> hole -> score
ScoreMatrix = dict[str, dict[int, int]]
