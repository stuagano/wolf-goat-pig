"""Games router — aggregates the /games route modules.

The /games routes live in games_setup, games_scorecard, games_lifecycle and
games_queries; this module includes them (in that order) into one router so
``app.include_router(games.router)`` registers the same surface as before.
Names are re-exported so existing ``from app.routers.games import X`` keeps working.
"""

from fastapi import APIRouter

from . import games_lifecycle, games_queries, games_scorecard, games_setup
from .games_lifecycle import (
    _check_game_achievements,
    _check_saved_game_achievements,
    delete_game,
    mark_game_complete,
    start_game_from_lobby,
)
from .games_queries import get_game_state_by_id, get_games, get_round_summary
from .games_scorecard import (
    ScorecardBackfillRequest,
    ScorecardRoundHoleQuarter,
    ScorecardRoundPlayer,
    ScorecardRoundRequest,
    backfill_scorecard,
    create_round_from_scorecard,
    get_scorecard_photo,
)
from .games_setup import (
    SetTeeOrderRequest,
    create_game_with_join_code,
    get_game_lobby,
    join_game_with_code,
    set_tee_order,
)

router = APIRouter()
router.include_router(games_setup.router)
router.include_router(games_scorecard.router)
router.include_router(games_lifecycle.router)
router.include_router(games_queries.router)

__all__ = [
    "LEGACY_TO_UNIFIED_ACTIONS",
    "UNIFIED_ACTION_TYPES",
    "ScorecardBackfillRequest",
    "ScorecardRoundHoleQuarter",
    "ScorecardRoundPlayer",
    "ScorecardRoundRequest",
    "SetTeeOrderRequest",
    "_check_game_achievements",
    "_check_saved_game_achievements",
    "_get_current_captain_id",
    "backfill_scorecard",
    "create_game_with_join_code",
    "create_round_from_scorecard",
    "delete_game",
    "get_game_lobby",
    "get_game_state_by_id",
    "get_games",
    "get_round_summary",
    "get_scorecard_photo",
    "join_game_with_code",
    "mark_game_complete",
    "router",
    "set_tee_order",
    "start_game_from_lobby",
]


# ---------------------------------------------------------------------------
# Legacy-to-unified action mapping (used by POST /games/{game_id}/action)
# ---------------------------------------------------------------------------


def _get_current_captain_id() -> str | None:
    """Best-effort lookup for the active captain id across legacy and unified state."""
    try:
        simulation_state = game.get_game_state()  # type: ignore
        if isinstance(simulation_state, dict):
            captain = simulation_state.get("captain_id") or simulation_state.get("captain")
            if captain:
                return captain  # type: ignore
    except Exception:
        # If the simulation hasn't been initialized yet, fall back to legacy state
        pass

    try:
        legacy_state = {"message": "Legacy game_state.get_state() is deprecated"}
        if isinstance(legacy_state, dict):
            return legacy_state.get("captain_id")
    except Exception:
        pass

    return None


LEGACY_TO_UNIFIED_ACTIONS = {
    "next_hole": ("ADVANCE_HOLE", lambda payload: {}),
    "request_partner": ("REQUEST_PARTNERSHIP", lambda payload: payload or {}),
    "accept_partner": ("RESPOND_PARTNERSHIP", lambda payload: {"accepted": True}),
    "decline_partner": ("RESPOND_PARTNERSHIP", lambda payload: {"accepted": False}),
    "go_solo": ("DECLARE_SOLO", lambda payload: {}),
    "offer_double": (
        "OFFER_DOUBLE",
        lambda payload: {
            "player_id": payload.get("player_id")
            or payload.get("captain_id")
            or payload.get("offering_player_id")
            or payload.get("offering_team_id")
            or _get_current_captain_id(),
        },
    ),
    "accept_double": ("ACCEPT_DOUBLE", lambda payload: {"accepted": True}),
    "decline_double": ("ACCEPT_DOUBLE", lambda payload: {"accepted": False}),
    "concede_putt": ("CONCEDE_PUTT", lambda payload: payload or {}),
    "INITIALIZE_GAME": ("INITIALIZE_GAME", lambda payload: payload or {}),
}

UNIFIED_ACTION_TYPES = {
    "INITIALIZE_GAME",
    "PLAY_SHOT",
    "REQUEST_PARTNERSHIP",
    "RESPOND_PARTNERSHIP",
    "DECLARE_SOLO",
    "OFFER_DOUBLE",
    "ACCEPT_DOUBLE",
    "CONCEDE_PUTT",
    "ADVANCE_HOLE",
    "OFFER_BIG_DICK",
    "ACCEPT_BIG_DICK",
    "AARDVARK_JOIN_REQUEST",
    "AARDVARK_TOSS",
    "AARDVARK_GO_SOLO",
    "PING_PONG_AARDVARK",
    "INVOKE_JOES_SPECIAL",
    "GET_POST_HOLE_ANALYSIS",
    "ENTER_HOLE_SCORES",
    "GET_ADVANCED_ANALYTICS",
}
