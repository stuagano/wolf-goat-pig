from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Rule(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str


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


# Action API Models
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
