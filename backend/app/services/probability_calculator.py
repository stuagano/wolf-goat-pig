from typing import Dict, Any, Optional
from ..game_state import GameState

def _require_key(obj, key, context):
    if key not in obj:
        raise KeyError(f"Missing key '{key}' in {context}")
    return obj[key]

class ProbabilityCalculator:
    @staticmethod
    def calculate_tee_shot_probabilities(player: dict, game_state: GameState) -> dict:
        # Handle both Player objects and dictionaries
        if hasattr(player, 'handicap'):
            handicap = player.handicap
        else:
            handicap = player["handicap"]
        
        hole_info = ProbabilityCalculator._get_hole_info(game_state)
        base_excellent = max(0.05, 0.25 - (handicap * 0.01))
        base_good = max(0.15, 0.35 - (handicap * 0.008))
        base_average = 0.35
        base_poor = max(0.10, 0.15 + (handicap * 0.005))
        base_terrible = max(0.05, 0.10 + (handicap * 0.003))
        stroke_index = hole_info.get("stroke_index", 10)
        difficulty_factor = (19 - stroke_index) / 18.0
        excellent = base_excellent * (1 - difficulty_factor * 0.3)
        good = base_good * (1 - difficulty_factor * 0.2)
        average = base_average
        poor = base_poor * (1 + difficulty_factor * 0.4)
        terrible = base_terrible * (1 + difficulty_factor * 0.6)
        total = excellent + good + average + poor + terrible
        return {
            "excellent": round(excellent / total * 100, 1),
            "good": round(good / total * 100, 1),
            "average": round(average / total * 100, 1),
            "poor": round(poor / total * 100, 1),
            "terrible": round(terrible / total * 100, 1),
            "expected_distance": ProbabilityCalculator._calculate_expected_distance(handicap, hole_info),
            "handicap_factor": f"Handicap {handicap}: {'Low' if handicap <= 5 else 'Mid' if handicap <= 15 else 'High'} skill level",
            "hole_difficulty": f"Stroke Index {stroke_index}: {'Hard' if stroke_index <= 6 else 'Medium' if stroke_index <= 12 else 'Easy'} hole"
        }

    @staticmethod
    def calculate_post_shot_probabilities(shot_result, game_state: GameState) -> dict:
        if hasattr(shot_result, 'shot_quality'):
            shot_quality = shot_result.shot_quality
            remaining = shot_result.remaining
            lie = shot_result.lie
        else:
            shot_quality = _require_key(shot_result, "shot_quality", "shot_result")
            remaining = _require_key(shot_result, "remaining", "shot_result")
            lie = _require_key(shot_result, "lie", "shot_result")
        scoring_probs = ProbabilityCalculator.calculate_scoring_probabilities(remaining, lie, game_state)
        partnership_value = ProbabilityCalculator._calculate_partnership_value(shot_result, game_state)
        return {
            "scoring_probabilities": scoring_probs,
            "partnership_value": partnership_value,
            "position_quality": ProbabilityCalculator._assess_position_quality(shot_result),
            "strategic_implications": ProbabilityCalculator._get_strategic_implications(shot_result, game_state)
        }

    @staticmethod
    def calculate_scoring_probabilities(remaining_yards: int, lie: str, game_state: GameState) -> dict:
        par = ProbabilityCalculator._get_hole_info(game_state).get("par", 4)
        if remaining_yards <= 100:
            if lie == "fairway":
                birdie, par_score, bogey, double_bogey = 0.15, 0.55, 0.25, 0.05
            elif lie in ["first cut", "rough"]:
                birdie, par_score, bogey, double_bogey = 0.08, 0.45, 0.35, 0.12
            else:
                birdie, par_score, bogey, double_bogey = 0.02, 0.25, 0.45, 0.28
        elif remaining_yards <= 150:
            if lie == "fairway":
                birdie, par_score, bogey, double_bogey = 0.10, 0.45, 0.35, 0.10
            elif lie in ["first cut", "rough"]:
                birdie, par_score, bogey, double_bogey = 0.05, 0.35, 0.45, 0.15
            else:
                birdie, par_score, bogey, double_bogey = 0.01, 0.20, 0.50, 0.29
        else:
            if lie == "fairway":
                birdie, par_score, bogey, double_bogey = 0.05, 0.35, 0.45, 0.15
            elif lie in ["first cut", "rough"]:
                birdie, par_score, bogey, double_bogey = 0.02, 0.25, 0.50, 0.23
            else:
                birdie, par_score, bogey, double_bogey = 0.01, 0.15, 0.55, 0.29
        return {
            "birdie": round(birdie * 100, 1),
            "par": round(par_score * 100, 1),
            "bogey": round(bogey * 100, 1),
            "double_bogey_or_worse": round(double_bogey * 100, 1),
            "expected_score": round(par - birdie + bogey + 2*double_bogey, 2)
        }

    @staticmethod
    def calculate_betting_probabilities(game_state: GameState, decision: dict) -> dict:
        # This method should call out to the appropriate partnership/solo logic in SimulationEngine for now
        # For now, just return an empty dict as a placeholder
        # The full extraction of partnership/solo logic will be done in the next refactor step
        return {}

    # --- Helper methods ---
    @staticmethod
    def _get_hole_info(game_state: GameState) -> dict:
        hole_idx = game_state.current_hole - 1
        return {
            "hole_number": game_state.current_hole,
            "par": game_state.hole_pars[hole_idx] if game_state.hole_pars else 4,
            "yards": game_state.hole_yards[hole_idx] if hasattr(game_state, 'hole_yards') and game_state.hole_yards else 400,
            "stroke_index": game_state.hole_stroke_indexes[hole_idx] if game_state.hole_stroke_indexes else 10,
            "description": game_state.hole_descriptions[hole_idx] if hasattr(game_state, 'hole_descriptions') and game_state.hole_descriptions else ""
        }

    @staticmethod
    def _calculate_expected_distance(handicap: float, hole_info: dict) -> dict:
        base_distance = 260 - (handicap * 4)
        min_distance = int(base_distance * 0.8)
        max_distance = int(base_distance * 1.2)
        return {
            "expected": int(base_distance),
            "range": f"{min_distance}-{max_distance} yards",
            "percentile_25": int(base_distance * 0.9),
            "percentile_75": int(base_distance * 1.1)
        }

    @staticmethod
    def _calculate_partnership_value(shot_result, game_state: GameState) -> dict:
        if hasattr(shot_result, 'shot_quality'):
            shot_quality = shot_result.shot_quality
            remaining = shot_result.remaining
        else:
            shot_quality = shot_result["shot_quality"]
            remaining = shot_result["remaining"]
        if shot_quality == "excellent":
            base_value = 85
        elif shot_quality == "good":
            base_value = 70
        elif shot_quality == "average":
            base_value = 50
        elif shot_quality == "poor":
            base_value = 30
        else:
            base_value = 15
        if remaining <= 100:
            position_bonus = 15
        elif remaining <= 150:
            position_bonus = 10
        else:
            position_bonus = 0
        return {
            "partnership_appeal": min(100, base_value + position_bonus),
            "reason": f"{shot_quality} shot, {remaining} yards remaining",
            "strategic_value": "High" if base_value >= 70 else "Medium" if base_value >= 50 else "Low"
        }

    @staticmethod
    def _assess_position_quality(shot_result: dict) -> dict:
        lie = shot_result["lie"]
        remaining = shot_result["remaining"]
        if lie == "fairway":
            if remaining <= 100:
                quality = "Excellent - Short iron to green"
                score = 90
            elif remaining <= 150:
                quality = "Good - Mid iron opportunity"
                score = 75
            else:
                quality = "Fair - Long approach needed"
                score = 60
        elif lie in ["first cut", "rough"]:
            if remaining <= 120:
                quality = "Good - Manageable from rough"
                score = 65
            else:
                quality = "Challenging - Long shot from rough"
                score = 45
        else:
            quality = "Difficult - Recovery shot needed"
            score = 25
        return {
            "quality_score": score,
            "description": quality,
            "lie_type": lie,
            "distance_category": "Short" if remaining <= 100 else "Medium" if remaining <= 150 else "Long"
        }

    @staticmethod
    def _get_strategic_implications(shot_result: dict, game_state: GameState) -> list:
        implications = []
        # Placeholder for strategic advice logic
        return implications 