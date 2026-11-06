"""Betting odds and shot-range analysis routes."""

import logging
import time
import traceback
from typing import Any

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

from ..domain.shot_range_analysis import analyze_shot_decision
from ..utils.time import utc_now

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
    monte_carlo_used: bool = False  # Deprecated, always False
    simulation_details: dict[str, Any] | None = None  # Deprecated, always None


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
            "timestamp": utc_now().isoformat(),
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
        from ..services.odds_calculator import (
            OddsCalculator,
            create_hole_state_from_game_data,
            create_player_state_from_game_data,
        )

        start_time = time.time()

        player_states = [create_player_state_from_game_data(p) for p in request.players]
        hole_state = create_hole_state_from_game_data(request.hole_state)

        calculator = OddsCalculator()

        odds_result = calculator.calculate_real_time_odds(
            player_states,
            hole_state,
            game_context={},
        )

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
            monte_carlo_used=False,
            simulation_details=None,
        )

    except Exception as e:
        logger.error(f"Error calculating odds: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to calculate odds: {e!s}")


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
