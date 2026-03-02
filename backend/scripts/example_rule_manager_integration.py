"""
Example integration of RuleManager with FastAPI endpoints.

This demonstrates how to use the RuleManager in actual API routes
to validate game actions and enforce rules.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.managers import RuleManager, RuleViolationError

app = FastAPI()


# Request/Response Models
class PartnershipRequest(BaseModel):
    captain_id: str
    partner_id: str


class BettingActionRequest(BaseModel):
    player_id: str
    action_type: str  # "double", "redouble", "duncan"


class PlayerActionsResponse(BaseModel):
    player_id: str
    available_actions: List[str]


class HoleResultsRequest(BaseModel):
    results: dict  # player_id -> net_score


class HandicapStrokesRequest(BaseModel):
    hole_number: int
    player_handicaps: dict  # player_id -> handicap
    hole_stroke_index: int


# Mock function to get game state (replace with actual DB query)
def get_game_state(game_id: str) -> dict:
    """Fetch current game state from database."""
    # This would be replaced with actual database query
    return {
        "game_id": game_id,
        "players": [
            {"id": "player_1", "name": "Alice", "handicap": 10.0},
            {"id": "player_2", "name": "Bob", "handicap": 15.0},
            {"id": "player_3", "name": "Charlie", "handicap": 8.0},
        ],
        "current_hole_number": 1,
        "current_hole": {
            "hole_number": 1,
            "par": 4,
            "yards": 420,
            "stroke_index": 5,
            "hitting_order": ["player_1", "player_2", "player_3"],
            "teams": {},
            "betting": {
                "base_wager": 1,
                "current_wager": 1,
                "doubled": False,
                "redoubled": False,
                "duncan_invoked": False,
            },
            "tee_shots_complete": 0,
            "partnership_deadline_passed": False,
            "wagering_closed": False,
            "hole_complete": False,
            "balls_in_hole": [],
            "next_player_to_hit": "player_1",
        }
    }


# API Endpoints

@app.post("/api/game/{game_id}/partnership")
async def form_partnership(game_id: str, request: PartnershipRequest):
    """
    Form a partnership between captain and partner.

    Validates the partnership request using RuleManager before creating.
    """
    manager = RuleManager.get_instance()

    try:
        # Get current game state
        game_state = get_game_state(game_id)

        # Validate partnership using RuleManager
        can_form = manager.can_form_partnership(
            captain_id=request.captain_id,
            partner_id=request.partner_id,
            game_state=game_state
        )

        if can_form:
            # Here you would update the game state in database
            # update_game_state(game_id, partnership=...)

            return {
                "status": "success",
                "message": f"Partnership formed: {request.captain_id} + {request.partner_id}",
                "partnership": {
                    "captain": request.captain_id,
                    "partner": request.partner_id
                }
            }

    except RuleViolationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Partnership validation failed",
                "reason": e.message,
                "field": e.field,
                "details": e.details
            }
        )


@app.post("/api/game/{game_id}/lone-wolf")
async def go_lone_wolf(game_id: str, player_id: str):
    """
    Player attempts to go lone wolf (solo against all).

    Validates using RuleManager before allowing.
    """
    manager = RuleManager.get_instance()

    try:
        game_state = get_game_state(game_id)

        # Validate lone wolf action
        can_go_lone = manager.can_go_lone_wolf(player_id, game_state)

        if can_go_lone:
            # Update game state
            # update_game_state(game_id, lone_wolf=player_id)

            return {
                "status": "success",
                "message": f"Player {player_id} is going lone wolf!",
                "lone_wolf": player_id
            }

    except RuleViolationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Lone wolf validation failed",
                "reason": e.message,
                "field": e.field,
                "details": e.details
            }
        )


@app.post("/api/game/{game_id}/betting-action")
async def betting_action(game_id: str, request: BettingActionRequest):
    """
    Execute a betting action (double, redouble, duncan).

    Validates the action using RuleManager before applying.
    """
    manager = RuleManager.get_instance()

    try:
        game_state = get_game_state(game_id)

        # Validate betting action
        is_valid = manager.validate_betting_action(
            player_id=request.player_id,
            action_type=request.action_type,
            game_state=game_state
        )

        if is_valid:
            # Apply betting action to game state
            # apply_betting_action(game_id, request.action_type)

            return {
                "status": "success",
                "message": f"Betting action '{request.action_type}' applied",
                "action": request.action_type,
                "player": request.player_id
            }

    except RuleViolationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Cannot perform {request.action_type}",
                "reason": e.message,
                "field": e.field,
                "details": e.details
            }
        )


@app.get("/api/game/{game_id}/actions/{player_id}")
async def get_player_actions(game_id: str, player_id: str) -> PlayerActionsResponse:
    """
    Get list of valid actions for a player.

    This is useful for the frontend to show/hide action buttons.
    """
    manager = RuleManager.get_instance()

    try:
        game_state = get_game_state(game_id)

        # Get valid actions using RuleManager
        actions = manager.get_valid_actions(player_id, game_state)

        return PlayerActionsResponse(
            player_id=player_id,
            available_actions=actions
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get player actions",
                "reason": str(e)
            }
        )


@app.post("/api/game/{game_id}/hole-complete")
async def complete_hole(game_id: str, request: HoleResultsRequest):
    """
    Complete a hole and determine the winner.

    Uses RuleManager to calculate winner based on net scores.
    """
    manager = RuleManager.get_instance()

    try:
        # Calculate hole winner
        winner = manager.calculate_hole_winner(request.results)

        if winner:
            return {
                "status": "success",
                "winner": winner,
                "results": request.results,
                "carry_over": False
            }
        else:
            return {
                "status": "success",
                "winner": None,
                "results": request.results,
                "carry_over": True,
                "message": "Hole tied - wager carries over"
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to complete hole",
                "reason": str(e)
            }
        )


@app.post("/api/game/{game_id}/handicap-strokes")
async def get_handicap_strokes(game_id: str, request: HandicapStrokesRequest):
    """
    Calculate handicap strokes for each player on a hole.

    Uses USGA stroke allocation via RuleManager.
    """
    manager = RuleManager.get_instance()

    try:
        strokes = manager.apply_handicap_strokes(
            hole_number=request.hole_number,
            player_handicaps=request.player_handicaps,
            hole_stroke_index=request.hole_stroke_index
        )

        return {
            "status": "success",
            "hole_number": request.hole_number,
            "stroke_index": request.hole_stroke_index,
            "strokes": strokes
        }

    except RuleViolationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Handicap calculation failed",
                "reason": e.message,
                "field": e.field,
                "details": e.details
            }
        )


@app.get("/api/rules/summary")
async def get_rules():
    """
    Get a summary of all game rules.

    Useful for displaying rules to players.
    """
    manager = RuleManager.get_instance()

    summary = manager.get_rule_summary()

    return {
        "status": "success",
        "rules": summary
    }


@app.post("/api/game/{game_id}/validate-turn/{player_id}")
async def validate_turn(game_id: str, player_id: str):
    """
    Check if it's a player's turn.

    Returns validation result without raising exception.
    """
    manager = RuleManager.get_instance()

    try:
        game_state = get_game_state(game_id)

        is_turn = manager.validate_player_turn(player_id, game_state)

        return {
            "status": "success",
            "is_turn": is_turn,
            "player_id": player_id
        }

    except RuleViolationError as e:
        return {
            "status": "not_turn",
            "is_turn": False,
            "player_id": player_id,
            "reason": e.message,
            "next_player": e.details.get("next_player")
        }


# Middleware example: Validate all game actions
@app.middleware("http")
async def validate_game_state(request, call_next):
    """
    Example middleware to validate game state for all requests.

    You could use this to ensure game state is valid before processing
    any action.
    """
    # Skip validation for non-game routes
    if not request.url.path.startswith("/api/game/"):
        return await call_next(request)

    # Process request
    response = await call_next(request)

    return response


if __name__ == "__main__":
    import uvicorn

    print("Starting example RuleManager API server...")
    print("Visit http://localhost:8000/docs for API documentation")

    uvicorn.run(app, host="0.0.0.0", port=8000)
