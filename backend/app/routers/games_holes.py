"""Hole operations routes — complete, update, delete holes; rotation; wagers; quarters-only scoring."""

import json
import logging
import traceback
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import database, models, schemas
from ..managers.websocket_manager import manager as websocket_manager
from ..schemas import CompleteHoleRequest, RotationSelectionRequest
from ..services.game_lifecycle_service import get_game_lifecycle_service
from ..services.notification_service import get_notification_service
from ..wolf_goat_pig import Player, WolfGoatPigGame

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class QuartersOnlyRequest(BaseModel):
    """Simplified scoring request - just quarters per hole per player"""

    hole_quarters: dict[str, dict[str, float]]  # { "1": { "player1": 2, "player2": -2 }, ... }
    optional_details: dict[str, dict[str, Any]] | None = None  # { "1": { "notes": "..." }, ... }
    current_hole: int = 18


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/{game_id}/holes/complete", deprecated=True)
async def complete_hole(  # type: ignore
    game_id: str, request: CompleteHoleRequest, db: Session = Depends(database.get_db)
):
    """
    DEPRECATED: Use POST /games/{game_id}/quarters-only instead.

    This endpoint has complex validation for special rules (Joe's Special, Big Dick,
    Aardvark, Float, carry-over). For simplified scoring, use the quarters-only endpoint
    which only validates that each hole sums to zero.

    Complete a hole with all data at once - simplified scorekeeper mode.
    No state machine validation, just direct data storage.
    """
    try:
        # Get game from database
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Validate Joe's Special
        if request.phase == "hoepfinger" and request.joes_special_wager:
            valid_wagers = [2, 4, 8]
            if request.joes_special_wager not in valid_wagers:
                raise HTTPException(
                    status_code=400,
                    detail=f"Joe's Special must be 2, 4, or 8 quarters. Got: {request.joes_special_wager}. Joe's Special maximum is 8 quarters.",
                )

        # Phase 4: The Big Dick validation
        if request.big_dick_invoked_by:
            if request.hole_number != 18:
                raise HTTPException(
                    status_code=400,
                    detail="The Big Dick can only be invoked on hole 18",
                )

        # Phase 5: The Aardvark validation (5-man games only)
        player_count = len(request.rotation_order)
        if player_count == 5:
            # Aardvark is player in position 5 (index 4)
            aardvark_id = request.rotation_order[4]
            captain_id = request.rotation_order[request.captain_index]

            # Validate: Captain cannot DIRECTLY partner with Aardvark (meaning 2-person team)
            if request.teams.type == "partners":
                team1 = request.teams.team1 or []
                team2 = request.teams.team2 or []

                # Check if it's a 2-person team with ONLY Captain and Aardvark
                if len(team1) == 2 and set(team1) == {captain_id, aardvark_id}:
                    raise HTTPException(
                        status_code=400,
                        detail="Captain cannot directly partner with the Aardvark (player #5). Aardvark must request to join teams after Captain forms partnership.",
                    )
                if len(team2) == 2 and set(team2) == {captain_id, aardvark_id}:
                    raise HTTPException(
                        status_code=400,
                        detail="Captain cannot directly partner with the Aardvark (player #5). Aardvark must request to join teams after Captain forms partnership.",
                    )

            # Validate: Ping Pong can only happen if Aardvark was tossed
            if request.aardvark_ping_ponged and not request.aardvark_tossed:
                raise HTTPException(
                    status_code=400,
                    detail="Aardvark cannot be ping-ponged unless initially tossed. Set aardvark_tossed=True.",
                )

            # Validate: The Tunkarri (Aardvark solo with 3-for-2 payout)
            if request.tunkarri_invoked:
                if request.teams.type != "solo":
                    raise HTTPException(
                        status_code=400,
                        detail="The Tunkarri can only be invoked in solo mode (Aardvark vs all others).",
                    )
                # In solo mode, captain field contains the solo player
                if request.teams.captain != aardvark_id:
                    raise HTTPException(
                        status_code=400,
                        detail="The Tunkarri can only be invoked by the Aardvark (player #5).",
                    )

        # Hole 18 push with carry-over validation
        game_state = game.state or {}
        if request.hole_number == 18 and request.winner == "push" and game_state.get("carry_over_wager"):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot push on hole 18 with a carry-over wager of {game_state.get('carry_over_wager')}Q. Since there's no hole 19, someone must win this hole.",
            )

        # Float validation: Each captain can only use Float once per round
        if request.float_invoked_by:
            # Check if this player has already used their float
            for player in game_state.get("players", []):
                if player.get("id") == request.float_invoked_by:
                    float_used = player.get("float_used", 0)
                    if float_used >= 1:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Player {request.float_invoked_by} has already used their Float this round. Each captain can only Float once per round.",
                        )
                    break

            # Also validate that Float invoker is the captain
            captain_id = request.rotation_order[request.captain_index] if request.rotation_order else None
            if request.float_invoked_by != captain_id:
                raise HTTPException(status_code=400, detail="Only the captain can invoke Float.")

        # Validate: Tunkarri only in 5-man/6-man games
        if request.tunkarri_invoked and player_count < 5:
            raise HTTPException(
                status_code=400,
                detail="The Tunkarri is only available in 5-man or 6-man games.",
            )

        # Phase 4: Enhanced Error Handling & Validation
        rotation_player_ids = set(request.rotation_order)

        # Validate team formations FIRST (before scores)
        all_team_players = []

        if request.teams.type == "partners":
            team1 = request.teams.team1 or []
            team2 = request.teams.team2 or []
            all_team_players = team1 + team2

            # Check for duplicates within teams
            if len(team1) != len(set(team1)):
                raise HTTPException(status_code=400, detail="Duplicate players found in team1")
            if len(team2) != len(set(team2)):
                raise HTTPException(status_code=400, detail="Duplicate players found in team2")

            # Check for players on both teams
            team1_set = set(team1)
            team2_set = set(team2)
            overlap = team1_set.intersection(team2_set)
            if overlap:
                raise HTTPException(
                    status_code=400,
                    detail=f"Players cannot be on both teams: {overlap}",
                )

        elif request.teams.type == "solo":
            captain = request.teams.captain
            opponents = request.teams.opponents or []
            all_team_players = [captain] + opponents if captain else opponents

            # Validate solo formation: 1 captain vs N-1 opponents
            expected_opponent_count = len(rotation_player_ids) - 1
            if len(opponents) != expected_opponent_count:
                raise HTTPException(
                    status_code=400,
                    detail=f"Solo must be 1 vs {expected_opponent_count}. Got {len(opponents)} opponents",
                )

            # Validate: Solo player must be in rotation
            # Note: Solo player can be ANY player in rotation, not just the Captain
            # - Captain can go solo (choosing not to pick a partner)
            # - Any other player can go solo (by rejecting Captain's partnership offer)
            # - On hole 18, Big Dick allows the points leader to go solo
            if captain and captain not in rotation_player_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Solo player {captain} is not in rotation_order",
                )

            # Check for duplicates in opponents
            if len(opponents) != len(set(opponents)):
                raise HTTPException(status_code=400, detail="Duplicate players found in opponents")

            # Check captain not in opponents
            if captain and captain in opponents:
                raise HTTPException(status_code=400, detail="Captain cannot be in opponents list")

        # Validate all rotation players are on teams
        all_team_players_set = set(all_team_players)
        if all_team_players_set != rotation_player_ids:
            missing = rotation_player_ids - all_team_players_set
            extra = all_team_players_set - rotation_player_ids
            if missing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Players in rotation but not on teams: {missing}",
                )
            if extra:
                raise HTTPException(
                    status_code=400,
                    detail=f"Players on teams but not in rotation: {extra}",
                )

        # Validate scores (after team validation)
        # Check all scores are for players in rotation
        for player_id in request.scores.keys():
            if player_id not in rotation_player_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Score provided for player {player_id} not in rotation order",
                )

        # Check all rotation players have scores
        for player_id in rotation_player_ids:
            if player_id not in request.scores:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing score for player {player_id} in rotation",
                )

        # Validate score values
        for player_id, score in request.scores.items():
            if score < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Score cannot be negative. Player {player_id} has score {score}",
                )
            if score > 15:
                raise HTTPException(
                    status_code=400,
                    detail=f"Score unreasonably high (max 15). Player {player_id} has score {score}",
                )

        # Get current game state
        game_state = game.state or {}

        # Validate Float usage (once per round per player)
        if request.float_invoked_by:
            # Check if player has already used float
            for player in game_state.get("players", []):
                if player["id"] == request.float_invoked_by:
                    float_count = player.get("float_used", 0)
                    # Handle boolean False or numeric values
                    if isinstance(float_count, bool):
                        float_count = 0
                    if float_count >= 1:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Player {request.float_invoked_by} has already used float this round",
                        )
                    break

        # Initialize hole_history if it doesn't exist
        if "hole_history" not in game_state:
            game_state["hole_history"] = []

        # Helper function for Karl Marx distribution
        def apply_karl_marx(team_players, total_amount, game_state):
            """
            Distribute quarters unevenly according to Karl Marx rule:
            Player furthest down (Goat) gets smaller loss or larger win.

            Args:
                team_players: List of player IDs on the team
                total_amount: Total quarters to distribute (positive for win, negative for loss)
                game_state: Current game state with player points

            Returns:
                Dict mapping player_id -> amount
            """
            if len(team_players) == 0:
                return {}

            num_players = len(team_players)
            result = {}

            # Work with absolute value for easier math
            abs_total = abs(total_amount)
            is_loss = total_amount < 0

            # Check if distribution is uneven
            if abs_total % num_players != 0:
                # Karl Marx applies!
                base_share = abs_total // num_players
                remainder = abs_total % num_players

                # Calculate current standings for these players
                player_points = {}
                for player in game_state.get("players", []):
                    if player["id"] in team_players:
                        player_points[player["id"]] = player.get("total_points", 0)

                # Find Goat (player with lowest points)
                goat_id = min(player_points, key=player_points.get) if player_points else team_players[0]  # type: ignore

                # Distribute remainder among non-Goat players (for losses) or to Goat (for wins)
                non_goat_count = num_players - 1
                extra_per_non_goat = remainder // non_goat_count if non_goat_count > 0 else 0
                leftover_after_even_split = remainder % non_goat_count if non_goat_count > 0 else remainder

                # Assign shares
                if is_loss:
                    # LOSING: Goat loses LESS (base), non-Goat players split the remainder
                    leftover_counter = leftover_after_even_split
                    for player_id in team_players:
                        if player_id == goat_id:
                            result[player_id] = -base_share
                        else:
                            share = base_share + extra_per_non_goat
                            if leftover_counter > 0:
                                share += 1
                                leftover_counter -= 1
                            result[player_id] = -share
                else:
                    # WINNING: Goat wins MORE (gets all the remainder), non-Goat gets base
                    for player_id in team_players:
                        if player_id == goat_id:
                            result[player_id] = base_share + remainder
                        else:
                            result[player_id] = base_share
            else:
                # Even split, no Karl Marx needed
                even_amount = total_amount / num_players
                for player_id in team_players:
                    result[player_id] = even_amount

            return result

        # Calculate quarters won/lost based on winner and wager
        points_delta = {}
        if request.teams.type == "partners":
            # Calculate total amounts based on team sizes
            team1_size = len(request.teams.team1)  # type: ignore
            team2_size = len(request.teams.team2)  # type: ignore

            if request.winner == "team1":
                # Team1 wins: each winner gets wager, total = winning_team_size * wager
                # Losing team2 pays out that total
                total_won_by_team1 = request.final_wager * team1_size
                total_lost_by_team2 = -request.final_wager * team1_size
                points_delta.update(apply_karl_marx(request.teams.team1, total_won_by_team1, game_state))
                points_delta.update(apply_karl_marx(request.teams.team2, total_lost_by_team2, game_state))
            elif request.winner == "team2":
                # Team2 wins: each winner gets wager, total = winning_team_size * wager
                # Losing team1 pays out that total
                total_won_by_team2 = request.final_wager * team2_size
                total_lost_by_team1 = -request.final_wager * team2_size
                points_delta.update(apply_karl_marx(request.teams.team2, total_won_by_team2, game_state))
                points_delta.update(apply_karl_marx(request.teams.team1, total_lost_by_team1, game_state))
            elif request.winner == "team1_flush":
                # Flush: Team2 concedes/folds - Team1 wins current wager
                total_won = request.final_wager * team2_size
                total_lost = -request.final_wager * team2_size
                points_delta.update(apply_karl_marx(request.teams.team1, total_won, game_state))
                points_delta.update(apply_karl_marx(request.teams.team2, total_lost, game_state))
            elif request.winner == "team2_flush":
                # Flush: Team1 concedes/folds - Team2 wins current wager
                total_won = request.final_wager * team1_size
                total_lost = -request.final_wager * team1_size
                points_delta.update(apply_karl_marx(request.teams.team2, total_won, game_state))
                points_delta.update(apply_karl_marx(request.teams.team1, total_lost, game_state))
            else:  # push
                for player_id in request.teams.team1 + request.teams.team2:  # type: ignore
                    points_delta[player_id] = 0
        else:  # solo mode
            if request.duncan_invoked and request.winner == "captain":
                # The Duncan: Captain wins 3Q for every 2Q wagered
                total_payout = (request.final_wager * 3) / 2
                points_delta[request.teams.captain] = total_payout
                loss_per_opponent = total_payout / len(request.teams.opponents)  # type: ignore
                for opp_id in request.teams.opponents:  # type: ignore
                    points_delta[opp_id] = -loss_per_opponent
            elif request.duncan_invoked and request.winner == "opponents":
                # The Duncan failed: Opponents win normal, Captain loses normal
                total_loss = request.final_wager * len(request.teams.opponents)  # type: ignore
                points_delta[request.teams.captain] = -total_loss
                for opp_id in request.teams.opponents:  # type: ignore
                    points_delta[opp_id] = request.final_wager
            elif request.tunkarri_invoked and request.winner == "captain":
                # The Tunkarri: Aardvark wins 3Q for every 2Q wagered (5-man/6-man only)
                total_payout = (request.final_wager * 3) / 2
                points_delta[request.teams.captain] = total_payout  # Aardvark is "captain" in solo mode
                loss_per_opponent = total_payout / len(request.teams.opponents)  # type: ignore
                for opp_id in request.teams.opponents:  # type: ignore
                    points_delta[opp_id] = -loss_per_opponent
            elif request.tunkarri_invoked and request.winner == "opponents":
                # The Tunkarri failed: Opponents win normal, Aardvark loses normal
                total_loss = request.final_wager * len(request.teams.opponents)  # type: ignore
                points_delta[request.teams.captain] = -total_loss  # Aardvark is "captain" in solo mode  # type: ignore
                for opp_id in request.teams.opponents:  # type: ignore
                    points_delta[opp_id] = request.final_wager
            elif request.winner == "captain":
                # Normal solo win
                points_delta[request.teams.captain] = request.final_wager * len(request.teams.opponents)  # type: ignore
                for opp_id in request.teams.opponents:  # type: ignore
                    points_delta[opp_id] = -request.final_wager
            elif request.winner == "opponents":
                # Normal solo loss
                points_delta[request.teams.captain] = -request.final_wager * len(request.teams.opponents)  # type: ignore
                for opp_id in request.teams.opponents:  # type: ignore
                    points_delta[opp_id] = request.final_wager
            elif request.winner == "captain_flush":
                # Flush: Opponents concede/fold - Captain wins current wager
                points_delta[request.teams.captain] = request.final_wager * len(request.teams.opponents)  # type: ignore
                for opp_id in request.teams.opponents:  # type: ignore
                    points_delta[opp_id] = -request.final_wager
            elif request.winner == "opponents_flush":
                # Flush: Captain concedes/folds - Opponents win current wager
                points_delta[request.teams.captain] = -request.final_wager * len(request.teams.opponents)  # type: ignore
                for opp_id in request.teams.opponents:  # type: ignore
                    points_delta[opp_id] = request.final_wager
            else:  # push
                points_delta[request.teams.captain] = 0
                for opp_id in request.teams.opponents:  # type: ignore
                    points_delta[opp_id] = 0

        # Apply double points for holes 17-18 (except during Hoepfinger which has Joe's Special)
        if request.hole_number in [17, 18] and request.phase != "hoepfinger":
            for player_id in points_delta:
                points_delta[player_id] *= 2

        # Phase 5: Aardvark toss doubling (5-man games only)
        # When Aardvark is tossed, the wager is effectively doubled for ALL players to maintain balance
        # Ping Pong: If tossed AGAIN by second team, quadruple the points (2x for toss, 2x for ping pong)
        if player_count == 5 and request.aardvark_tossed and request.aardvark_requested_team:
            if request.teams.type == "partners":
                # Calculate multiplier: 2x for toss, 4x if ping-ponged
                multiplier = 4 if request.aardvark_ping_ponged else 2

                # Apply multiplier to all players' points to maintain zero-sum balance
                for player_id in points_delta:
                    points_delta[player_id] *= multiplier

        # Apply manual points override if provided
        if request.manual_points_override:
            override = request.manual_points_override
            logger.info(f"Manual points override for player {override.player_id}: {override.quarters}")
            points_delta[override.player_id] = override.quarters

        # Phase 4: Scorekeeping Validation - verify points balance to zero
        # Skip validation if manual override was used
        points_total = sum(points_delta.values())
        if not request.manual_points_override and abs(points_total) > 0.01:  # Allow for floating point precision
            logger.error(
                f"SCOREKEEPING ERROR: Points do not balance to zero! "
                f"Hole {request.hole_number}, Total: {points_total}, "
                f"Points: {points_delta}"
            )
            # Return error to prevent saving invalid data
            raise HTTPException(
                status_code=500,
                detail=f"Scorekeeping error: points total {points_total} instead of 0. Please report this bug.",
            )
        if request.manual_points_override and abs(points_total) > 0.01:
            logger.warning(
                f"Manual override used - points do not balance to zero. "
                f"Hole {request.hole_number}, Total: {points_total}, Points: {points_delta}"
            )

        # Calculate per-opponent quarters breakdown for display purposes
        # This helps show individual matchup results in the scorecard
        quarters_breakdown = {}  # type: ignore
        for player_id in points_delta:
            quarters_breakdown[player_id] = {}

            # For partners mode: quarters are split based on team matchups
            if request.teams.type == "partners":
                # Each player on team1 plays against each player on team2
                if player_id in request.teams.team1:  # type: ignore
                    # This player is on team1, their opponents are team2
                    opponent_count = len(request.teams.team2)  # type: ignore
                    if opponent_count > 0:
                        quarters_per_opponent = points_delta[player_id] / opponent_count
                        for opp_id in request.teams.team2:  # type: ignore
                            quarters_breakdown[player_id][opp_id] = quarters_per_opponent
                elif player_id in request.teams.team2:  # type: ignore
                    # This player is on team2, their opponents are team1
                    opponent_count = len(request.teams.team1)  # type: ignore
                    if opponent_count > 0:
                        quarters_per_opponent = points_delta[player_id] / opponent_count
                        for opp_id in request.teams.team1:  # type: ignore
                            quarters_breakdown[player_id][opp_id] = quarters_per_opponent

            # For solo mode: quarters are already per-opponent
            elif request.teams.type == "solo":
                if player_id == request.teams.captain:
                    # Solo player plays against each opponent individually
                    opponent_count = len(request.teams.opponents)  # type: ignore
                    if opponent_count > 0:
                        quarters_per_opponent = points_delta[player_id] / opponent_count
                        for opp_id in request.teams.opponents:  # type: ignore
                            quarters_breakdown[player_id][opp_id] = quarters_per_opponent
                else:
                    # Regular opponent vs the solo player
                    quarters_breakdown[player_id][request.teams.captain] = points_delta[player_id]

        # Create hole result
        hole_result = {
            "hole": request.hole_number,
            "hole_number": request.hole_number,  # Alias for consistency
            "rotation_order": request.rotation_order,
            "captain_index": request.captain_index,
            "phase": request.phase,
            "joes_special_wager": request.joes_special_wager,
            "option_turned_off": request.option_turned_off,
            "duncan_invoked": request.duncan_invoked,
            "tunkarri_invoked": (request.tunkarri_invoked if player_count >= 5 else False),
            "teams": request.teams.model_dump(),
            "wager": request.final_wager,
            "final_wager": request.final_wager,  # Phase 4: Add final_wager field
            "winner": request.winner,
            "gross_scores": request.scores,
            "hole_par": request.hole_par,
            "points_delta": points_delta,
            "quarters_breakdown": quarters_breakdown,  # Per-opponent quarters for scorecard display
            "float_invoked_by": request.float_invoked_by,
            "option_invoked_by": request.option_invoked_by,
            "carry_over_applied": request.carry_over_applied,
            "doubles_history": request.doubles_history or [],  # Phase 4: Add doubles history
            "big_dick_invoked_by": request.big_dick_invoked_by,  # Phase 4: The Big Dick
            # Phase 5: The Aardvark (5-man games only)
            "aardvark_requested_team": (request.aardvark_requested_team if player_count == 5 else None),
            "aardvark_tossed": request.aardvark_tossed if player_count == 5 else False,
            "aardvark_ping_ponged": (request.aardvark_ping_ponged if player_count == 5 else False),
            "aardvark_solo": request.aardvark_solo if player_count == 5 else False,
            # Interactive betting narrative
            "betting_narrative": request.betting_narrative,
            "betting_events": request.betting_events or [],
        }

        # Add or update hole in history
        existing_hole_index = next(
            (i for i, h in enumerate(game_state["hole_history"]) if h.get("hole") == request.hole_number),
            None,
        )

        if existing_hole_index is not None:
            game_state["hole_history"][existing_hole_index] = hole_result
        else:
            game_state["hole_history"].append(hole_result)

        # Track carry-over state
        if request.winner == "push":
            # Check if last hole was also a push (consecutive block)
            last_push_hole = game_state.get("last_push_hole")
            if last_push_hole == request.hole_number - 1:
                # Consecutive push - don't trigger new carry-over
                game_state["consecutive_push_block"] = True
                game_state["last_push_hole"] = request.hole_number
            else:
                # Trigger carry-over for next hole
                game_state["carry_over_wager"] = request.final_wager * 2
                game_state["carry_over_from_hole"] = request.hole_number
                game_state["last_push_hole"] = request.hole_number
                game_state["consecutive_push_block"] = False
        else:
            # Hole was decided - reset carry-over tracking
            if "carry_over_wager" in game_state:
                del game_state["carry_over_wager"]
            if "carry_over_from_hole" in game_state:
                del game_state["carry_over_from_hole"]
            game_state["consecutive_push_block"] = False

        # Update player totals
        if "players" not in game_state:
            game_state["players"] = []

        # Ensure all players from rotation_order are in game_state["players"]
        players_list = cast("list[dict[str, Any]]", game_state["players"])
        existing_player_ids = {p.get("id") for p in players_list}
        for player_id in request.rotation_order:
            if player_id not in existing_player_ids:
                game_state["players"].append({"id": player_id, "points": 0, "float_used": 0})

        for player in game_state["players"]:
            player_id = player.get("id")
            if player_id in points_delta:
                if "points" not in player:
                    player["points"] = 0
                player["points"] += points_delta[player_id]

            # Track float usage
            if request.float_invoked_by == player_id:
                current_float_count = player.get("float_used", 0)
                # Handle boolean False
                if isinstance(current_float_count, bool):
                    current_float_count = 0
                player["float_used"] = current_float_count + 1

        # Update current hole
        game_state["current_hole"] = request.hole_number + 1

        # Update game state in database
        game.state = game_state
        game.updated_at = datetime.now(UTC).isoformat()

        # Mark state as modified for SQLAlchemy to detect changes in JSON field
        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(game, "state")

        db.commit()
        db.refresh(game)

        # Also update simulation if game is in active_games (for test mode)
        service = get_game_lifecycle_service()
        if game_id in service._active_games:
            simulation = service._active_games[game_id]
            # Store tracking fields as direct simulation attributes
            simulation.carry_over_wager = game_state.get("carry_over_wager")  # type: ignore
            simulation.carry_over_from_hole = game_state.get("carry_over_from_hole")  # type: ignore
            simulation.consecutive_push_block = game_state.get("consecutive_push_block", False)  # type: ignore
            simulation.last_push_hole = game_state.get("last_push_hole")  # type: ignore
            simulation.base_wager = game_state.get("base_wager")  # type: ignore
            simulation.scorekeeper_hole_history = game_state.get("hole_history", [])  # type: ignore

            # Update player float/solo counts in simulation
            if request.float_invoked_by:
                float_player = next(
                    (p for p in simulation.players if p.id == request.float_invoked_by),
                    None,
                )
                if float_player:
                    float_player.float_used += 1

            # Sync player points from database game state to simulation
            for db_player in game_state.get("players", []):
                sim_player = next((p for p in simulation.players if p.id == db_player["id"]), None)
                if sim_player:
                    sim_player.points = db_player.get("points", 0)

        logger.info(f"Completed hole {request.hole_number} for game {game_id}")

        await websocket_manager.broadcast(json.dumps({"game_state": game_state}), game_id)

        # Send game end notifications when final hole (18) is completed
        if request.hole_number == 18:
            try:
                notification_service = get_notification_service()
                # Calculate final standings for notification message
                final_standings = sorted(
                    game_state.get("players", []),
                    key=lambda p: p.get("points", 0),
                    reverse=True,
                )
                winner_name = final_standings[0].get("id", "Unknown") if final_standings else "Unknown"
                winner_points = final_standings[0].get("points", 0) if final_standings else 0

                notification_service.broadcast_to_game(
                    game_id=game_id,
                    notification_type="game_end",
                    message=f"Game completed! Winner: {winner_name} with {winner_points:+.0f}Q",
                    db=db,
                    data={
                        "game_id": game_id,
                        "final_standings": [{"id": p.get("id"), "points": p.get("points", 0)} for p in final_standings],
                    },
                )
                logger.info(f"Sent game_end notifications for game {game_id}")
            except Exception as notify_error:
                # Don't fail the hole completion if notifications fail
                logger.warning(f"Failed to send game_end notifications: {notify_error}")

        return {
            "success": True,
            "game_state": game_state,
            "hole_result": hole_result,
            "message": f"Hole {request.hole_number} completed successfully",
        }

    except HTTPException:
        # Re-raise HTTPException without wrapping
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error completing hole: {e}")
        raise HTTPException(status_code=500, detail=f"Error completing hole: {e!s}")


@router.patch("/{game_id}/holes/{hole_number}")
async def update_hole(  # type: ignore
    game_id: str,
    hole_number: int,
    request: CompleteHoleRequest,
    db: Session = Depends(database.get_db),
):
    """
    Update an existing hole's data. Uses same validation as complete_hole.
    Recalculates all player totals from scratch after update.
    """
    try:
        # Validate hole_number matches request
        if request.hole_number != hole_number:
            raise HTTPException(
                status_code=400,
                detail=f"Hole number in URL ({hole_number}) must match request body ({request.hole_number})",
            )

        # Get game from database
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state or {}

        # Check if hole exists
        if "hole_history" not in game_state:
            raise HTTPException(status_code=404, detail="No holes recorded for this game")

        existing_hole_index = next(
            (i for i, h in enumerate(game_state["hole_history"]) if h.get("hole") == hole_number),
            None,
        )

        if existing_hole_index is None:
            raise HTTPException(status_code=404, detail=f"Hole {hole_number} not found in game history")

        # Validate the new hole data (reuse validation from complete_hole)
        player_count = len(request.rotation_order)

        # Validate Joe's Special
        if request.phase == "hoepfinger" and request.joes_special_wager:
            valid_wagers = [2, 4, 8]
            if request.joes_special_wager not in valid_wagers:
                raise HTTPException(
                    status_code=400,
                    detail=f"Joe's Special must be 2, 4, or 8 quarters. Got: {request.joes_special_wager}",
                )

        # Phase 4: The Big Dick validation
        if request.big_dick_invoked_by and hole_number != 18:
            raise HTTPException(status_code=400, detail="The Big Dick can only be invoked on hole 18")

        # Validate team formations
        rotation_player_ids = set(request.rotation_order)
        all_team_players = []

        if request.teams.type == "partners":
            team1 = request.teams.team1 or []
            team2 = request.teams.team2 or []
            all_team_players = team1 + team2

            if len(team1) != len(set(team1)):
                raise HTTPException(status_code=400, detail="Duplicate players in team1")
            if len(team2) != len(set(team2)):
                raise HTTPException(status_code=400, detail="Duplicate players in team2")

            overlap = set(team1).intersection(set(team2))
            if overlap:
                raise HTTPException(status_code=400, detail=f"Players on both teams: {overlap}")

        elif request.teams.type == "solo":
            captain = request.teams.captain
            opponents = request.teams.opponents or []
            all_team_players = [captain] + opponents if captain else opponents

            expected_opponent_count = len(rotation_player_ids) - 1
            if len(opponents) != expected_opponent_count:
                raise HTTPException(
                    status_code=400,
                    detail=f"Solo must be 1 vs {expected_opponent_count}. Got {len(opponents)} opponents",
                )

        # Validate all rotation players are on teams
        all_team_players_set = set(all_team_players)
        if all_team_players_set != rotation_player_ids:
            missing = rotation_player_ids - all_team_players_set
            extra = all_team_players_set - rotation_player_ids
            if missing:
                raise HTTPException(status_code=400, detail=f"Missing from teams: {missing}")
            if extra:
                raise HTTPException(status_code=400, detail=f"Not in rotation: {extra}")

        # Validate scores
        for player_id in request.scores.keys():
            if player_id not in rotation_player_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Score for player {player_id} not in rotation",
                )

        for player_id in rotation_player_ids:
            if player_id not in request.scores:
                raise HTTPException(status_code=400, detail=f"Missing score for {player_id}")

        for player_id, score in request.scores.items():
            if score < 0:
                raise HTTPException(status_code=400, detail=f"Negative score for {player_id}")
            if score > 15:
                raise HTTPException(status_code=400, detail=f"Score too high for {player_id}")

        # Recalculate points_delta using the same logic as complete_hole
        # (Extracted from complete_hole endpoint for consistency)

        # Helper function for Karl Marx distribution
        def apply_karl_marx(team_players, total_amount, game_state):
            if len(team_players) == 0:
                return {}
            num_players = len(team_players)
            result = {}
            abs_total = abs(total_amount)
            is_loss = total_amount < 0

            if abs_total % num_players != 0:
                base_share = abs_total // num_players
                remainder = abs_total % num_players
                player_points = {}
                for player in game_state.get("players", []):
                    if player["id"] in team_players:
                        player_points[player["id"]] = player.get("total_points", 0)
                goat_id = min(player_points, key=player_points.get) if player_points else team_players[0]  # type: ignore
                non_goat_count = num_players - 1
                extra_per_non_goat = remainder // non_goat_count if non_goat_count > 0 else 0
                leftover_after_even_split = remainder % non_goat_count if non_goat_count > 0 else remainder

                if is_loss:
                    leftover_counter = leftover_after_even_split
                    for player_id in team_players:
                        if player_id == goat_id:
                            result[player_id] = -base_share
                        else:
                            share = base_share + extra_per_non_goat
                            if leftover_counter > 0:
                                share += 1
                                leftover_counter -= 1
                            result[player_id] = -share
                else:
                    for player_id in team_players:
                        if player_id == goat_id:
                            result[player_id] = base_share + remainder
                        else:
                            result[player_id] = base_share
            else:
                even_amount = total_amount / num_players
                for player_id in team_players:
                    result[player_id] = even_amount
            return result

        # Calculate points_delta based on winner and teams
        points_delta = {}
        if request.teams.type == "partners":
            team1_size = len(request.teams.team1)  # type: ignore
            team2_size = len(request.teams.team2)  # type: ignore

            if request.winner == "team1":
                total_won_by_team1 = request.final_wager * team1_size
                total_lost_by_team2 = -request.final_wager * team1_size
                points_delta.update(apply_karl_marx(request.teams.team1, total_won_by_team1, game_state))
                points_delta.update(apply_karl_marx(request.teams.team2, total_lost_by_team2, game_state))
            elif request.winner == "team2":
                total_won_by_team2 = request.final_wager * team2_size
                total_lost_by_team1 = -request.final_wager * team2_size
                points_delta.update(apply_karl_marx(request.teams.team2, total_won_by_team2, game_state))
                points_delta.update(apply_karl_marx(request.teams.team1, total_lost_by_team1, game_state))
            elif request.winner == "team1_flush":
                total_won = request.final_wager * team2_size
                total_lost = -request.final_wager * team2_size
                points_delta.update(apply_karl_marx(request.teams.team1, total_won, game_state))
                points_delta.update(apply_karl_marx(request.teams.team2, total_lost, game_state))
            elif request.winner == "team2_flush":
                total_won = request.final_wager * team1_size
                total_lost = -request.final_wager * team1_size
                points_delta.update(apply_karl_marx(request.teams.team2, total_won, game_state))
                points_delta.update(apply_karl_marx(request.teams.team1, total_lost, game_state))
            else:  # push
                for player_id in request.teams.team1 + request.teams.team2:  # type: ignore
                    points_delta[player_id] = 0
        else:  # solo mode
            if request.duncan_invoked and request.winner == "captain":
                total_payout = (request.final_wager * 3) / 2
                points_delta[request.teams.captain] = total_payout
                loss_per_opponent = total_payout / len(request.teams.opponents)  # type: ignore
                for opp_id in request.teams.opponents:  # type: ignore
                    points_delta[opp_id] = -loss_per_opponent
            elif request.duncan_invoked and request.winner == "opponents":
                total_loss = request.final_wager * len(request.teams.opponents)  # type: ignore
                points_delta[request.teams.captain] = -total_loss
                for opp_id in request.teams.opponents:  # type: ignore
                    points_delta[opp_id] = request.final_wager
            elif request.tunkarri_invoked and request.winner == "captain":
                total_payout = (request.final_wager * 3) / 2
                points_delta[request.teams.captain] = total_payout
                loss_per_opponent = total_payout / len(request.teams.opponents)  # type: ignore
                for opp_id in request.teams.opponents:  # type: ignore
                    points_delta[opp_id] = -loss_per_opponent
            elif request.tunkarri_invoked and request.winner == "opponents":
                total_loss = request.final_wager * len(request.teams.opponents)  # type: ignore
                points_delta[request.teams.captain] = -total_loss
                for opp_id in request.teams.opponents:  # type: ignore
                    points_delta[opp_id] = request.final_wager
            elif request.winner == "captain":
                points_delta[request.teams.captain] = request.final_wager * len(request.teams.opponents)  # type: ignore
                for opp_id in request.teams.opponents:  # type: ignore
                    points_delta[opp_id] = -request.final_wager
            elif request.winner == "opponents":
                points_delta[request.teams.captain] = -request.final_wager * len(request.teams.opponents)  # type: ignore
                for opp_id in request.teams.opponents:  # type: ignore
                    points_delta[opp_id] = request.final_wager
            elif request.winner == "captain_flush":
                points_delta[request.teams.captain] = request.final_wager * len(request.teams.opponents)  # type: ignore
                for opp_id in request.teams.opponents:  # type: ignore
                    points_delta[opp_id] = -request.final_wager
            elif request.winner == "opponents_flush":
                points_delta[request.teams.captain] = -request.final_wager * len(request.teams.opponents)  # type: ignore
                for opp_id in request.teams.opponents:  # type: ignore
                    points_delta[opp_id] = request.final_wager
            else:  # push
                points_delta[request.teams.captain] = 0
                for opp_id in request.teams.opponents:  # type: ignore
                    points_delta[opp_id] = 0

        # Apply double points for holes 17-18 (except during Hoepfinger)
        if hole_number in [17, 18] and request.phase != "hoepfinger":
            for player_id in points_delta:
                points_delta[player_id] *= 2

        # Phase 5: Aardvark toss doubling (5-man games only)
        if player_count == 5 and request.aardvark_tossed and request.aardvark_requested_team:
            if request.teams.type == "partners":
                multiplier = 4 if request.aardvark_ping_ponged else 2
                for player_id in points_delta:
                    points_delta[player_id] *= multiplier

        # Apply manual points override if provided
        if request.manual_points_override:
            override = request.manual_points_override
            logger.info(f"Manual points override for player {override.player_id}: {override.quarters}")
            points_delta[override.player_id] = override.quarters

        # Calculate per-opponent quarters breakdown for display purposes
        quarters_breakdown = {}  # type: ignore
        for player_id in points_delta:
            quarters_breakdown[player_id] = {}

            # For partners mode: quarters are split based on team matchups
            if request.teams.type == "partners":
                if player_id in request.teams.team1:  # type: ignore
                    opponent_count = len(request.teams.team2)  # type: ignore
                    if opponent_count > 0:
                        quarters_per_opponent = points_delta[player_id] / opponent_count
                        for opp_id in request.teams.team2:  # type: ignore
                            quarters_breakdown[player_id][opp_id] = quarters_per_opponent
                elif player_id in request.teams.team2:  # type: ignore
                    opponent_count = len(request.teams.team1)  # type: ignore
                    if opponent_count > 0:
                        quarters_per_opponent = points_delta[player_id] / opponent_count
                        for opp_id in request.teams.team1:  # type: ignore
                            quarters_breakdown[player_id][opp_id] = quarters_per_opponent

            # For solo mode: quarters are already per-opponent
            elif request.teams.type == "solo":
                if player_id == request.teams.captain:
                    opponent_count = len(request.teams.opponents)  # type: ignore
                    if opponent_count > 0:
                        quarters_per_opponent = points_delta[player_id] / opponent_count
                        for opp_id in request.teams.opponents:  # type: ignore
                            quarters_breakdown[player_id][opp_id] = quarters_per_opponent
                else:
                    quarters_breakdown[player_id][request.teams.captain] = points_delta[player_id]

        # Create updated hole result
        hole_result = {
            "hole": hole_number,
            "hole_number": hole_number,
            "rotation_order": request.rotation_order,
            "captain_index": request.captain_index,
            "phase": request.phase,
            "joes_special_wager": request.joes_special_wager,
            "option_turned_off": request.option_turned_off,
            "duncan_invoked": request.duncan_invoked,
            "tunkarri_invoked": (request.tunkarri_invoked if player_count >= 5 else False),
            "teams": request.teams.model_dump(),
            "wager": request.final_wager,
            "final_wager": request.final_wager,
            "winner": request.winner,
            "gross_scores": request.scores,
            "hole_par": request.hole_par,
            "points_delta": points_delta,
            "quarters_breakdown": quarters_breakdown,
            "float_invoked_by": request.float_invoked_by,
            "option_invoked_by": request.option_invoked_by,
            "carry_over_applied": request.carry_over_applied,
            "doubles_history": request.doubles_history or [],
            "big_dick_invoked_by": request.big_dick_invoked_by,
            "aardvark_requested_team": (request.aardvark_requested_team if player_count == 5 else None),
            "aardvark_tossed": request.aardvark_tossed if player_count == 5 else False,
            "aardvark_ping_ponged": (request.aardvark_ping_ponged if player_count == 5 else False),
            "aardvark_solo": request.aardvark_solo if player_count == 5 else False,
            # Interactive betting narrative
            "betting_narrative": request.betting_narrative,
            "betting_events": request.betting_events or [],
        }

        # Update the hole in history
        game_state["hole_history"][existing_hole_index] = hole_result

        # Recalculate all player totals from scratch
        # Reset all player points and float usage
        for player in game_state.get("players", []):
            player["points"] = 0
            player["float_used"] = 0

        # Replay all holes to recalculate totals
        # (This ensures consistency if hole was modified)
        # Note: This is a simplified version - for full accuracy, would need to
        # recalculate Karl Marx distribution for each hole
        for hole in game_state["hole_history"]:
            points_delta = hole.get("points_delta", {})
            for player in game_state.get("players", []):
                player_id = player.get("id")
                if player_id in points_delta:
                    player["points"] += points_delta[player_id]

                # Track float usage
                if hole.get("float_invoked_by") == player_id:
                    player["float_used"] += 1

        # Update game state in database
        game.state = game_state
        game.updated_at = datetime.now(UTC).isoformat()

        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(game, "state")

        db.commit()
        db.refresh(game)

        logger.info(f"Updated hole {hole_number} for game {game_id}")

        await websocket_manager.broadcast(json.dumps({"game_state": game_state}), game_id)
        return {
            "success": True,
            "game_state": game_state,
            "hole_result": hole_result,
            "message": f"Hole {hole_number} updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating hole: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating hole: {e!s}")


@router.delete("/{game_id}/holes/{hole_number}")
async def delete_hole(game_id: str, hole_number: int, db: Session = Depends(database.get_db)):  # type: ignore
    """
    Delete a hole from hole_history.
    Recalculates all player totals and updates current_hole if needed.
    """
    try:
        # Get game from database
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state or {}

        # Check if hole exists
        if "hole_history" not in game_state or not game_state["hole_history"]:
            raise HTTPException(status_code=404, detail="No holes recorded for this game")

        existing_hole_index = next(
            (i for i, h in enumerate(game_state["hole_history"]) if h.get("hole") == hole_number),
            None,
        )

        if existing_hole_index is None:
            raise HTTPException(status_code=404, detail=f"Hole {hole_number} not found in game history")

        # Remove the hole from history
        deleted_hole = game_state["hole_history"].pop(existing_hole_index)

        # Recalculate all player totals from scratch
        # Reset all player points and float usage
        for player in game_state.get("players", []):
            player["points"] = 0
            player["float_used"] = 0

        # Replay remaining holes to recalculate totals
        for hole in game_state["hole_history"]:
            points_delta = hole.get("points_delta", {})
            for player in game_state.get("players", []):
                player_id = player.get("id")
                if player_id in points_delta:
                    player["points"] += points_delta[player_id]

                # Track float usage
                if hole.get("float_invoked_by") == player_id:
                    player["float_used"] += 1

        # Update current_hole if the deleted hole was the last one played
        max_hole_played = max([h.get("hole", 0) for h in game_state["hole_history"]], default=0)
        game_state["current_hole"] = max_hole_played + 1

        # Update game state in database
        game.state = game_state
        game.updated_at = datetime.now(UTC).isoformat()

        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(game, "state")

        db.commit()
        db.refresh(game)

        logger.info(f"Deleted hole {hole_number} from game {game_id}")

        return {
            "success": True,
            "game_state": game_state,
            "deleted_hole": deleted_hole,
            "message": f"Hole {hole_number} deleted successfully",
            "remaining_holes": len(game_state["hole_history"]),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting hole: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting hole: {e!s}")


@router.get("/{game_id}/next-rotation", deprecated=True)
async def get_next_rotation(game_id: str, db: Session = Depends(database.get_db)):  # type: ignore
    """
    DEPRECATED: Not needed for quarters-only scoring.

    Calculate the next rotation order based on current hole.
    Handles normal rotation and Hoepfinger special selection.
    Only needed if tracking complex game mechanics (rotation, Hoepfinger, etc).
    """
    try:
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state or {}
        player_count = len(game_state.get("players", []))

        # Use game_state.get("current_hole", 1) for current_hole
        current_hole = game_state.get("current_hole", 1)

        # Determine Hoepfinger start based on player count
        hoepfinger_start = {4: 17, 5: 16, 6: 13}.get(player_count, 17)

        is_hoepfinger = current_hole >= hoepfinger_start

        # Get last hole's rotation
        hole_history = game_state.get("hole_history", [])
        is_first_hole = len(hole_history) == 0

        if hole_history:
            last_hole = hole_history[-1]
            last_rotation = last_hole.get("rotation_order", [p["id"] for p in game_state["players"]])
        else:
            # First hole - use player order (sorted by tee_order)
            last_rotation = [p["id"] for p in game_state["players"]]

        if is_hoepfinger:
            # Hoepfinger: Goat (furthest down) selects position
            # Calculate current standings
            standings = {}
            for player in game_state["players"]:
                standings[player["id"]] = player.get("points", 0)

            goat_id = min(standings, key=standings.get)  # type: ignore

            return {
                "is_hoepfinger": True,
                "goat_id": goat_id,
                "goat_selects_position": True,
                "available_positions": list(range(player_count)),
                "current_rotation": last_rotation,
                "message": "Goat selects hitting position",
            }
        if is_first_hole:
            # First hole - use initial tee order without rotation
            new_rotation = last_rotation
        else:
            # Normal rotation: shift left by 1 from previous hole
            new_rotation = last_rotation[1:] + [last_rotation[0]]

        return {
            "is_hoepfinger": False,
            "rotation_order": new_rotation,
            "captain_index": 0,
            "captain_id": new_rotation[0],
        }

    except Exception as e:
        logger.error(f"Error calculating next rotation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{game_id}/next-hole-wager", deprecated=True)
async def get_next_hole_wager(  # type: ignore
    game_id: str,
    current_hole: int | None = None,
    db: Session = Depends(database.get_db),
):
    """
    DEPRECATED: Not needed for quarters-only scoring.

    Calculate the base wager for the next hole.
    Accounts for carry-over, Vinnie's Variation, and Hoepfinger rules.
    Only needed if tracking complex game mechanics (wager escalation, carry-over, etc).
    """
    try:
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state or {}
        player_count = len(game_state.get("players", []))

        # Use provided current_hole or get from game state
        if current_hole is None:
            current_hole = game_state.get("current_hole", 1)

        base_wager = game_state.get("base_wager", 1)

        # Check for carry-over
        if game_state.get("carry_over_wager"):
            carry_over_wager = game_state["carry_over_wager"]
            from_hole = game_state.get("carry_over_from_hole", current_hole - 1)

            if game_state.get("consecutive_push_block"):
                return {
                    "base_wager": carry_over_wager,
                    "carry_over": False,
                    "message": f"Consecutive carry-over blocked. Base wager remains {carry_over_wager}Q from hole {from_hole}",
                }
            return {
                "base_wager": carry_over_wager,
                "carry_over": True,
                "message": f"Carry-over from hole {from_hole} push",
            }

        # Check for The Option (Captain is Goat)
        if not game_state.get("carry_over_wager"):  # Option doesn't stack with carry-over
            # Calculate current standings to find Goat
            standings = {}
            for player in game_state.get("players", []):
                standings[player["id"]] = player.get("points", 0)

            if standings:
                goat_id = min(standings, key=standings.get)  # type: ignore
                goat_points = standings[goat_id]

                # Option applies if Captain (first in rotation) is the Goat AND has negative points
                hole_history = game_state.get("hole_history", [])
                if hole_history:
                    last_hole = hole_history[-1]
                    next_rotation_order = last_hole.get("rotation_order", [])[1:] + [
                        last_hole.get("rotation_order", [])[0]
                    ]
                    next_captain_id = next_rotation_order[0] if next_rotation_order else None

                    if next_captain_id == goat_id and goat_points < 0:
                        # Check if last hole turned off Option
                        if not last_hole.get("option_turned_off", False):
                            return {
                                "base_wager": base_wager * 2,
                                "option_active": True,
                                "goat_id": goat_id,
                                "carry_over": False,
                                "vinnies_variation": False,
                                "message": f"The Option: Captain is Goat ({goat_points}Q), wager doubled",
                            }

        # Check for Vinnie's Variation (holes 13-16 in 4-player)
        if player_count == 4 and 13 <= current_hole <= 16:
            return {
                "base_wager": base_wager * 2,
                "vinnies_variation": True,
                "carry_over": False,
                "message": f"Vinnie's Variation: holes 13-16 doubled (hole {current_hole})",
            }

        # Normal base wager
        return {
            "base_wager": base_wager,
            "carry_over": False,
            "vinnies_variation": False,
            "message": "Normal base wager",
        }

    except Exception as e:
        logger.error(f"Error calculating next hole wager: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{game_id}/select-rotation", deprecated=True)
async def select_rotation(  # type: ignore
    game_id: str,
    request: RotationSelectionRequest,
    db: Session = Depends(database.get_db),
):
    """
    DEPRECATED: Not needed for quarters-only scoring.

    Phase 5: Dynamic rotation selection for 5-man games on holes 16-18.
    The Goat (lowest points player) selects their position in the rotation.
    Only needed for complex 5-man game Hoepfinger mechanics.
    """
    # Get game state (follow same pattern as get_game_state_by_id)
    service = get_game_lifecycle_service()
    simulation = None
    game = None
    game_state = None

    if game_id in service._active_games:
        simulation = service._active_games[game_id]
        game_state = simulation.get_game_state()
    else:
        # Fetch from database
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state

    if not game_state:
        raise HTTPException(status_code=404, detail="Game state not found")

    player_count = len(game_state.get("players", []))

    # Validate: Only 5-man games
    if player_count != 5:
        raise HTTPException(
            status_code=400,
            detail="Dynamic rotation selection only applies to 5-player games",
        )

    # Validate: Only holes 16, 17, 18
    if request.hole_number not in [16, 17, 18]:
        raise HTTPException(
            status_code=400,
            detail="Rotation selection only allowed on holes 16, 17, and 18",
        )

    # Validate: Position must be 1-5 for 5-man game
    if request.selected_position < 1 or request.selected_position > 5:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid position {request.selected_position}. Must be 1-5 for 5-player games",
        )

    # Identify current Goat (player with lowest total points)
    players = game_state.get("players", [])
    if not players:
        raise HTTPException(status_code=404, detail="No players found in game")

    # Find player with lowest points
    goat_player = min(players, key=lambda p: p.get("points", 0))
    actual_goat_id = goat_player["id"]

    # Validate: Request must be from actual Goat
    if request.goat_player_id != actual_goat_id:
        raise HTTPException(
            status_code=400,
            detail=f"Only the Goat (player with lowest points) can select rotation. Current Goat is {actual_goat_id}, not {request.goat_player_id}",
        )

    # Get current rotation order (or use default player order)
    current_rotation = game_state.get("current_rotation_order") or [p["id"] for p in players]

    # Reorder rotation: Goat at selected position, others maintain relative order
    goat_id = request.goat_player_id
    selected_index = request.selected_position - 1  # Convert to 0-indexed

    # Remove Goat from current rotation
    rotation_without_goat = [pid for pid in current_rotation if pid != goat_id]

    # Insert Goat at selected position
    new_rotation = rotation_without_goat[:selected_index] + [goat_id] + rotation_without_goat[selected_index:]

    # Store new rotation in game state
    game_state["current_rotation_order"] = new_rotation

    # Save updated rotation
    if simulation:
        # Update simulation state for in-progress games
        simulation._game_state = game_state  # type: ignore
    else:
        # Update database for stored games
        assert game is not None  # game is guaranteed non-None here (we returned 404 if None)
        game.state = game_state
        db.commit()

    return {
        "message": f"Rotation updated for hole {request.hole_number}",
        "rotation_order": new_rotation,
        "goat_id": goat_id,
        "selected_position": request.selected_position,
    }


@router.post("/{game_id}/quarters-only")
async def save_quarters_only(game_id: str, request: QuartersOnlyRequest, db: Session = Depends(database.get_db)):
    """
    Simplified scoring endpoint - just quarters per hole per player.
    Only validation: each hole must sum to zero (zero-sum game).

    This replaces the complex hole completion flow with a simple:
    1. Enter quarters (+/-) for each player per hole
    2. Validate sum is zero
    3. Save
    """
    try:
        # Get game from database
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Validate: Each hole must sum to zero
        validation_errors = []
        for hole_str, player_quarters in request.hole_quarters.items():
            hole_sum = sum(player_quarters.values())
            if abs(hole_sum) > 0.001:  # Allow small floating point errors
                validation_errors.append(f"Hole {hole_str}: sum is {hole_sum}, must be 0")

        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail=f"Zero-sum validation failed: {'; '.join(validation_errors)}",
            )

        # Calculate standings
        standings = {}
        for hole_str, player_quarters in request.hole_quarters.items():
            for player_id, quarters in player_quarters.items():
                if player_id not in standings:
                    standings[player_id] = 0
                standings[player_id] += quarters

        # Update game state with simplified data
        game_state = game.state or {}
        game_state["quarters_only_mode"] = True
        game_state["hole_quarters"] = request.hole_quarters
        game_state["optional_details"] = request.optional_details or {}
        game_state["current_hole"] = request.current_hole
        game_state["standings"] = standings

        # Update player points in game state
        for player in game_state.get("players", []):
            player_id = player.get("id")
            if player_id in standings:
                player["total_points"] = standings[player_id]

        # Convert hole_quarters to hole_history format for compatibility
        # Include all optional details (teams, winner, wager, gross_scores, phase, notes)
        hole_history = []
        for hole_num in range(1, 19):
            hole_str = str(hole_num)
            if hole_str in request.hole_quarters:
                # Get all optional details for this hole
                hole_details = (request.optional_details or {}).get(hole_str, {})
                hole_entry = {
                    "hole": hole_num,
                    "points_delta": request.hole_quarters[hole_str],
                    "quarters_only": True,
                    "notes": hole_details.get("notes", ""),
                    # Include all other fields from optional_details
                    "teams": hole_details.get("teams"),
                    "winner": hole_details.get("winner"),
                    "wager": hole_details.get("wager"),
                    "gross_scores": hole_details.get("gross_scores"),
                    "phase": hole_details.get("phase"),
                }
                hole_history.append(hole_entry)
        game_state["hole_history"] = hole_history

        # Mark game status based on holes completed
        holes_with_data = len([h for h in request.hole_quarters.values() if h])
        if holes_with_data >= 18:
            game_state["game_status"] = "completed"
            game.game_status = "completed"
        elif holes_with_data > 0:
            game_state["game_status"] = "in_progress"
            game.game_status = "in_progress"

        game.state = game_state
        db.commit()

        logger.info(f"Saved quarters-only data for game {game_id}: {holes_with_data} holes")

        return {
            "success": True,
            "game_id": game_id,
            "holes_saved": holes_with_data,
            "standings": standings,
            "game_status": game.game_status,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving quarters-only data for game {game_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error saving data: {e!s}")
