"""
WGP Action Engine Router — unified action dispatcher for Wolf Goat Pig games.

Routes ``POST /wgp/{game_id}/action`` to the appropriate domain handler.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import database

# Domain handler imports — betting actions
from ..domain.wgp_handlers_betting import (
    handle_accept_big_dick,
    handle_accept_double,
    handle_concede_putt,
    handle_flush,
    handle_invoke_float,
    handle_joes_special,
    handle_offer_big_dick,
    handle_offer_double,
    handle_toggle_option,
)

# Domain handler imports — core game flow
from ..domain.wgp_handlers_core import (
    handle_advance_hole,
    handle_calculate_hole_points,
    handle_complete_game,
    handle_enter_hole_scores,
    handle_get_advanced_analytics,
    handle_get_post_hole_analysis,
    handle_initialize_game,
    handle_play_shot,
    handle_record_net_score,
)

# Domain handler imports — team/partnership actions
from ..domain.wgp_handlers_teams import (
    handle_aardvark_go_solo,
    handle_aardvark_join_request,
    handle_aardvark_toss,
    handle_declare_solo,
    handle_ping_pong_aardvark,
    handle_request_partnership,
    handle_respond_partnership,
)
from ..schemas import ActionRequest, ActionResponse
from ..services.game_lifecycle_service import get_game_lifecycle_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wgp", tags=["wgp-actions"])


# ---------------------------------------------------------------------------
# Legacy-to-unified action mappings (kept next to the dispatcher)
# ---------------------------------------------------------------------------


def _get_current_captain_id_for_mapping() -> str | None:
    """Thin wrapper used only by LEGACY_TO_UNIFIED_ACTIONS lambdas."""
    from ..domain.wgp_handlers_core import _get_current_captain_id

    return _get_current_captain_id()


LEGACY_TO_UNIFIED_ACTIONS: dict[str, tuple[str, Any]] = {
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
            or _get_current_captain_id_for_mapping(),
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


# ---------------------------------------------------------------------------
# Unified Action API — main game logic endpoint
# ---------------------------------------------------------------------------


@router.post("/{game_id}/action", response_model=ActionResponse)
async def unified_action(game_id: str, action: ActionRequest, db: Session = Depends(database.get_db)) -> ActionResponse:
    """Unified action endpoint for all Wolf Goat Pig game interactions"""
    try:
        # Get the specific game instance for this game_id
        # MIGRATED: Using GameLifecycleService instead of get_or_load_game
        game = get_game_lifecycle_service().get_game(db, game_id)

        # Normalize action_type to uppercase for consistent matching
        action_type = action.action_type.upper()
        payload = action.payload or {}

        # Route to appropriate handler based on action type
        # All handlers now receive the game instance instead of using global wgp_simulation
        if action_type == "INITIALIZE_GAME":
            return await handle_initialize_game(game, payload)
        if action_type == "PLAY_SHOT":
            return await handle_play_shot(game, payload)
        if action_type == "REQUEST_PARTNERSHIP" or action_type == "REQUEST_PARTNER":
            return await handle_request_partnership(game, payload)
        if action_type == "RESPOND_PARTNERSHIP" or action_type == "ACCEPT_PARTNER" or action_type == "DECLINE_PARTNER":
            return await handle_respond_partnership(game, payload)
        if action_type == "DECLARE_SOLO" or action_type == "GO_SOLO":
            return await handle_declare_solo(game)
        if action_type == "OFFER_DOUBLE":
            return await handle_offer_double(game, payload)
        if action_type == "ACCEPT_DOUBLE":
            return await handle_accept_double(game, payload)
        if action_type == "INVOKE_FLOAT":
            # Frontend sends captain_id as direct field
            action_dict = action.model_dump() if hasattr(action, "model_dump") else action.dict()
            return await handle_invoke_float(game, action_dict)
        if action_type == "TOGGLE_OPTION":
            # Frontend sends captain_id as direct field
            action_dict = action.model_dump() if hasattr(action, "model_dump") else action.dict()
            return await handle_toggle_option(game, action_dict)
        if action_type == "FLUSH":
            # Flush = concede/fold the hole
            action_dict = action.model_dump() if hasattr(action, "model_dump") else action.dict()
            return await handle_flush(game, action_dict)
        if action_type == "CONCEDE_PUTT":
            return await handle_concede_putt(game, payload)
        if action_type == "ADVANCE_HOLE" or action_type == "NEXT_HOLE":
            return await handle_advance_hole(game)
        if action_type == "OFFER_BIG_DICK":
            return await handle_offer_big_dick(game, payload)
        if action_type == "ACCEPT_BIG_DICK":
            return await handle_accept_big_dick(game, payload)
        if action_type == "AARDVARK_JOIN_REQUEST":
            return await handle_aardvark_join_request(game, payload)
        if action_type == "AARDVARK_TOSS":
            return await handle_aardvark_toss(game, payload)
        if action_type == "AARDVARK_GO_SOLO":
            return await handle_aardvark_go_solo(game, payload)
        if action_type == "PING_PONG_AARDVARK":
            return await handle_ping_pong_aardvark(game, payload)
        if action_type == "INVOKE_JOES_SPECIAL":
            return await handle_joes_special(game, payload)
        if action_type == "GET_POST_HOLE_ANALYSIS":
            return await handle_get_post_hole_analysis(game, payload)
        if action_type == "ENTER_HOLE_SCORES":
            return await handle_enter_hole_scores(game, payload)
        if action_type == "GET_ADVANCED_ANALYTICS":
            return await handle_get_advanced_analytics(game, payload)
        if action_type == "COMPLETE_GAME":
            return await handle_complete_game(game, payload)
        if action_type == "RECORD_NET_SCORE":
            # Handle score recording action from frontend
            # Frontend sends player_id and score as direct fields, not in payload
            action_dict = action.model_dump() if hasattr(action, "model_dump") else action.dict()
            return await handle_record_net_score(game, action_dict)
        if action_type == "CALCULATE_HOLE_POINTS":
            # Handle calculate points action from frontend
            action_dict = action.model_dump() if hasattr(action, "model_dump") else action.dict()
            return await handle_calculate_hole_points(game, action_dict)  # type: ignore
        raise HTTPException(status_code=400, detail=f"Unknown action type: {action_type}")

    except HTTPException:
        # Re-raise HTTPExceptions to preserve their status codes
        raise
