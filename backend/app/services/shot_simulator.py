import random
from typing import List, Dict, Any, Optional
from ..domain.player import Player
from ..domain.shot_result import ShotResult
from ..game_state import GameState

class ShotSimulator:
    @staticmethod
    def simulate_individual_tee_shot(player: Player, game_state: GameState) -> ShotResult:
        """Simulate tee shot for a single player and return a ShotResult object"""
        # Always expect Player objects - no more dictionary handling
        player_id = player.id
        handicap = player.handicap
        
        # Get hole information from course manager
        hole_idx = game_state.current_hole - 1
        par = game_state.course_manager.hole_pars[hole_idx] if game_state.course_manager.hole_pars else 4
        yards = game_state.course_manager.hole_yards[hole_idx] if game_state.course_manager.hole_yards else 400
        
        # Calculate drive distance based on player's expected drive distance
        expected_drive = player.get_expected_drive_distance()
        drive = int(random.gauss(expected_drive, expected_drive * 0.05))  # 5% standard deviation
        drive = max(100, min(drive, yards - 30))
        
        # Use player's shot quality weights for more realistic simulation
        shot_quality_weights = player.get_shot_quality_weights()
        shot_quality = random.choices(
            ["excellent", "good", "average", "poor", "terrible"],
            weights=shot_quality_weights, k=1
        )[0]
        
        # Determine lie and penalty based on shot quality
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
            player=player,
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
        hole_par = game_state.course_manager.hole_pars[game_state.current_hole - 1] if game_state.course_manager.hole_pars else 4
        scores = {}
        shot_details = {}
        
        # Always work with Player objects from player_manager
        for player in game_state.player_manager.players:
            player_id = player.id
            handicap = player.handicap
            
            strokes = game_state.get_player_strokes()
            net_strokes = strokes[player_id][game_state.current_hole]
            tee_result = tee_shot_results.get(player_id)
            
            # Handle ShotResult objects properly
            if tee_result and hasattr(tee_result, 'shot_quality'):
                tee_quality = tee_result.shot_quality
                remaining_distance = tee_result.remaining
            elif tee_result and isinstance(tee_result, dict):
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
        
        # Generate feedback using Player objects
        for player in game_state.player_manager.players:
            player_id = player.id
            player_name = player.name
            details = shot_details[player_id]
            
            if player_id == ShotSimulator._get_human_player_id(game_state):
                feedback.append(f"🧑 **Your final score:** {details['gross']} gross, {details['net']} net (received {details['strokes_received']} strokes)")
            else:
                feedback.append(f"💻 **{player_name}:** {details['gross']} gross, {details['net']} net (received {details['strokes_received']} strokes)")
        
        return feedback

    @staticmethod
    def simulate_approach_shot(player: Player, distance: int, game_state: GameState) -> ShotResult:
        """Simulate approach shot for a player and return a ShotResult object"""
        # Always expect Player objects
        handicap = player.handicap
        
        # Calculate shot distance based on player's ability and remaining distance
        if distance <= 50:  # Pitching/chipping
            base_distance = distance * 0.8  # 80% of target distance
        elif distance <= 150:  # Short iron
            base_distance = distance * 0.85
        else:  # Long iron/hybrid
            base_distance = distance * 0.9
        
        # Add variance based on handicap
        variance = handicap * 0.1  # Higher handicap = more variance
        actual_distance = int(random.gauss(base_distance, variance))
        
        # Determine shot quality based on player's ability
        shot_quality_weights = player.get_shot_quality_weights()
        shot_quality = random.choices(
            ["excellent", "good", "average", "poor", "terrible"],
            weights=shot_quality_weights, k=1
        )[0]
        
        # Calculate remaining distance and lie
        remaining = max(0, distance - actual_distance)
        
        if shot_quality == "excellent":
            lie = "green" if remaining <= 5 else "fairway"
            penalty = 0
        elif shot_quality == "good":
            lie = "green" if remaining <= 10 else "fairway"
            penalty = 0
        elif shot_quality == "average":
            lie = "fairway" if remaining <= 15 else "rough"
            penalty = 0
        elif shot_quality == "poor":
            lie = "rough" if remaining <= 20 else "bunker"
            penalty = 0
        else:
            lie = "bunker" if remaining <= 25 else "deep rough"
            penalty = random.randint(0, 1)
        
        return ShotResult(
            player=player,
            drive=actual_distance,
            lie=lie,
            remaining=remaining,
            shot_quality=shot_quality,
            penalty=penalty,
            hole_number=game_state.current_hole
        )

    @staticmethod
    def simulate_remaining_shots_chronological(game_state: GameState, tee_shot_results: dict) -> List[str]:
        """Simulate the remaining shots chronologically based on where tee shots landed"""
        feedback = []
        
        # Get hole information
        hole_idx = game_state.current_hole - 1
        par = game_state.course_manager.hole_pars[hole_idx] if game_state.course_manager.hole_pars else 4
        yards = game_state.course_manager.hole_yards[hole_idx] if game_state.course_manager.hole_yards else 400
        
        feedback.append("🎯 **APPROACH SHOTS & PUTTING**")
        
        # Track each player's position and score
        player_positions = {}
        player_scores = {}
        
        # Initialize positions based on tee shot results
        for player in game_state.player_manager.players:
            player_id = player.id
            tee_result = tee_shot_results.get(player_id)
            
            if tee_result and hasattr(tee_result, 'remaining'):
                remaining_distance = tee_result.remaining
                lie = tee_result.lie
                penalty = tee_result.penalty
            else:
                remaining_distance = yards * 0.6  # Default to 60% of hole
                lie = "fairway"
                penalty = 0
            
            player_positions[player_id] = {
                "distance_to_pin": remaining_distance,
                "lie": lie,
                "penalty": penalty,
                "shots_taken": 1,  # Already took tee shot
                "on_green": False
            }
            player_scores[player_id] = 1  # Start with 1 (tee shot)
        
        # Simulate approach shots and putting until all players complete the hole
        max_shots = par + 4  # Prevent infinite loops
        shot_number = 2  # Start with second shot (approach)
        
        while shot_number <= max_shots:
            all_completed = True
            
            for player in game_state.player_manager.players:
                player_id = player.id
                position = player_positions[player_id]
                
                # Skip if player already completed the hole
                if position.get("completed", False):
                    continue
                
                all_completed = False
                distance_to_pin = position["distance_to_pin"]
                lie = position["lie"]
                on_green = position["on_green"]
                
                # Determine shot type and simulate
                if on_green:
                    # Putting
                    shot_result = ShotSimulator._simulate_putt(player, distance_to_pin, game_state)
                    shot_desc = f"Putt from {distance_to_pin:.0f} feet"
                elif distance_to_pin <= 30:
                    # Chip shot
                    shot_result = ShotSimulator._simulate_chip(player, distance_to_pin, lie, game_state)
                    shot_desc = f"Chip from {distance_to_pin:.0f} yards ({lie})"
                else:
                    # Approach shot
                    shot_result = ShotSimulator.simulate_approach_shot(player, int(distance_to_pin), game_state)
                    shot_desc = f"Approach from {distance_to_pin:.0f} yards ({lie})"
                
                # Update position and score
                new_distance = shot_result.remaining
                new_lie = shot_result.lie
                new_penalty = shot_result.penalty
                
                position["distance_to_pin"] = new_distance
                position["lie"] = new_lie
                position["penalty"] = new_penalty
                position["shots_taken"] += 1
                player_scores[player_id] += 1
                
                # Check if on green (using fairway as proxy for green)
                if new_lie == "fairway" and new_distance <= 5:
                    position["on_green"] = True
                
                # Check if hole completed
                if new_distance <= 0.5:  # Within 6 inches
                    position["completed"] = True
                    final_score = player_scores[player_id]
                    
                    # Add penalty strokes
                    total_penalty = position.get("penalty", 0)
                    final_score += total_penalty
                    player_scores[player_id] = final_score
                    
                    player_name = player.name
                    if player_id == ShotSimulator._get_human_player_id(game_state):
                        feedback.append(f"🧑 **{player_name}:** {shot_desc} → **Hole completed in {final_score} strokes**")
                    else:
                        feedback.append(f"💻 **{player_name}:** {shot_desc} → **Hole completed in {final_score} strokes**")
                    
                    # Record the score in game state
                    strokes = game_state.get_player_strokes()
                    net_strokes = strokes[player_id][game_state.current_hole]
                    net_score = max(1, final_score - net_strokes)
                    game_state.dispatch_action("record_net_score", {
                        "player_id": player_id,
                        "score": int(net_score)
                    })
                else:
                    # Show shot result
                    player_name = player.name
                    if player_id == ShotSimulator._get_human_player_id(game_state):
                        feedback.append(f"🧑 **{player_name}:** {shot_desc} → {new_distance:.0f} yards remaining")
                    else:
                        feedback.append(f"💻 **{player_name}:** {shot_desc} → {new_distance:.0f} yards remaining")
            
            if all_completed:
                break
                
            shot_number += 1
        
        feedback.append("")
        return feedback

    @staticmethod
    def simulate_player_final_score(handicap: float, par: int, hole_number: int, game_state: 'GameState' = None, tee_quality: str = "average", remaining_distance: float = 150) -> int:
        base_score = ShotSimulator.simulate_player_score(handicap, par, hole_number, game_state)
        
        # Adjust based on tee shot quality
        if tee_quality == "excellent":
            adjustment = -0.3
        elif tee_quality == "good":
            adjustment = -0.1
        elif tee_quality == "average":
            adjustment = 0
        elif tee_quality == "poor":
            adjustment = 0.2
        else:  # terrible
            adjustment = 0.5
        
        # Adjust based on remaining distance
        if remaining_distance > 200:
            adjustment += 0.3
        elif remaining_distance > 150:
            adjustment += 0.1
        elif remaining_distance < 100:
            adjustment -= 0.1
        
        # Apply adjustment probabilistically
        if random.random() < abs(adjustment):
            if adjustment > 0:
                base_score += 1
            else:
                base_score = max(1, base_score - 1)
        
        return base_score

    @staticmethod
    def simulate_player_score(handicap: float, par: int, hole_number: int, game_state: 'GameState' = None) -> int:
        """Simulate a player's score based on handicap and hole difficulty"""
        # Base score starts at par
        base = par
        
        # Adjust based on handicap category
        if handicap <= 5:
            base += random.choice([-1, 0, 0, 1])  # Scratch golfers can shoot under par
        elif handicap <= 12:
            base += random.choice([0, 0, 1, 1])   # Low handicappers around par
        elif handicap <= 20:
            base += random.choice([0, 1, 1, 2])   # Mid handicappers slightly over
        else:
            base += random.choice([1, 2, 2, 3])   # High handicappers well over
        
        # Add hole-specific difficulty if available
        if game_state and hasattr(game_state, 'course_manager') and game_state.course_manager.course_data:
            hole_data = game_state.course_manager.course_data.get(str(hole_number), {})
            difficulty = hole_data.get('difficulty', 0)
            base += int(difficulty)
        
        return max(1, base)  # Ensure minimum score of 1

    @staticmethod
    def _simulate_putt(player: Player, distance_to_pin: float, game_state: GameState) -> ShotResult:
        """Simulate a putt"""
        # Putt distance is typically 80-90% of distance to pin
        putt_distance = distance_to_pin * random.uniform(0.8, 0.9)
        remaining = max(0, distance_to_pin - putt_distance)
        
        # Determine if putt went in
        if remaining <= 0.5:  # Within 6 inches
            remaining = 0
            lie = "fairway"  # Use fairway as closest valid lie for green
            shot_quality = "excellent"
        else:
            lie = "fairway"  # Use fairway as closest valid lie for green
            if remaining <= 2:
                shot_quality = "good"
            elif remaining <= 5:
                shot_quality = "average"
            elif remaining <= 10:
                shot_quality = "poor"
            else:
                shot_quality = "terrible"
        
        return ShotResult(
            player=player,
            drive=int(putt_distance),
            lie=lie,
            remaining=remaining,
            shot_quality=shot_quality,
            penalty=0,
            hole_number=game_state.current_hole
        )

    @staticmethod
    def _simulate_chip(player: Player, distance_to_pin: float, lie: str, game_state: GameState) -> ShotResult:
        """Simulate a chip shot"""
        # Chip distance varies based on lie and player skill
        base_distance = distance_to_pin * random.uniform(0.7, 1.1)
        
        # Adjust for lie difficulty
        if lie == "rough":
            base_distance *= random.uniform(0.8, 1.0)
        elif lie == "bunker":
            base_distance *= random.uniform(0.6, 0.9)
        
        remaining = max(0, distance_to_pin - base_distance)
        
        # Determine lie after chip (using valid lie types)
        if remaining <= 5:
            lie = "fairway"  # Use fairway as closest valid lie for green
            shot_quality = "excellent"
        elif remaining <= 15:
            lie = "fairway"  # Use fairway as closest valid lie for green
            shot_quality = "good"
        elif remaining <= 25:
            lie = "first cut"  # Use first cut as closest valid lie for fringe
            shot_quality = "average"
        else:
            lie = "rough"
            shot_quality = "poor"
        
        return ShotResult(
            player=player,
            drive=int(base_distance),
            lie=lie,
            remaining=remaining,
            shot_quality=shot_quality,
            penalty=0,
            hole_number=game_state.current_hole
        )



    @staticmethod
    def _get_human_player_id(game_state: GameState) -> str:
        """Get the human player ID consistently using GameState utility"""
        return game_state.get_human_player_id()
