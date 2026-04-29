"""Service for hole completion business logic — validation, scoring, and state persistence."""

import logging
from typing import Any, cast

from fastapi import HTTPException

from ..schemas import CompleteHoleRequest

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_joes_special(request: CompleteHoleRequest) -> None:
    """Validate Joe's Special wager (Hoepfinger phase only)."""
    if request.phase == "hoepfinger" and request.joes_special_wager:
        valid_wagers = [2, 4, 8]
        if request.joes_special_wager not in valid_wagers:
            raise HTTPException(
                status_code=400,
                detail=f"Joe's Special must be 2, 4, or 8 quarters. Got: {request.joes_special_wager}. Joe's Special maximum is 8 quarters.",
            )


def validate_big_dick(request: CompleteHoleRequest) -> None:
    """Validate The Big Dick — can only be invoked on hole 18."""
    if request.big_dick_invoked_by:
        if request.hole_number != 18:
            raise HTTPException(
                status_code=400,
                detail="The Big Dick can only be invoked on hole 18",
            )


def validate_aardvark(request: CompleteHoleRequest, player_count: int) -> None:
    """Validate Aardvark rules for 5-man games."""
    if player_count != 5:
        return

    aardvark_id = request.rotation_order[4]
    captain_id = request.rotation_order[request.captain_index]

    # Captain cannot DIRECTLY partner with Aardvark (2-person team)
    if request.teams.type == "partners":
        team1 = request.teams.team1 or []
        team2 = request.teams.team2 or []

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

    # Ping Pong requires toss first
    if request.aardvark_ping_ponged and not request.aardvark_tossed:
        raise HTTPException(
            status_code=400,
            detail="Aardvark cannot be ping-ponged unless initially tossed. Set aardvark_tossed=True.",
        )

    # The Tunkarri validation
    if request.tunkarri_invoked:
        if request.teams.type != "solo":
            raise HTTPException(
                status_code=400,
                detail="The Tunkarri can only be invoked in solo mode (Aardvark vs all others).",
            )
        if request.teams.captain != aardvark_id:
            raise HTTPException(
                status_code=400,
                detail="The Tunkarri can only be invoked by the Aardvark (player #5).",
            )


def validate_carry_over_hole_18(request: CompleteHoleRequest, game_state: dict[str, Any]) -> None:
    """Cannot push on hole 18 with a carry-over wager."""
    if request.hole_number == 18 and request.winner == "push" and game_state.get("carry_over_wager"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot push on hole 18 with a carry-over wager of {game_state.get('carry_over_wager')}Q. Since there's no hole 19, someone must win this hole.",
        )


def validate_float(request: CompleteHoleRequest, game_state: dict[str, Any]) -> None:
    """Validate Float — each captain can only use Float once per round."""
    if not request.float_invoked_by:
        return

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

    # Float invoker must be the captain
    captain_id = request.rotation_order[request.captain_index] if request.rotation_order else None
    if request.float_invoked_by != captain_id:
        raise HTTPException(status_code=400, detail="Only the captain can invoke Float.")


def validate_tunkarri_player_count(request: CompleteHoleRequest, player_count: int) -> None:
    """Tunkarri only available in 5-man/6-man games."""
    if request.tunkarri_invoked and player_count < 5:
        raise HTTPException(
            status_code=400,
            detail="The Tunkarri is only available in 5-man or 6-man games.",
        )


def validate_team_formations(request: CompleteHoleRequest) -> None:
    """Validate team formations — no duplicates, no overlaps, all players accounted for."""
    rotation_player_ids = set(request.rotation_order)
    all_team_players: list[str] = []

    if request.teams.type == "partners":
        team1 = request.teams.team1 or []
        team2 = request.teams.team2 or []
        all_team_players = team1 + team2

        if len(team1) != len(set(team1)):
            raise HTTPException(status_code=400, detail="Duplicate players found in team1")
        if len(team2) != len(set(team2)):
            raise HTTPException(status_code=400, detail="Duplicate players found in team2")

        overlap = set(team1).intersection(set(team2))
        if overlap:
            raise HTTPException(
                status_code=400,
                detail=f"Players cannot be on both teams: {overlap}",
            )

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

        if captain and captain not in rotation_player_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Solo player {captain} is not in rotation_order",
            )

        if len(opponents) != len(set(opponents)):
            raise HTTPException(status_code=400, detail="Duplicate players found in opponents")

        if captain and captain in opponents:
            raise HTTPException(status_code=400, detail="Captain cannot be in opponents list")

    # All rotation players must be on teams
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


def validate_scores(request: CompleteHoleRequest) -> None:
    """Validate scores — all rotation players have valid scores."""
    rotation_player_ids = set(request.rotation_order)

    for player_id in request.scores.keys():
        if player_id not in rotation_player_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Score provided for player {player_id} not in rotation order",
            )

    for player_id in rotation_player_ids:
        if player_id not in request.scores:
            raise HTTPException(
                status_code=400,
                detail=f"Missing score for player {player_id} in rotation",
            )

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


def validate_float_usage(request: CompleteHoleRequest, game_state: dict[str, Any]) -> None:
    """Validate Float usage — once per round per player (second check after game state loaded)."""
    if not request.float_invoked_by:
        return
    for player in game_state.get("players", []):
        if player["id"] == request.float_invoked_by:
            float_count = player.get("float_used", 0)
            if isinstance(float_count, bool):
                float_count = 0
            if float_count >= 1:
                raise HTTPException(
                    status_code=400,
                    detail=f"Player {request.float_invoked_by} has already used float this round",
                )
            break


def run_complete_hole_validations(
    request: CompleteHoleRequest,
    game_state: dict[str, Any],
) -> None:
    """Run all validations for the complete_hole endpoint."""
    player_count = len(request.rotation_order)

    validate_joes_special(request)
    validate_big_dick(request)
    validate_aardvark(request, player_count)
    validate_carry_over_hole_18(request, game_state)
    validate_float(request, game_state)
    validate_tunkarri_player_count(request, player_count)
    validate_team_formations(request)
    validate_scores(request)
    validate_float_usage(request, game_state)


def run_update_hole_validations(
    request: CompleteHoleRequest,
    hole_number: int,
) -> None:
    """Run validations for the update_hole endpoint (subset — no game-state-dependent checks)."""
    player_count = len(request.rotation_order)

    # Joe's Special
    if request.phase == "hoepfinger" and request.joes_special_wager:
        valid_wagers = [2, 4, 8]
        if request.joes_special_wager not in valid_wagers:
            raise HTTPException(
                status_code=400,
                detail=f"Joe's Special must be 2, 4, or 8 quarters. Got: {request.joes_special_wager}",
            )

    # Big Dick
    if request.big_dick_invoked_by and hole_number != 18:
        raise HTTPException(status_code=400, detail="The Big Dick can only be invoked on hole 18")

    # Team formations (simplified for update — same core checks)
    rotation_player_ids = set(request.rotation_order)
    all_team_players: list[str] = []

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

    # All rotation players on teams
    all_team_players_set = set(all_team_players)
    if all_team_players_set != rotation_player_ids:
        missing = rotation_player_ids - all_team_players_set
        extra = all_team_players_set - rotation_player_ids
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing from teams: {missing}")
        if extra:
            raise HTTPException(status_code=400, detail=f"Not in rotation: {extra}")

    # Scores
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


# ---------------------------------------------------------------------------
# Score Calculation
# ---------------------------------------------------------------------------


def apply_karl_marx(
    team_players: list[str],
    total_amount: float,
    game_state: dict[str, Any],
) -> dict[str, float]:
    """
    Distribute quarters unevenly according to Karl Marx rule.

    Player furthest down (Goat) gets smaller loss or larger win.
    """
    if len(team_players) == 0:
        return {}

    num_players = len(team_players)
    result: dict[str, float] = {}

    abs_total = abs(total_amount)
    is_loss = total_amount < 0

    if abs_total % num_players != 0:
        base_share = abs_total // num_players
        remainder = abs_total % num_players

        player_points: dict[str, float] = {}
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


def calculate_points_delta(
    request: CompleteHoleRequest,
    game_state: dict[str, Any],
) -> dict[str, float]:
    """Calculate quarters won/lost based on winner, wager, and team formation."""
    points_delta: dict[str, float] = {}

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
            points_delta[request.teams.captain] = total_payout  # Aardvark is "captain" in solo mode
            loss_per_opponent = total_payout / len(request.teams.opponents)  # type: ignore
            for opp_id in request.teams.opponents:  # type: ignore
                points_delta[opp_id] = -loss_per_opponent
        elif request.tunkarri_invoked and request.winner == "opponents":
            total_loss = request.final_wager * len(request.teams.opponents)  # type: ignore
            points_delta[request.teams.captain] = -total_loss  # Aardvark is "captain" in solo mode  # type: ignore
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

    return points_delta


def apply_multipliers(
    points_delta: dict[str, float],
    request: CompleteHoleRequest,
    hole_number: int,
) -> dict[str, float]:
    """Apply double points (holes 17-18), aardvark toss doubling, and manual override."""
    player_count = len(request.rotation_order)

    # Double points for holes 17-18 (except Hoepfinger which uses Joe's Special)
    if hole_number in [17, 18] and request.phase != "hoepfinger":
        for player_id in points_delta:
            points_delta[player_id] *= 2

    # Aardvark toss doubling (5-man games only)
    if player_count == 5 and request.aardvark_tossed and request.aardvark_requested_team:
        if request.teams.type == "partners":
            multiplier = 4 if request.aardvark_ping_ponged else 2
            for player_id in points_delta:
                points_delta[player_id] *= multiplier

    # Manual points override
    if request.manual_points_override:
        override = request.manual_points_override
        logger.info(f"Manual points override for player {override.player_id}: {override.quarters}")
        points_delta[override.player_id] = override.quarters

    return points_delta


def validate_points_balance(
    points_delta: dict[str, float],
    request: CompleteHoleRequest,
) -> None:
    """Verify points balance to zero (zero-sum game)."""
    points_total = sum(points_delta.values())
    if not request.manual_points_override and abs(points_total) > 0.01:
        logger.error(
            f"SCOREKEEPING ERROR: Points do not balance to zero! "
            f"Hole {request.hole_number}, Total: {points_total}, "
            f"Points: {points_delta}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Scorekeeping error: points total {points_total} instead of 0. Please report this bug.",
        )
    if request.manual_points_override and abs(points_total) > 0.01:
        logger.warning(
            f"Manual override used - points do not balance to zero. "
            f"Hole {request.hole_number}, Total: {points_total}, Points: {points_delta}"
        )


# ---------------------------------------------------------------------------
# Quarters Breakdown (for display)
# ---------------------------------------------------------------------------


def calculate_quarters_breakdown(
    points_delta: dict[str, float],
    request: CompleteHoleRequest,
) -> dict[str, dict[str, float]]:
    """Calculate per-opponent quarters breakdown for scorecard display."""
    quarters_breakdown: dict[str, dict[str, float]] = {}
    for player_id in points_delta:
        quarters_breakdown[player_id] = {}

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

        elif request.teams.type == "solo":
            if player_id == request.teams.captain:
                opponent_count = len(request.teams.opponents)  # type: ignore
                if opponent_count > 0:
                    quarters_per_opponent = points_delta[player_id] / opponent_count
                    for opp_id in request.teams.opponents:  # type: ignore
                        quarters_breakdown[player_id][opp_id] = quarters_per_opponent
            else:
                quarters_breakdown[player_id][request.teams.captain] = points_delta[player_id]

    return quarters_breakdown


# ---------------------------------------------------------------------------
# Hole Result Construction
# ---------------------------------------------------------------------------


def build_hole_result(
    request: CompleteHoleRequest,
    points_delta: dict[str, float],
    quarters_breakdown: dict[str, dict[str, float]],
    hole_number: int,
) -> dict[str, Any]:
    """Build the hole result dict that gets stored in hole_history."""
    player_count = len(request.rotation_order)
    return {
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
        "betting_narrative": request.betting_narrative,
        "betting_events": request.betting_events or [],
    }


# ---------------------------------------------------------------------------
# Game State Persistence
# ---------------------------------------------------------------------------


def update_hole_history(
    game_state: dict[str, Any],
    hole_result: dict[str, Any],
    hole_number: int,
) -> None:
    """Add or update a hole in the history."""
    if "hole_history" not in game_state:
        game_state["hole_history"] = []

    existing_hole_index = next(
        (i for i, h in enumerate(game_state["hole_history"]) if h.get("hole") == hole_number),
        None,
    )

    if existing_hole_index is not None:
        game_state["hole_history"][existing_hole_index] = hole_result
    else:
        game_state["hole_history"].append(hole_result)


def update_carry_over_state(
    game_state: dict[str, Any],
    request: CompleteHoleRequest,
) -> None:
    """Track carry-over state after a hole result."""
    if request.winner == "push":
        last_push_hole = game_state.get("last_push_hole")
        if last_push_hole == request.hole_number - 1:
            game_state["consecutive_push_block"] = True
            game_state["last_push_hole"] = request.hole_number
        else:
            game_state["carry_over_wager"] = request.final_wager * 2
            game_state["carry_over_from_hole"] = request.hole_number
            game_state["last_push_hole"] = request.hole_number
            game_state["consecutive_push_block"] = False
    else:
        game_state.pop("carry_over_wager", None)
        game_state.pop("carry_over_from_hole", None)
        game_state["consecutive_push_block"] = False


def update_player_totals(
    game_state: dict[str, Any],
    points_delta: dict[str, float],
    request: CompleteHoleRequest,
) -> None:
    """Update player points and float usage after a hole."""
    if "players" not in game_state:
        game_state["players"] = []

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

        if request.float_invoked_by == player_id:
            current_float_count = player.get("float_used", 0)
            if isinstance(current_float_count, bool):
                current_float_count = 0
            player["float_used"] = current_float_count + 1


def sync_simulation(
    game_id: str,
    game_state: dict[str, Any],
    request: CompleteHoleRequest,
) -> None:
    """Sync game state to in-memory simulation if present."""
    from ..services.game_lifecycle_service import get_game_lifecycle_service

    service = get_game_lifecycle_service()
    if game_id not in service._active_games:
        return

    simulation = service._active_games[game_id]
    simulation.carry_over_wager = game_state.get("carry_over_wager")  # type: ignore
    simulation.carry_over_from_hole = game_state.get("carry_over_from_hole")  # type: ignore
    simulation.consecutive_push_block = game_state.get("consecutive_push_block", False)  # type: ignore
    simulation.last_push_hole = game_state.get("last_push_hole")  # type: ignore
    simulation.base_wager = game_state.get("base_wager")  # type: ignore
    simulation.scorekeeper_hole_history = game_state.get("hole_history", [])  # type: ignore

    if request.float_invoked_by:
        float_player = next(
            (p for p in simulation.players if p.id == request.float_invoked_by),
            None,
        )
        if float_player:
            float_player.float_used += 1

    for db_player in game_state.get("players", []):
        sim_player = next((p for p in simulation.players if p.id == db_player["id"]), None)
        if sim_player:
            sim_player.points = db_player.get("points", 0)


def replay_player_totals(game_state: dict[str, Any]) -> None:
    """Reset and replay all player totals from hole_history (used after update/delete)."""
    for player in game_state.get("players", []):
        player["points"] = 0
        player["float_used"] = 0

    for hole in game_state.get("hole_history", []):
        hole_points_delta = hole.get("points_delta", {})
        for player in game_state.get("players", []):
            player_id = player.get("id")
            if player_id in hole_points_delta:
                player["points"] += hole_points_delta[player_id]
            if hole.get("float_invoked_by") == player_id:
                player["float_used"] += 1


# ---------------------------------------------------------------------------
# Orchestrator — called by the route handler
# ---------------------------------------------------------------------------


def process_complete_hole(
    request: CompleteHoleRequest,
    game_state: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Run all business logic for completing a hole.

    Returns (hole_result, updated game_state).
    """
    # Initialize hole_history
    if "hole_history" not in game_state:
        game_state["hole_history"] = []

    # Calculate points
    points_delta = calculate_points_delta(request, game_state)
    apply_multipliers(points_delta, request, request.hole_number)
    validate_points_balance(points_delta, request)

    # Build result
    quarters_breakdown = calculate_quarters_breakdown(points_delta, request)
    hole_result = build_hole_result(request, points_delta, quarters_breakdown, request.hole_number)

    # Update game state
    update_hole_history(game_state, hole_result, request.hole_number)
    update_carry_over_state(game_state, request)
    update_player_totals(game_state, points_delta, request)
    game_state["current_hole"] = request.hole_number + 1

    return hole_result, game_state


def process_update_hole(
    request: CompleteHoleRequest,
    game_state: dict[str, Any],
    hole_number: int,
    existing_hole_index: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Run all business logic for updating a hole.

    Returns (hole_result, updated game_state).
    """
    # Calculate points
    points_delta = calculate_points_delta(request, game_state)
    apply_multipliers(points_delta, request, hole_number)

    # Manual override
    if request.manual_points_override:
        override = request.manual_points_override
        logger.info(f"Manual points override for player {override.player_id}: {override.quarters}")
        points_delta[override.player_id] = override.quarters

    # Build result
    quarters_breakdown = calculate_quarters_breakdown(points_delta, request)
    hole_result = build_hole_result(request, points_delta, quarters_breakdown, hole_number)

    # Update hole in history
    game_state["hole_history"][existing_hole_index] = hole_result

    # Replay all totals from scratch
    replay_player_totals(game_state)

    return hole_result, game_state
