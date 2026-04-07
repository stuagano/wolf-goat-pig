"""
Core WGP game-flow handlers — initialize, play shot, advance hole, scoring, analytics.

These are plain async functions (no APIRouter). The router in
``routers/wgp_actions.py`` dispatches to them.
"""

import logging
import traceback
from datetime import datetime
from typing import Any

from fastapi import HTTPException

from ..managers.rule_manager import RuleManager
from ..schemas import ActionResponse
from ..state.course_manager import CourseManager
from ..validators import GameStateValidator, HandicapValidator
from ..wolf_goat_pig import Player, WolfGoatPigGame

# Module-level CourseManager for game initialization
course_manager = CourseManager()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level global (mirrors the old main.py global)
# ---------------------------------------------------------------------------
game: WolfGoatPigGame | None = None


# ---------------------------------------------------------------------------
# Private helpers
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


def _serialize_game_state():
    """Convert game state to serializable format"""
    try:
        # Get the current game state from the WGP simulation
        state = game.get_game_state()  # type: ignore
        return state
    except Exception as e:
        logger.error(f"Error serializing game state: {e}")
        return {}


# ---------------------------------------------------------------------------
# Handlers — core game flow
# ---------------------------------------------------------------------------

async def handle_initialize_game(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle game initialization with robust error handling and fallbacks"""
    try:
        players = payload.get("players", [])
        course_name = payload.get("course_name", "Wing Point Golf & Country Club")

        # Validate player count using GameStateValidator
        GameStateValidator.validate_player_count(len(players))

        # Ensure all players have required fields with smart defaults
        for i, player in enumerate(players):
            if "name" not in player:
                player["name"] = f"Player {i + 1}"
                logger.warning(f"Player {i + 1} missing name, using default")

            # Validate and normalize handicap using HandicapValidator
            player["handicap"] = HandicapValidator.validate_and_normalize_handicap(
                player.get("handicap"), player_name=player.get("name")
            )

            # Add missing fields if not present
            if "id" not in player:
                player["id"] = f"p{i + 1}"
            if "strength" not in player:
                # Calculate strength from handicap using HandicapValidator
                player["strength"] = HandicapValidator.calculate_strength_from_handicap(player["handicap"])

        # Verify course exists, use fallback if needed
        try:
            available_courses = course_manager.get_courses()
            if course_name not in available_courses:
                logger.warning(f"Requested course '{course_name}' not available, using fallback")
                # Use first available course or fallback
                if available_courses:
                    course_name = list(available_courses.keys())[0]
                    logger.info(f"Using available course: {course_name}")
                else:
                    logger.error("No courses available, using emergency fallback")
                    course_name = "Emergency Course"
        except Exception as course_error:
            logger.error(f"Course verification failed: {course_error}")
            course_name = "Emergency Course"

        # Initialize WGP simulation with robust error handling
        try:
            # Create Player objects
            wgp_players = []
            for player in players:
                try:
                    wgp_players.append(
                        Player(
                            id=player["id"],
                            name=player["name"],
                            handicap=player["handicap"],
                        )
                    )
                except Exception as player_creation_error:
                    logger.error(f"Failed to create Player for {player['name']}: {player_creation_error}")
                    # Create with minimal data
                    wgp_players.append(
                        Player(
                            id=player.get("id", f"p{len(wgp_players) + 1}"),
                            name=player.get("name", f"Player {len(wgp_players) + 1}"),
                            handicap=18.0,
                        )
                    )

            if len(wgp_players) != len(players):
                logger.warning(f"Only created {len(wgp_players)} WGP players from {len(players)} input players")

            # Initialize the simulation with these players and course manager
            try:
                game.__init__(
                    player_count=len(wgp_players),
                    players=wgp_players,
                    course_manager=course_manager,
                )  # type: ignore
                logger.info("WGP simulation initialized successfully with course data")
            except Exception as sim_init_error:
                logger.error(f"WGP simulation initialization failed: {sim_init_error}")
                # Try without course manager
                try:
                    game.__init__(player_count=len(wgp_players), players=wgp_players)  # type: ignore
                    logger.warning("Initialized without course manager")
                except Exception as fallback_error:
                    # Try with basic initialization
                    logger.warning(f"Fallback init also had issues: {fallback_error}")
                    game.__init__(player_count=len(wgp_players))  # type: ignore
                    logger.warning("Fell back to basic simulation initialization")

            # Set computer players (all except first) with error handling
            try:
                computer_player_ids = [p["id"] for p in players[1:]]
                game.set_computer_players(computer_player_ids)
                logger.info(f"Set {len(computer_player_ids)} computer players")
            except Exception as computer_setup_error:
                logger.error(f"Failed to set computer players: {computer_setup_error}")
                # Continue without computer player setup

            # Initialize the first hole with error handling
            try:
                game._initialize_hole(1)
                logger.info("First hole initialized")
            except Exception as hole_init_error:
                logger.error(f"Failed to initialize first hole: {hole_init_error}")
                # Continue - hole might be initialized differently

            # Enable shot progression and timeline tracking
            try:
                game.enable_shot_progression()
                logger.info("Shot progression enabled")
            except Exception as progression_error:
                logger.warning(f"Failed to enable shot progression: {progression_error}")
                # Non-critical, continue

            # Add initial timeline event
            try:
                if hasattr(wgp_simulation, "hole_progression") and game.hole_progression:  # type: ignore
                    game.hole_progression.add_timeline_event(
                        event_type="game_start",
                        description=f"Game started with {len(players)} players on {course_name}",
                        details={"players": players, "course": course_name},
                    )
                    logger.info("Initial timeline event added")
            except Exception as timeline_error:
                logger.warning(f"Failed to add timeline event: {timeline_error}")
                # Non-critical, continue

        except Exception as simulation_error:
            logger.error(f"Critical simulation setup error: {simulation_error}")
            # Create minimal fallback simulation
            try:
                game.__init__(player_count=len(players))  # type: ignore
                logger.warning("Created minimal fallback simulation")
            except Exception as fallback_error:
                logger.error(f"Even fallback simulation failed: {fallback_error}")
                # This is critical - raise error
                raise HTTPException(status_code=500, detail="Failed to initialize simulation engine")

        # Get initial game state (with error handling)
        try:
            current_state = game.get_game_state()
            if not current_state:
                logger.warning("Empty game state returned, creating minimal state")
                current_state = {
                    "active": True,
                    "current_hole": 1,
                    "players": players,
                    "course": course_name,
                }
        except Exception as state_error:
            logger.error(f"Failed to get game state: {state_error}")
            # Create minimal state
            current_state = {
                "active": True,
                "current_hole": 1,
                "players": players,
                "course": course_name,
                "error": "Partial initialization - some features may be limited",
            }

        success_message = f"Game initialized with {len(players)} players on {course_name}"
        if any("error" in str(current_state).lower() for _ in [1]):  # Check if there were issues
            success_message += " (some advanced features may be limited)"

        return ActionResponse(
            game_state=current_state,
            log_message=success_message,
            available_actions=[
                {
                    "action_type": "PLAY_SHOT",
                    "prompt": "Start first hole",
                    "player_turn": players[0]["name"],
                }
            ],
            timeline_event={
                "id": "init_1",
                "timestamp": datetime.now().isoformat(),
                "type": "game_start",
                "description": f"Game started with {len(players)} players",
                "details": {"players": players, "course": course_name},
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Critical error initializing game: {e}")
        logger.error(traceback.format_exc())

        # Create minimal emergency response
        emergency_state = {
            "active": False,
            "error": "Game initialization failed",
            "fallback": True,
            "message": "Please try again or contact support",
        }

        return ActionResponse(
            game_state=emergency_state,
            log_message=f"Game initialization failed: {e!s}",
            available_actions=[{"action_type": "RETRY_INITIALIZATION", "prompt": "Try Again"}],
            timeline_event={
                "id": "init_error",
                "timestamp": datetime.now().isoformat(),
                "type": "initialization_error",
                "description": "Game initialization failed",
                "details": {"error": str(e)},
            },
        )


async def handle_play_shot(game: WolfGoatPigGame, payload: dict[str, Any] = None) -> ActionResponse:  # type: ignore
    """Handle playing a shot"""
    try:
        # Get current game state
        current_state = game.get_game_state()

        # Determine next player to hit
        next_player = game._get_next_shot_player()
        if not next_player:
            return ActionResponse(
                game_state=current_state,
                log_message="No players available to hit",
                available_actions=[],
                timeline_event={
                    "id": f"shot_{datetime.now().timestamp()}",
                    "timestamp": datetime.now().isoformat(),
                    "type": "shot",
                    "description": "No players available to hit",
                    "player_name": None,
                },
            )

        # Simulate the shot
        shot_response = game.simulate_shot(next_player)  # type: ignore
        shot_result = shot_response.get("shot_result", {})

        # Update game state
        updated_state = game.get_game_state()
        hole_state = game.hole_states[game.current_hole]

        # Check if this was a tee shot and update invitation windows
        is_tee_shot = (
            next_player not in hole_state.ball_positions or hole_state.ball_positions[next_player].shot_count == 1
        )
        if is_tee_shot:
            # Create a WGPShotResult object from the shot_result dictionary
            from archived.game_engine.wolf_goat_pig_simulation import WGPShotResult

            shot_obj = WGPShotResult(
                player_id=shot_result.get("player_id", next_player),
                shot_number=shot_result.get("shot_number", 1),
                lie_type=shot_result.get("lie_type", "fairway"),
                distance_to_pin=shot_result.get("distance_to_pin", 0.0),
                shot_quality=shot_result.get("shot_quality", "average"),
                made_shot=shot_result.get("made_shot", False),
                penalty_strokes=shot_result.get("penalty_strokes", 0),
            )
            hole_state.process_tee_shot(next_player, shot_obj)  # type: ignore

        # Determine next available actions based on shot progression and partnership timing
        available_actions = []

        if shot_response.get("hole_complete"):
            # Hole is complete - offer scoring options
            available_actions.append({"action_type": "ENTER_HOLE_SCORES", "prompt": "Enter hole scores"})
        elif hole_state.teams.type == "pending":
            # Teams not formed yet - check if we should offer partnership decisions
            captain_id = hole_state.teams.captain
            captain_name = game._get_player_name(captain_id)

            # Get available partners using RuleManager
            rule_mgr = RuleManager.get_instance()
            available_partners = rule_mgr.get_available_partners(
                game_state=game.get_game_state(),
                captain_id=captain_id,  # type: ignore
                hole_number=game.current_hole,
            )

            # Check if we have enough tee shots for partnership decisions
            tee_shots_completed = sum(
                1
                for player_id, ball in hole_state.ball_positions.items()  # type: ignore
                if ball and ball.shot_count >= 1
            )

            if tee_shots_completed >= 2:
                if available_partners:
                    # Add partnership actions for captain with context about their shots
                    for partner in available_partners:
                        tee_context = f"{partner['name']} hit to {partner['tee_shot_distance']:.0f} yards"
                        available_actions.append(
                            {
                                "action_type": "REQUEST_PARTNERSHIP",
                                "prompt": f"Partner with {partner['name']}?",
                                "payload": {"target_player_name": partner["name"]},  # type: ignore
                                "player_turn": captain_name,
                                "context": f"🏌️ {tee_context}. Form partnership with {partner['name']} (handicap {partner['handicap']})?",
                            }
                        )

                    # Add solo option with context
                available_actions.append(
                    {
                        "action_type": "DECLARE_SOLO",
                        "prompt": "Go solo (1v3)",
                        "player_turn": captain_name,
                        "context": "Play alone against all three opponents. High risk, high reward!",
                    }
                )
            else:
                # Need more tee shots or partnership deadline passed
                if tee_shots_completed < 2:
                    remaining_players = [
                        p.name
                        for p in game.players
                        if p.id not in hole_state.ball_positions or not hole_state.ball_positions[p.id]
                    ]
                    available_actions.append(
                        {
                            "action_type": "TAKE_SHOT",
                            "prompt": "Continue tee shots",
                            "context": f"Need more tee shots for partnership decisions. Waiting on: {', '.join(remaining_players) if remaining_players else 'all set'}",
                        }
                    )
                else:
                    # Partnership deadline has passed - captain must go solo
                    available_actions.append(
                        {
                            "action_type": "DECLARE_SOLO",
                            "prompt": "Go solo (deadline passed)",
                            "player_turn": captain_name,
                            "context": "Partnership deadline has passed. Must play solo.",
                        }
                    )
        else:
            # Continue with shot progression
            next_shot_player = game._get_next_shot_player()
            if next_shot_player:
                next_shot_player_name = game._get_player_name(next_shot_player)

                # Determine shot type for better UX
                current_ball = hole_state.get_player_ball_position(next_shot_player)
                shot_type = "tee shot" if not current_ball else f"shot #{current_ball.shot_count + 1}"

                available_actions.append(
                    {
                        "action_type": "PLAY_SHOT",
                        "prompt": f"{next_shot_player_name} hits {shot_type}",
                        "player_turn": next_shot_player_name,
                        "context": f"Continue hole progression with {next_shot_player_name}'s {shot_type}",
                    }
                )
            elif not hole_state.hole_complete:
                # All players have played but hole not complete - might need scoring
                available_actions.append(
                    {
                        "action_type": "ENTER_HOLE_SCORES",
                        "prompt": "Enter final scores for hole",
                    }
                )

            # Check for betting opportunities using RuleManager
            rule_mgr = RuleManager.get_instance()
            betting_check = rule_mgr.check_betting_opportunities(
                game_state=game.get_game_state(),
                hole_number=game.current_hole,
                last_shot=shot_response.get("shot_result") if shot_response else None,
            )

            if betting_check["should_offer"]:
                # Add betting action to available_actions
                available_actions.append(betting_check["action"])

        # Create timeline event from shot response
        player_name = game._get_player_name(next_player)
        shot_description = f"{player_name} hits a {shot_result.get('shot_quality', 'average')} shot"
        if shot_result.get("made_shot"):
            shot_description += " and holes out!"
        else:
            shot_description += f" - {shot_result.get('distance_to_pin', 0):.0f} yards to pin"

        timeline_event = {
            "id": f"shot_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat(),
            "type": "shot",
            "description": shot_description,
            "player_name": player_name,
            "details": shot_result,
        }

        return ActionResponse(
            game_state=updated_state,
            log_message=shot_description,
            available_actions=available_actions,
            timeline_event=timeline_event,
        )
    except Exception as e:
        logger.error(f"Error playing shot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to play shot: {e!s}")


async def handle_advance_hole(game: WolfGoatPigGame) -> ActionResponse:
    """Handle advancing to the next hole"""
    try:
        # Advance to next hole
        game.advance_to_next_hole()

        # Get updated game state
        current_state = game.get_game_state()

        # Add timeline event for hole advancement
        if hasattr(wgp_simulation, "hole_progression") and game.hole_progression:  # type: ignore
            game.hole_progression.add_timeline_event(
                event_type="hole_start",
                description=f"Started hole {game.current_hole}",
                details={"hole_number": game.current_hole},
            )

        # Enable shot progression for the new hole
        game.enable_shot_progression()

        # Get the next player to hit
        next_player = game._get_next_shot_player()
        next_player_name = game._get_player_name(next_player) if next_player else "Unknown"

        return ActionResponse(
            game_state=current_state,
            log_message=f"Advanced to hole {game.current_hole}",
            available_actions=[
                {
                    "action_type": "PLAY_SHOT",
                    "prompt": f"Start hole {game.current_hole}",
                    "player_turn": next_player_name,
                }
            ],
            timeline_event={
                "id": f"hole_start_{game.current_hole}",
                "timestamp": datetime.now().isoformat(),
                "type": "hole_start",
                "description": f"Started hole {game.current_hole}",
                "details": {"hole_number": game.current_hole},
            },
        )
    except Exception as e:
        logger.error(f"Error advancing hole: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to advance hole: {e!s}")


async def handle_enter_hole_scores(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle entering hole scores"""
    try:
        scores = payload.get("scores", {})

        result = game.enter_hole_scores(scores)
        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message=result.get("message", "Hole scores entered and points calculated"),
            available_actions=[
                {
                    "action_type": "GET_POST_HOLE_ANALYSIS",
                    "prompt": "View Hole Analysis",
                },
                {"action_type": "ADVANCE_HOLE", "prompt": "Continue to Next Hole"},
            ],
            timeline_event={
                "id": f"scores_entered_{game.current_hole}_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "scores_entered",
                "description": f"Scores entered for hole {game.current_hole}",
                "details": {"scores": scores, "points_result": result},
            },
        )
    except Exception as e:
        logger.error(f"Error entering hole scores: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enter hole scores: {e!s}")


async def handle_complete_game(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle completing a game and saving results permanently"""
    try:
        # Get the game state instance
        game_state = game.game_state if hasattr(wgp_simulation, "game_state") else None  # type: ignore

        if not game_state:
            raise HTTPException(status_code=400, detail="No active game to complete")

        # Complete the game and save results
        result_message = game_state.complete_game()

        updated_state = game.get_game_state()
        updated_state["game_completed"] = True
        updated_state["completion_message"] = result_message

        # TODO: Send game_end notifications using NotificationService
        # Once DB session is passed to handlers, add:
        # notification_service = get_notification_service()
        # for player in game_state.player_manager.players:
        #     notification_service.send_notification(
        #         player_id=player.db_id,
        #         notification_type="game_end",
        #         message=f"Game completed! {result_message}",
        #         db=db
        #     )

        return ActionResponse(
            game_state=updated_state,
            log_message=f"🎉 Game completed! {result_message}",
            available_actions=[],  # No more actions available
            timeline_event={
                "id": f"game_completed_{game.game_state.game_id}_{datetime.now().timestamp()}",  # type: ignore
                "timestamp": datetime.now().isoformat(),
                "type": "game_completed",
                "description": "Game completed and results saved",
                "details": {
                    "game_id": game.game_state.game_id,  # type: ignore
                    "holes_played": len(game.game_state.hole_history),  # type: ignore
                    "final_scores": {p.id: p.points for p in game.game_state.player_manager.players},  # type: ignore
                },
            },
        )
    except Exception as e:
        logger.error(f"Error completing game: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to complete game: {e!s}")


async def handle_record_net_score(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle recording a net score for a player"""
    try:
        # Debug: Log the payload
        logger.info(f"handle_record_net_score payload: {payload}")

        # Use 'in' to check if keys exist, since player_id can be 0
        if "player_id" not in payload or "score" not in payload:
            logger.error(f"Missing keys in payload. Keys present: {list(payload.keys())}")
            raise ValueError("player_id and score are required")

        player_id = payload["player_id"]
        score = payload["score"]

        # Get the game state instance
        game_state = game.game_state if hasattr(wgp_simulation, "game_state") else None  # type: ignore

        if not game_state:
            raise HTTPException(status_code=400, detail="No active game")

        # Record the net score
        result = game_state.record_net_score(player_id, score)
        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message=result,
            available_actions=[],  # No specific actions after recording score
            timeline_event={
                "id": f"score_recorded_{player_id}_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "score_recorded",
                "description": f"Score {score} recorded for player {player_id}",
                "details": {"player_id": player_id, "score": score},
            },
        )
    except Exception as e:
        logger.error(f"Error recording net score: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record net score: {e!s}")


async def handle_calculate_hole_points(payload: dict[str, Any]) -> ActionResponse:
    """Handle calculating points for the current hole"""
    try:
        # Get the game state instance
        game_state = game.game_state if hasattr(wgp_simulation, "game_state") else None  # type: ignore

        if not game_state:
            raise HTTPException(status_code=400, detail="No active game")

        # Calculate hole points
        game_state.calculate_hole_points()
        updated_state = game.get_game_state()  # type: ignore

        return ActionResponse(
            game_state=updated_state,
            log_message="Hole points calculated",
            available_actions=[
                {
                    "action_type": "GET_POST_HOLE_ANALYSIS",
                    "prompt": "View Hole Analysis",
                },
                {"action_type": "ADVANCE_HOLE", "prompt": "Continue to Next Hole"},
            ],
            timeline_event={
                "id": f"points_calculated_{game_state.current_hole}_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "points_calculated",
                "description": f"Points calculated for hole {game_state.current_hole}",
                "details": {
                    "hole": game_state.current_hole,
                    "points": {p.id: p.points for p in game_state.player_manager.players},
                },
            },
        )
    except Exception as e:
        logger.error(f"Error calculating hole points: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate hole points: {e!s}")


async def handle_get_advanced_analytics(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle getting advanced analytics dashboard data"""
    try:
        analytics = game.get_advanced_analytics()
        updated_state = game.get_game_state()

        # Include analytics data in the updated game state
        updated_state["analytics"] = analytics

        return ActionResponse(
            game_state=updated_state,
            log_message="Advanced analytics data retrieved",
            available_actions=[
                {"action_type": "PLAY_SHOT", "prompt": "Continue Game"},
                {
                    "action_type": "GET_ADVANCED_ANALYTICS",
                    "prompt": "Refresh Analytics",
                },
            ],
            timeline_event={
                "id": f"analytics_viewed_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "analytics_viewed",
                "description": "Advanced analytics dashboard accessed",
                "details": analytics,  # Include full analytics data here
            },
        )
    except Exception as e:
        logger.error(f"Error getting advanced analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get advanced analytics: {e!s}")


async def handle_get_post_hole_analysis(game: WolfGoatPigGame, payload: dict[str, Any]) -> ActionResponse:
    """Handle post-hole analysis request"""
    try:
        hole_number = payload.get("hole_number", game.current_hole)

        analysis = game.get_post_hole_analysis(hole_number)
        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message=f"Post-hole analysis generated for hole {hole_number}",
            available_actions=[{"action_type": "ADVANCE_HOLE", "prompt": "Continue to next hole"}],
            timeline_event={
                "id": f"post_hole_analysis_{hole_number}_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "post_hole_analysis",
                "description": f"Comprehensive analysis of hole {hole_number}",
                "details": analysis,
            },
        )
    except Exception as e:
        logger.error(f"Error getting post-hole analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get post-hole analysis: {e!s}")
