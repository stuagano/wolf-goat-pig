"""
WGP team/partnership handlers — request, respond, solo, aardvark actions.

These are plain async functions (no APIRouter). The router in
``routers/wgp_actions.py`` dispatches to them.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import HTTPException

from ..schemas import ActionResponse
from ..wolf_goat_pig import WolfGoatPigGame

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Handlers — team / partnership actions
# ---------------------------------------------------------------------------

async def handle_request_partnership(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle partnership request"""
    try:
        # Accept either partner_id or target_player_name
        partner_id = payload.get("partner_id")
        target_player = payload.get("target_player_name")

        if not partner_id and not target_player:
            raise HTTPException(
                status_code=400,
                detail="Either partner_id or target_player_name is required",
            )

        # Get current game state
        game.get_game_state()

        # Get the actual captain ID from the current hole state
        hole_state = game.hole_states[game.current_hole]
        captain_id = hole_state.teams.captain

        # If we have target_player name, convert to ID
        if target_player and not partner_id:
            for player in game.players:
                if player.name == target_player:
                    partner_id = player.id
                    break

            if not partner_id:
                raise HTTPException(status_code=400, detail=f"Player '{target_player}' not found")

        # If we have partner_id, get the name for response
        if partner_id and not target_player:
            for player in game.players:
                if player.id == partner_id:
                    target_player = player.name
                    break

            if not target_player:
                raise HTTPException(status_code=400, detail=f"Player with ID '{partner_id}' not found")

        # Request the partnership
        result = game.request_partner(captain_id, partner_id)  # type: ignore

        # Get updated game state
        updated_state = game.get_game_state()

        # Determine next available actions
        available_actions = []

        # If partnership was requested, the target player needs to respond
        if result.get("partnership_requested"):
            captain_name = game._get_player_name(captain_id)
            partner_name = target_player

            available_actions.append(
                {
                    "action_type": "RESPOND_PARTNERSHIP",
                    "prompt": f"Accept partnership with {captain_name}",
                    "payload": {"accepted": True},
                    "player_turn": partner_name,
                    "context": f"{captain_name} has requested you as a partner",
                }
            )

            available_actions.append(
                {
                    "action_type": "RESPOND_PARTNERSHIP",
                    "prompt": f"Decline partnership with {captain_name}",
                    "payload": {"accepted": False},
                    "player_turn": partner_name,
                    "context": f"{captain_name} has requested you as a partner",
                }
            )

        return ActionResponse(
            game_state=updated_state,
            log_message=result.get("message", f"Partnership requested with {target_player}"),
            available_actions=available_actions,
            timeline_event={
                "id": f"partnership_request_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "partnership_request",
                "description": f"Partnership requested with {target_player}",
                "player_name": game._get_player_name(captain_id),
                "details": {
                    "captain": game._get_player_name(captain_id),
                    "requested_partner": target_player,
                    "status": "pending_response",
                },
            },
        )
    except Exception as e:
        logger.error(f"Error requesting partnership: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to request partnership: {e!s}")


async def handle_respond_partnership(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle partnership response"""
    try:
        accepted = payload.get("accepted", False)

        # Get current game state
        game.get_game_state()

        # Get the partner ID from the pending request
        hole_state = game.hole_states[game.current_hole]
        partner_id = hole_state.teams.pending_request.get("requested") if hole_state.teams.pending_request else None

        if not partner_id:
            raise HTTPException(status_code=400, detail="No pending partnership request")

        # Respond to partnership
        if accepted:
            game.respond_to_partnership(partner_id, True)
            message = "Partnership accepted! Teams are formed."
        else:
            game.respond_to_partnership(partner_id, False)
            message = "Partnership declined. Captain goes solo."

        # Add timeline event to hole progression if available
        if hasattr(game, "hole_progression") and game.hole_progression:  # type: ignore
            game.hole_progression.add_timeline_event(
                event_type="partnership_response",
                description=f"Partnership {'accepted' if accepted else 'declined'}",
                player_name="Partner",
                details={"accepted": accepted},
            )

        # Update game state
        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message=message,
            available_actions=[{"action_type": "PLAY_SHOT", "prompt": "Continue with hole"}],
            timeline_event={
                "id": f"partnership_response_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "partnership_response",
                "description": f"Partnership {'accepted' if accepted else 'declined'}",
                "player_name": "Partner",
                "details": {"accepted": accepted},
            },
        )
    except Exception as e:
        logger.error(f"Error responding to partnership: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to respond to partnership: {e!s}")


async def handle_declare_solo(game: WolfGoatPigGame) -> ActionResponse:
    """Handle captain going solo"""
    try:
        # Get current game state
        game.get_game_state()

        # Get the actual captain ID from the current hole state
        hole_state = game.hole_states.get(game.current_hole)
        if not hole_state or not hole_state.teams.captain:
            raise HTTPException(status_code=400, detail="No captain found for current hole")

        captain_id = hole_state.teams.captain

        # Captain goes solo
        game.captain_go_solo(captain_id)

        # Add timeline event to hole progression if available
        if hasattr(game, "hole_progression") and game.hole_progression:  # type: ignore
            game.hole_progression.add_timeline_event(
                event_type="partnership_decision",
                description="Captain goes solo - 1 vs 3",
                player_name="Captain",
                details={"solo": True},
            )

        # Update game state
        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message="Captain declares solo! It's 1 vs 3.",
            available_actions=[{"action_type": "PLAY_SHOT", "prompt": "Continue with hole"}],
            timeline_event={
                "id": f"solo_declaration_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "partnership_decision",
                "description": "Captain goes solo - 1 vs 3",
                "player_name": "Captain",
                "details": {"solo": True},
            },
        )
    except Exception as e:
        logger.error(f"Error declaring solo: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to declare solo: {e!s}")


async def handle_aardvark_join_request(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle Aardvark requesting to join a team"""
    try:
        aardvark_id = payload.get("aardvark_id")
        target_team = payload.get("target_team", "team1")

        if not aardvark_id:
            raise HTTPException(status_code=400, detail="aardvark_id is required")

        result = game.aardvark_request_team(aardvark_id, target_team)
        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message=result["message"],
            available_actions=[
                {
                    "action_type": "AARDVARK_TOSS",
                    "prompt": f"Accept or toss {result['aardvark_name']}",
                }
            ],
            timeline_event={
                "id": f"aardvark_request_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "aardvark_request",
                "description": result["message"],
                "details": {"aardvark_id": aardvark_id, "target_team": target_team},
            },
        )
    except Exception as e:
        logger.error(f"Error handling Aardvark join request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to handle Aardvark join request: {e!s}")


async def handle_aardvark_toss(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle team response to Aardvark request (accept or toss)"""
    try:
        team_id = payload.get("team_id", "team1")
        accept = payload.get("accept", False)

        result = game.respond_to_aardvark(team_id, accept)
        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message=result["message"],
            available_actions=[{"action_type": "PLAY_SHOT", "prompt": "Continue with hole"}],
            timeline_event={
                "id": f"aardvark_toss_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "aardvark_toss",
                "description": result["message"],
                "details": {
                    "team_id": team_id,
                    "accepted": accept,
                    "status": result["status"],
                },
            },
        )
    except Exception as e:
        logger.error(f"Error handling Aardvark toss: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to handle Aardvark toss: {e!s}")


async def handle_aardvark_go_solo(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle Aardvark deciding to go solo"""
    try:
        aardvark_id = payload.get("aardvark_id")
        use_tunkarri = payload.get("use_tunkarri", False)

        if not aardvark_id:
            raise HTTPException(status_code=400, detail="aardvark_id is required")

        result = game.aardvark_go_solo(aardvark_id, use_tunkarri)
        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message=result["message"],
            available_actions=[{"action_type": "PLAY_SHOT", "prompt": "Continue with hole"}],
            timeline_event={
                "id": f"aardvark_solo_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "aardvark_solo",
                "description": result["message"],
                "details": {
                    "aardvark_id": aardvark_id,
                    "use_tunkarri": use_tunkarri,
                    "status": result["status"],
                },
            },
        )
    except Exception as e:
        logger.error(f"Error handling Aardvark go solo: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to handle Aardvark go solo: {e!s}")


async def handle_ping_pong_aardvark(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle Ping Pong Aardvark"""
    try:
        team_id = payload.get("team_id", "team1")
        aardvark_id = payload.get("aardvark_id", "default_aardvark")

        result = game.ping_pong_aardvark(team_id, aardvark_id)
        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message=result["message"],
            available_actions=[{"action_type": "PLAY_SHOT", "prompt": "Continue with hole"}],
            timeline_event={
                "id": f"ping_pong_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "ping_pong_aardvark",
                "description": result["message"],
                "details": {
                    "new_wager": result["new_wager"],
                    "ping_pong_count": result.get("ping_pong_count", 0),
                },
            },
        )
    except Exception as e:
        logger.error(f"Error ping ponging Aardvark: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ping pong Aardvark: {e!s}")
