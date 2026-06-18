"""
WGP betting handlers — double, float, option, flush, concede, big dick, joe's special.

These are plain async functions (no APIRouter). The router in
``routers/wgp_actions.py`` dispatches to them.
"""

import logging
from typing import Any

from fastapi import HTTPException

from ..managers.rule_manager import RuleManager, RuleViolationError
from ..managers.scoring_manager import get_scoring_manager
from ..schemas import ActionResponse
from ..utils.time import utc_now
from ..validators import GameStateValidationError, GameStateValidator
from ..wolf_goat_pig import WolfGoatPigGame

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Handlers — betting actions
# ---------------------------------------------------------------------------


async def handle_offer_double(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle double offer"""
    try:
        player_id = payload.get("player_id")
        if not player_id:
            raise ValueError("Player ID required for double offer")

        # Check if partnerships have been formed (REQUIRED before any betting)
        game_state = game.get_game_state()
        rule_mgr = RuleManager.get_instance()

        # Validate partnerships formed before betting using RuleManager
        if not rule_mgr.are_partnerships_formed(game_state, game.current_hole):
            raise HTTPException(
                status_code=400,
                detail="Partnerships must be formed before betting can start",
            )

        # Validate player can double using RuleManager
        if not rule_mgr.can_double(player_id, game_state):
            raise HTTPException(status_code=400, detail="Cannot double at this time")

        # Get current game state
        game.get_game_state()

        # Offer double
        game.offer_double(player_id)

        player_name = game._get_player_name(player_id)

        # Add timeline event to hole progression if available
        if hasattr(game, "hole_progression") and game.hole_progression:  # type: ignore
            game.hole_progression.add_timeline_event(
                event_type="double_offer",
                description=f"{player_name} offered to double the wager",
                player_name=player_name,
                details={"double_offered": True, "player_id": player_id},
            )

        # Update game state
        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message="Double offered! Wager increases.",
            available_actions=[{"action_type": "ACCEPT_DOUBLE", "prompt": "Accept/Decline double"}],
            timeline_event={
                "id": f"double_offer_{utc_now().timestamp()}",
                "timestamp": utc_now().isoformat(),
                "type": "double_offer",
                "description": f"{player_name} offered to double the wager",
                "player_name": player_name,
                "details": {"double_offered": True, "player_id": player_id},
            },
        )
    except Exception as e:
        logger.error(f"Error offering double: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to offer double: {e!s}")


async def handle_accept_double(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle double acceptance/decline"""
    try:
        accepted = payload.get("accepted", False)

        # Get current game state
        game.get_game_state()

        # Identify the responding team from the payload
        responding_team = payload.get("responding_team", payload.get("team_id", "unknown"))

        # Respond to double
        if accepted:
            game.respond_to_double(responding_team, True)
            message = "Double accepted! Wager doubled."
        else:
            game.respond_to_double(responding_team, False)
            message = "Double declined. Original wager maintained."

        # Add timeline event to hole progression if available
        if hasattr(game, "hole_progression") and game.hole_progression:  # type: ignore
            game.hole_progression.add_timeline_event(
                event_type="double_response",
                description=f"Double {'accepted' if accepted else 'declined'}",
                player_name="Responding Team",
                details={"accepted": accepted},
            )

        # Update game state
        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message=message,
            available_actions=[{"action_type": "PLAY_SHOT", "prompt": "Continue with hole"}],
            timeline_event={
                "id": f"double_response_{utc_now().timestamp()}",
                "timestamp": utc_now().isoformat(),
                "type": "double_response",
                "description": f"Double {'accepted' if accepted else 'declined'}",
                "player_name": "Responding Team",
                "details": {"accepted": accepted},
            },
        )
    except Exception as e:
        logger.error(f"Error responding to double: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to respond to double: {e!s}")


async def handle_invoke_float(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle Float invocation by captain"""
    try:
        logger.info(f"handle_invoke_float payload: {payload}")

        if "captain_id" not in payload:
            raise ValueError("captain_id is required")

        captain_id = payload["captain_id"]

        # Get the game state instance
        game_state = game.game_state if hasattr(game, "game_state") else None

        if not game_state:
            raise HTTPException(status_code=400, detail="No active game")

        # Check if partnerships have been formed (REQUIRED before any betting)
        rule_mgr = RuleManager.get_instance()
        if not rule_mgr.are_partnerships_formed(game_state, game.current_hole):
            raise HTTPException(
                status_code=400,
                detail="Partnerships must be formed before betting can start",
            )

        # Validate captain can double (Float is a type of double)
        try:
            rule_mgr.validate_can_double(captain_id, game.get_game_state())
        except RuleViolationError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Invoke the float
        game.invoke_float(captain_id)
        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message="Float invoked! Wager doubled.",
            available_actions=[],
            timeline_event={
                "id": f"float_invoked_{captain_id}_{utc_now().timestamp()}",
                "timestamp": utc_now().isoformat(),
                "type": "float_invoked",
                "description": "Captain invoked Float - wager doubled!",
                "details": {
                    "captain_id": captain_id,
                    "new_wager": updated_state.get("hole_state", {}).get("betting", {}).get("current_wager", 0),
                },
            },
        )
    except Exception as e:
        logger.error(f"Error invoking float: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to invoke float: {e!s}")


async def handle_toggle_option(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle Option toggle by captain"""
    try:
        logger.info(f"handle_toggle_option payload: {payload}")

        if "captain_id" not in payload:
            raise ValueError("captain_id is required")

        captain_id = payload["captain_id"]

        # Get the game state instance
        game_state = game.game_state if hasattr(game, "game_state") else None  # type: ignore

        if not game_state:
            raise HTTPException(status_code=400, detail="No active game")

        # Check if partnerships have been formed (REQUIRED before any betting)
        rule_mgr = RuleManager.get_instance()
        if not rule_mgr.are_partnerships_formed(game_state, game.current_hole):
            raise HTTPException(
                status_code=400,
                detail="Partnerships must be formed before betting can start",
            )

        # Additional validation: Check if captain can invoke option (type of doubling)
        full_game_state = game.get_game_state()
        if not rule_mgr.can_double(captain_id, full_game_state):
            raise HTTPException(status_code=400, detail="Cannot toggle Option at this time")

        # Apply The Option using RuleManager (FULL IMPLEMENTATION)
        rule_mgr.apply_option(
            game_state=game_state,
            captain_id=captain_id,
            hole_number=game_state.current_hole,
        )

        # Get the new option state for logging (read AFTER apply_option toggled it)
        hole_state = game_state.hole_states[game_state.current_hole]
        option_active = getattr(hole_state.betting, "option_active", False)

        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message=f"The Option {'activated' if option_active else 'deactivated'}",
            available_actions=[],
            timeline_event={
                "id": f"option_toggled_{captain_id}_{utc_now().timestamp()}",
                "timestamp": utc_now().isoformat(),
                "type": "option_toggled",
                "description": f"Captain {'activated' if option_active else 'deactivated'} The Option",
                "details": {
                    "captain_id": captain_id,
                    "option_active": option_active,
                },
            },
        )
    except Exception as e:
        logger.error(f"Error toggling option: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to toggle option: {e!s}")


async def handle_flush(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """
    Handle Flush action - conceding/folding the hole.
    A player or team gives up on the current hole, awarding the hole to opponents.
    """
    try:
        logger.info(f"handle_flush payload: {payload}")

        # Validate required fields
        if "player_id" not in payload and "team_id" not in payload:
            raise ValueError("Either player_id or team_id is required for flush")

        # Get the game state instance
        game_state = game.game_state if hasattr(game, "game_state") else None  # type: ignore

        if not game_state:
            raise HTTPException(status_code=400, detail="No active game")

        # Check if partnerships have been formed (REQUIRED before any betting/conceding)
        rule_mgr = RuleManager.get_instance()
        if not rule_mgr.are_partnerships_formed(game_state, game.current_hole):
            raise HTTPException(
                status_code=400,
                detail="Partnerships must be formed before you can flush",
            )

        # Validate game is in correct phase for concession
        try:
            full_game_state = game.get_game_state()
            GameStateValidator.validate_game_phase(  # type: ignore
                full_game_state.get("phase", "unknown"), "playing", "concede hole"
            )
        except GameStateValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Get player/team info
        player_id = payload.get("player_id")
        team_id = payload.get("team_id")

        # Get current hole state
        hole_state = game_state.hole_states[game_state.current_hole]

        # Determine who is conceding
        if player_id is not None:
            conceding_player_name = game._get_player_name(player_id)
            concede_description = f"{conceding_player_name} has flushed (conceded) the hole"
        else:
            concede_description = f"Team {team_id} has flushed (conceded) the hole"

        # Award concession points using ScoringManager
        scoring_mgr = get_scoring_manager()
        scoring_mgr.award_concession_points(
            game_state=game_state,
            conceding_player=player_id,
            conceding_team=team_id,
            hole_number=game_state.current_hole,
        )

        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message=f"Flush! {concede_description}",
            available_actions=[{"action_type": "ADVANCE_HOLE", "prompt": "Continue to next hole"}],
            timeline_event={
                "id": f"flush_{utc_now().timestamp()}",
                "timestamp": utc_now().isoformat(),
                "type": "flush",
                "description": concede_description,
                "details": {
                    "player_id": player_id,
                    "team_id": team_id,
                    "current_wager": hole_state.betting.current_wager,
                },
            },
        )
    except Exception as e:
        logger.error(f"Error handling flush: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to handle flush: {e!s}")


async def handle_concede_putt(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle putt concession"""
    try:
        conceding_player = payload.get("conceding_player")
        conceded_player = payload.get("conceded_player")

        if not conceding_player or not conceded_player:
            raise HTTPException(
                status_code=400,
                detail="conceding_player and conceded_player are required",
            )

        # Get current game state
        current_state = game.get_game_state()

        # Update game state to reflect concession
        # This would typically update the hole state to mark the putt as conceded

        return ActionResponse(
            game_state=current_state,
            log_message=f"{conceding_player} concedes putt to {conceded_player}",
            available_actions=[{"action_type": "PLAY_SHOT", "prompt": "Continue with hole"}],
            timeline_event={
                "id": f"concession_{utc_now().timestamp()}",
                "timestamp": utc_now().isoformat(),
                "type": "concession",
                "description": f"Putt conceded to {conceded_player}",
                "player_name": conceding_player,
                "details": {"conceded_to": conceded_player},
            },
        )
    except Exception as e:
        logger.error(f"Error conceding putt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to concede putt: {e!s}")


async def handle_offer_big_dick(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle Big Dick challenge on hole 18"""
    try:
        player_id = payload.get("player_id", "default_player")

        result = game.offer_big_dick(player_id)
        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message=result["message"],
            available_actions=[
                {
                    "action_type": "ACCEPT_BIG_DICK",
                    "prompt": "Accept/Decline Big Dick challenge",
                }
            ],
            timeline_event={
                "id": f"big_dick_offer_{utc_now().timestamp()}",
                "timestamp": utc_now().isoformat(),
                "type": "big_dick_offer",
                "description": result["message"],
                "player_name": result["challenger_name"],
                "details": {"wager_amount": result["wager_amount"]},
            },
        )
    except Exception as e:
        logger.error(f"Error offering Big Dick: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to offer Big Dick: {e!s}")


async def handle_accept_big_dick(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle Big Dick challenge response"""
    try:
        accepting_players = payload.get("accepting_players", [])

        result = game.accept_big_dick(accepting_players)
        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message=result["message"],
            available_actions=[{"action_type": "PLAY_SHOT", "prompt": "Continue with hole"}],
            timeline_event={
                "id": f"big_dick_response_{utc_now().timestamp()}",
                "timestamp": utc_now().isoformat(),
                "type": "big_dick_response",
                "description": result["message"],
                "details": result,
            },
        )
    except Exception as e:
        logger.error(f"Error accepting Big Dick: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to accept Big Dick: {e!s}")


async def handle_joes_special(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle Joe's Special wager selection in Hoepfinger"""
    try:
        selected_value = payload.get("selected_value", 2)

        # Apply Joe's Special using RuleManager
        rule_mgr = RuleManager.get_instance()
        rule_mgr.apply_joes_special(
            game_state=game.get_game_state(),
            hole_number=game.current_hole,
            selected_value=selected_value,
        )

        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message=f"Joe's Special invoked! Hole starts at {selected_value} quarters.",
            available_actions=[{"action_type": "PLAY_SHOT", "prompt": "Continue with hole"}],
            timeline_event={
                "id": f"joes_special_{utc_now().timestamp()}",
                "timestamp": utc_now().isoformat(),
                "type": "joes_special",
                "description": f"Joe's Special: Hole value set to {selected_value} quarters",
                "details": {"selected_value": selected_value},
            },
        )
    except Exception as e:
        logger.error(f"Error invoking Joe's Special: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to invoke Joe's Special: {e!s}")
