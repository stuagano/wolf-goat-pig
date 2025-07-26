import random
from typing import List, Dict, Any, Optional
from backend.app.domain.player import Player
from backend.app.domain.shot_result import ShotResult
from backend.app.game_state import GameState

class ShotSimulator:
    @staticmethod
    def simulate_individual_tee_shot(player: dict, game_state: GameState) -> ShotResult:
        """Simulate tee shot for a single player and return a ShotResult object"""
        if isinstance(player, dict):
            player_obj = Player.from_dict(player)
        else:
            player_obj = player
        player_id = player_obj.id
        handicap = player_obj.handicap
        hole_idx = game_state.current_hole - 1
        par = game_state.hole_pars[hole_idx] if game_state.hole_pars else 4
        yards = game_state.hole_yards[hole_idx] if hasattr(game_state, 'hole_yards') and game_state.hole_yards else 400
        if handicap <= 5:
            drive = int(random.gauss(265, 12))
        elif handicap <= 12:
            drive = int(random.gauss(245, 15))
        elif handicap <= 20:
            drive = int(random.gauss(225, 18))
        else:
            drive = int(random.gauss(200, 20))
        drive = max(100, min(drive, yards - 30))
        shot_quality = random.choices(
            ["excellent", "good", "average", "poor", "terrible"],
            weights=[0.12, 0.38, 0.32, 0.15, 0.03], k=1
        )[0]
        if shot_quality == "excellent":
            lie = "fairway"
            penalty = 0
        elif shot_quality == "good":
            lie = random.choice(["fairway", "first cut"])
            penalty = 0
        elif shot_quality == "average":
            lie = random.choice(["fairway", "rough"])
            penalty = 0
        elif shot_quality == "poor":
            lie = random.choice(["rough", "bunker"])
            penalty = 0
        else:
            lie = random.choice(["trees", "hazard", "deep rough"])
            penalty = random.randint(1, 2)
        remaining = max(30, yards - drive + penalty * 20)
        return ShotResult(
            player=player_obj,
            drive=drive,
            lie=lie,
            remaining=remaining,
            shot_quality=shot_quality,
            penalty=penalty,
            hole_number=game_state.current_hole
        )

    @staticmethod
    def simulate_remaining_shots(game_state: GameState, tee_shot_results: dict) -> List[str]:
        feedback = []
        hole_par = game_state.hole_pars[game_state.current_hole - 1] if game_state.hole_pars else 4
        scores = {}
        shot_details = {}
        for player in game_state.player_manager.players:
            player_id = player["id"]
            handicap = player["handicap"]
            strokes = game_state.get_player_strokes()
            net_strokes = strokes[player_id][game_state.current_hole]
            tee_result = tee_shot_results.get(player_id)
            if tee_result and hasattr(tee_result, 'shot_quality'):
                tee_quality = tee_result.shot_quality
                remaining_distance = tee_result.remaining
            elif tee_result:
                tee_quality = tee_result.get("shot_quality", "average")
                remaining_distance = tee_result.get("remaining", 150)
            else:
                tee_quality = "average"
                remaining_distance = 150
            gross_score = ShotSimulator.simulate_player_final_score(handicap, hole_par, game_state.current_hole, game_state, tee_quality, remaining_distance)
            net_score = max(1, gross_score - net_strokes)
            scores[player_id] = int(net_score)
            shot_details[player_id] = {
                "gross": gross_score,
                "net": net_score,
                "strokes_received": net_strokes,
                "tee_quality": tee_quality
            }
            game_state.dispatch_action("record_net_score", {
                "player_id": player_id,
                "score": int(net_score)
            })
        for player in game_state.player_manager.players:
            player_id = player["id"]
            details = shot_details[player_id]
            if player_id == ShotSimulator._get_human_player_id(game_state):
                feedback.append(f"🧑 **Your final score:** {details['gross']} gross, {details['net']} net (received {details['strokes_received']} strokes)")
            else:
                feedback.append(f"💻 **{player['name']}:** {details['gross']} gross, {details['net']} net (received {details['strokes_received']} strokes)")
        return feedback

    @staticmethod
    def simulate_remaining_shots_chronological(game_state: GameState, tee_shot_results: dict) -> List[str]:
        # This is nearly identical to simulate_remaining_shots, but kept for compatibility
        return ShotSimulator.simulate_remaining_shots(game_state, tee_shot_results)

    @staticmethod
    def simulate_player_final_score(handicap: float, par: int, hole_number: int, game_state: 'GameState' = None, tee_quality: str = "average", remaining_distance: float = 150) -> int:
        base_score = ShotSimulator.simulate_player_score(handicap, par, hole_number, game_state)
        if tee_quality == "excellent":
            adjustment = -0.3
        elif tee_quality == "good":
            adjustment = -0.1
        elif tee_quality == "average":
            adjustment = 0
        elif tee_quality == "poor":
            adjustment = 0.2
        else:
            adjustment = 0.5
        if remaining_distance > 200:
            adjustment += 0.3
        elif remaining_distance > 150:
            adjustment += 0.1
        elif remaining_distance < 100:
            adjustment -= 0.1
        if random.random() < abs(adjustment):
            if adjustment > 0:
                base_score += 1
            else:
                base_score = max(1, base_score - 1)
        return base_score

    @staticmethod
    def simulate_player_score(handicap: float, par: int, hole_number: int, game_state: 'GameState' = None) -> int:
        # Simple model: lower handicap = lower expected score
        base = par
        if handicap <= 5:
            base += random.choice([-1, 0, 0, 1])
        elif handicap <= 12:
            base += random.choice([0, 0, 1, 1])
        elif handicap <= 20:
            base += random.choice([0, 1, 1, 2])
        else:
            base += random.choice([1, 2, 2, 3])
        # Add some hole-specific randomness
        if game_state and hasattr(game_state, 'hole_difficulty'):
            base += int(game_state.hole_difficulty.get(hole_number, 0))
        return max(1, base)

    @staticmethod
    def _get_human_player_id(game_state: GameState) -> str:
        # Utility to get the human player id
        for player in game_state.player_manager.players:
            if player.get("is_human", False):
                return player["id"]
        # Fallback: assume first player is human
        return game_state.player_manager.players[0]["id"] 