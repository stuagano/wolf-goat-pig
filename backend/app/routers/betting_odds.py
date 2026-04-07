"""Betting odds and shot-range analysis routes."""

import logging
import time
import traceback
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

from ..domain.shot_range_analysis import analyze_shot_decision

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wgp", tags=["betting"])


# ---------------------------------------------------------------------------
# Pydantic models (only used by routes in this file)
# ---------------------------------------------------------------------------


class ShotRangeAnalysisRequest(BaseModel):
    """Request model for shot range analysis"""

    lie_type: str = Field(..., description="Current lie (fairway, rough, bunker, etc)")
    distance_to_pin: float = Field(..., description="Distance to pin in yards")
    player_handicap: float = Field(..., description="Player's handicap")
    hole_number: int = Field(..., description="Current hole number")
    team_situation: str = Field(default="solo", description="Team situation (solo, partners)")
    score_differential: int = Field(default=0, description="Current score differential")
    opponent_styles: list[str] = Field(default=[], description="Opponent playing styles")


class OddsCalculationRequest(BaseModel):
    """Request model for odds calculation"""

    players: list[dict[str, Any]] = Field(..., description="Current player states")
    hole_state: dict[str, Any] = Field(..., description="Current hole state")
    use_monte_carlo: bool = Field(default=False, description="Use Monte Carlo simulation for higher accuracy")
    simulation_params: dict[str, Any] | None = Field(default=None, description="Monte Carlo simulation parameters")


class BettingScenarioResponse(BaseModel):
    """Response model for betting scenarios"""

    scenario_type: str
    win_probability: float
    expected_value: float
    risk_level: str
    confidence_interval: tuple[float, float]
    recommendation: str
    reasoning: str
    payout_matrix: dict[str, float]


class OddsCalculationResponse(BaseModel):
    """Response model for odds calculation"""

    timestamp: float
    calculation_time_ms: float
    player_probabilities: dict[str, dict[str, Any]]
    team_probabilities: dict[str, float]
    betting_scenarios: list[dict[str, Any]]
    optimal_strategy: str
    risk_assessment: dict[str, Any]
    educational_insights: list[str]
    confidence_level: float
    monte_carlo_used: bool = False
    simulation_details: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _normalize_probabilities(probabilities: dict[str, float]) -> dict[str, float]:
    """Normalize probability buckets so they sum to ~1.0 and clamp negatives."""
    safe_probs = {k: max(0.0, float(v)) for k, v in probabilities.items()}
    total = sum(safe_probs.values())
    if total <= 0:
        bucket_count = len(safe_probs)
        if bucket_count == 0:
            return {}
        equal_share = 1.0 / bucket_count
        return dict.fromkeys(safe_probs, equal_share)
    return {k: v / total for k, v in safe_probs.items()}


def _compute_shot_probabilities(
    player_stats: dict[str, Any] | None = None,
    hole_info: dict[str, Any] | None = None,
    lie_type: str | None = None,
) -> dict[str, float]:
    """Generate a balanced shot probability distribution based on context."""
    player_stats = player_stats or {}
    hole_info = hole_info or {}
    lie_type = (lie_type or hole_info.get("lie_type") or "").lower()

    base_distribution = {
        "excellent": 0.18,
        "good": 0.32,
        "average": 0.30,
        "poor": 0.15,
        "disaster": 0.05,
    }

    handicap = float(player_stats.get("handicap", 18) or 18)
    skill_delta = max(min((18 - handicap) / 40.0, 0.2), -0.2)
    base_distribution["excellent"] += skill_delta
    base_distribution["good"] += skill_delta * 0.5
    base_distribution["poor"] -= abs(skill_delta) * 0.4
    base_distribution["disaster"] = max(0.02, base_distribution["disaster"] - skill_delta * 0.3)

    difficulty = str(hole_info.get("difficulty", "medium")).lower()
    if difficulty in {"hard", "very hard", "difficult"}:
        base_distribution["excellent"] *= 0.75
        base_distribution["good"] *= 0.85
        base_distribution["poor"] *= 1.2
        base_distribution["disaster"] *= 1.3
    elif difficulty in {"easy", "very easy"}:
        base_distribution["excellent"] *= 1.15
        base_distribution["good"] *= 1.05
        base_distribution["poor"] *= 0.85
        base_distribution["disaster"] *= 0.75

    distance = hole_info.get("distance") or hole_info.get("distance_to_pin")
    if isinstance(distance, (int, float)):
        if distance < 100:
            base_distribution["excellent"] *= 1.1
            base_distribution["good"] *= 1.05
            base_distribution["poor"] *= 0.9
        elif distance > 200:
            base_distribution["excellent"] *= 0.85
            base_distribution["good"] *= 0.9
            base_distribution["poor"] *= 1.1
            base_distribution["disaster"] *= 1.15

    if lie_type in {"tee"}:
        base_distribution["excellent"] *= 1.2
        base_distribution["good"] *= 1.1
        base_distribution["poor"] *= 0.8
        base_distribution["disaster"] *= 0.6
    elif lie_type in {"rough", "deep_rough"}:
        base_distribution["excellent"] *= 0.7
        base_distribution["good"] *= 0.8
        base_distribution["poor"] *= 1.2
        base_distribution["disaster"] *= 1.3
    elif lie_type in {"bunker"}:
        base_distribution["excellent"] *= 0.6
        base_distribution["good"] *= 0.75
        base_distribution["poor"] *= 1.25
        base_distribution["disaster"] *= 1.4
    elif lie_type in {"green"}:
        base_distribution["excellent"] *= 1.4
        base_distribution["good"] *= 1.15
        base_distribution["poor"] *= 0.6
        base_distribution["disaster"] *= 0.4

    return _normalize_probabilities(base_distribution)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/shot-range-analysis")
async def get_shot_range_analysis(request: ShotRangeAnalysisRequest) -> dict[str, Any]:
    """Get poker-style shot range analysis for decision making"""
    try:
        # Perform shot range analysis
        analysis = analyze_shot_decision(
            current_lie=request.lie_type,
            distance=request.distance_to_pin,
            player_handicap=request.player_handicap,
            hole_number=request.hole_number,
            team_situation=request.team_situation,
            score_differential=request.score_differential,
            opponent_styles=request.opponent_styles,
        )

        return {
            "status": "success",
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in shot range analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze shot range: {e!s}")


@router.post("/calculate-odds", response_model=OddsCalculationResponse)
async def calculate_real_time_odds(request: OddsCalculationRequest) -> dict[str, Any]:
    """
    Calculate real-time betting odds and probabilities.
    Provides comprehensive analysis for strategic decision making.
    """
    try:
        from ..services.monte_carlo import SimulationParams, run_monte_carlo_simulation
        from ..services.odds_calculator import (
            OddsCalculator,
            create_hole_state_from_game_data,
            create_player_state_from_game_data,
        )

        start_time = time.time()

        # Convert request data to internal objects
        player_states = [create_player_state_from_game_data(p) for p in request.players]
        hole_state = create_hole_state_from_game_data(request.hole_state)

        # Initialize odds calculator
        calculator = OddsCalculator()

        # Determine if we should use Monte Carlo
        use_mc = request.use_monte_carlo
        if not use_mc:
            # Auto-enable Monte Carlo for complex scenarios
            complex_scenario = (
                len(player_states) > 4
                or hole_state.teams.value != "pending"
                or any(p.distance_to_pin > 200 for p in player_states)
            )
            use_mc = complex_scenario

        simulation_details = None
        if use_mc:
            # Run Monte Carlo simulation
            mc_params = SimulationParams()
            if request.simulation_params:
                mc_params.num_simulations = request.simulation_params.get("num_simulations", 5000)
                mc_params.max_simulation_time_ms = request.simulation_params.get("max_time_ms", 25.0)

            simulation_result = run_monte_carlo_simulation(
                player_states,
                hole_state,
                mc_params.num_simulations,
                mc_params.max_simulation_time_ms,
            )

            simulation_details = {
                "num_simulations_run": simulation_result.num_simulations_run,
                "simulation_time_ms": simulation_result.simulation_time_ms,
                "convergence_achieved": simulation_result.convergence_achieved,
                "confidence_intervals": simulation_result.confidence_intervals,
            }

            # Enhance calculator with Monte Carlo results
            # This would integrate MC results into the main calculation

        # Calculate comprehensive odds
        odds_result = calculator.calculate_real_time_odds(
            player_states,
            hole_state,
            game_context={"monte_carlo_result": simulation_details if use_mc else None},
        )

        # Convert betting scenarios to response format
        betting_scenarios = []
        for scenario in odds_result.betting_scenarios:
            betting_scenarios.append(
                {
                    "scenario_type": scenario.scenario_type,
                    "win_probability": scenario.win_probability,
                    "expected_value": scenario.expected_value,
                    "risk_level": scenario.risk_level,
                    "confidence_interval": scenario.confidence_interval,
                    "recommendation": scenario.recommendation,
                    "reasoning": scenario.reasoning,
                    "payout_matrix": scenario.payout_matrix,
                }
            )

        total_time = (time.time() - start_time) * 1000

        return OddsCalculationResponse(
            timestamp=odds_result.timestamp,
            calculation_time_ms=total_time,
            player_probabilities=odds_result.player_probabilities,
            team_probabilities=odds_result.team_probabilities,
            betting_scenarios=betting_scenarios,
            optimal_strategy=odds_result.optimal_strategy,
            risk_assessment=odds_result.risk_assessment,
            educational_insights=odds_result.educational_insights,
            confidence_level=odds_result.confidence_level,
            monte_carlo_used=use_mc,
            simulation_details=simulation_details,
        )

    except Exception as e:
        logger.error(f"Error calculating odds: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to calculate odds: {e!s}")


@router.get("/betting-opportunities")
async def get_current_betting_opportunities():
    """
    Get current betting opportunities based on game state.
    Lightweight endpoint for real-time updates.
    """
    try:
        # game global lives in domain handler module
        from ..domain.wgp_handlers_core import game

        from ..managers.rule_manager import RuleManager, RuleViolationError

        # Get current game state
        current_state = game.get_game_state()  # type: ignore

        # Quick opportunity assessment
        opportunities = []

        # Check if game is active
        if not current_state.get("active", False):
            return {"opportunities": [], "message": "No active game"}

        current_hole = current_state.get("current_hole", 1)
        hole_state = game.hole_states.get(current_hole)  # type: ignore

        if hole_state:
            # REFACTORED: Using RuleManager for betting opportunities
            # Check for doubling opportunities
            rule_mgr = RuleManager.get_instance()

            # Check if any player can double
            can_any_player_double = False
            for player in game.players:  # type: ignore
                if rule_mgr.can_double(player.id, current_state):
                    can_any_player_double = True
                    break

            if can_any_player_double and hole_state.teams.type != "pending":
                opportunities.append(
                    {
                        "type": "offer_double",
                        "description": f"Double the wager from {hole_state.betting.current_wager} to {hole_state.betting.current_wager * 2} quarters",
                        "current_wager": hole_state.betting.current_wager,
                        "potential_wager": hole_state.betting.current_wager * 2,
                        "risk_level": "medium",
                        "timing": ("optimal" if not hole_state.wagering_closed else "limited"),
                    }
                )

            # REFACTORED: Using RuleManager for partnership opportunities
            # Check for partnership opportunities
            if hole_state.teams.type == "pending":
                captain_id = hole_state.teams.captain
                captain_name = game._get_player_name(captain_id)  # type: ignore

                available_partners = []
                for player in game.players:  # type: ignore
                    # Use both hole state and RuleManager for validation
                    if player.id != captain_id and hole_state.can_request_partnership(captain_id, player.id):  # type: ignore
                        try:
                            if rule_mgr.can_form_partnership(captain_id, player.id, current_state):  # type: ignore
                                available_partners.append(
                                    {
                                        "id": player.id,
                                        "name": player.name,
                                        "handicap": player.handicap,
                                    }
                                )
                        except RuleViolationError:
                            # Partnership not allowed
                            pass

                if available_partners:
                    opportunities.append(
                        {
                            "type": "partnership_decision",
                            "description": f"{captain_name} must choose a partner or go solo",
                            "captain": captain_name,
                            "available_partners": available_partners,
                            "solo_multiplier": 2,
                            "deadline_approaching": len(available_partners) < len(game.players) - 1,  # type: ignore
                        }
                    )

        return {
            "opportunities": opportunities,
            "hole_number": current_hole,
            "timestamp": datetime.now().isoformat(),
            "game_active": current_state.get("active", False),
        }

    except Exception as e:
        logger.error(f"Error getting betting opportunities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get betting opportunities: {e!s}")


@router.post("/quick-odds")
async def calculate_quick_odds(
    players_data: list[dict[str, Any]] = Body(...),
) -> dict[str, Any]:
    """
    Quick odds calculation for immediate feedback.
    Optimized for sub-50ms response time.
    """
    try:
        from ..services.odds_calculator import HoleState, OddsCalculator, PlayerState, TeamConfiguration

        start_time = time.time()

        # Simple validation
        if len(players_data) < 2:
            raise HTTPException(status_code=400, detail="At least 2 players required")

        # Create simplified player states
        players = []
        for i, p_data in enumerate(players_data):
            player = PlayerState(
                id=p_data.get("id", f"p{i}"),
                name=p_data.get("name", f"Player {i + 1}"),
                handicap=float(p_data.get("handicap", 18)),
                distance_to_pin=float(p_data.get("distance_to_pin", 150)),
                lie_type=p_data.get("lie_type", "fairway"),
            )
            players.append(player)

        # Create basic hole state
        hole = HoleState(hole_number=1, par=4, teams=TeamConfiguration.PENDING)

        # Quick calculation
        calculator = OddsCalculator()

        # Calculate win probabilities only
        quick_probs = {}
        for player in players:
            win_prob = calculator._calculate_player_win_vs_field(player, players, hole)
            quick_probs[player.id] = {
                "name": player.name,
                "win_probability": win_prob,
                "handicap": player.handicap,
                "distance": player.distance_to_pin,
            }

        calculation_time = (time.time() - start_time) * 1000

        return {
            "probabilities": quick_probs,
            "calculation_time_ms": calculation_time,
            "method": "quick_analytical",
            "timestamp": time.time(),
        }

    except Exception as e:
        logger.error(f"Error in quick odds calculation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate quick odds: {e!s}")


@router.get("/odds-history/{game_id}")
async def get_odds_history(game_id: str, hole_number: int | None = None) -> dict[str, Any]:
    """
    Get historical odds data for analysis and trends.
    """
    try:
        # This would typically query a database for historical odds
        # For now, return mock data structure

        history_data = {
            "game_id": game_id,
            "holes": {},
            "trends": {
                "volatility_by_hole": {},
                "betting_patterns": {},
                "accuracy_metrics": {},
            },
        }

        # If specific hole requested
        if hole_number:
            history_data["holes"][str(hole_number)] = {  # type: ignore
                "initial_odds": {},
                "final_odds": {},
                "betting_actions": [],
                "outcome": {},
            }

        return history_data

    except Exception as e:
        logger.error(f"Error getting odds history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get odds history: {e!s}")
