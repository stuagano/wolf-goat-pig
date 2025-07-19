"""
Utility functions for common operations
"""
from typing import Dict, List, Optional, Any
from .constants import STRENGTH_THRESHOLDS, EXPECTED_YARDS_BY_PAR


class PlayerUtils:
    """Utility functions for player-related operations"""
    
    @staticmethod
    def handicap_to_strength(handicap: float) -> str:
        """Convert handicap to strength category"""
        for strength, (min_hcp, max_hcp) in STRENGTH_THRESHOLDS.items():
            if min_hcp <= handicap <= max_hcp:
                return strength
        return "Average"  # Default fallback
    
    @staticmethod
    def find_player_by_id(players: List[Dict], player_id: str) -> Optional[Dict]:
        """Find a player by ID in a player list"""
        for player in players:
            if player.get("id") == player_id:
                return player
        return None
    
    @staticmethod
    def get_player_name(players: List[Dict], player_id: str) -> str:
        """Get player name by ID, return ID if not found"""
        player = PlayerUtils.find_player_by_id(players, player_id)
        return player.get("name", player_id) if player else player_id
    
    @staticmethod
    def get_player_handicap(players: List[Dict], player_id: str) -> float:
        """Get player handicap by ID"""
        player = PlayerUtils.find_player_by_id(players, player_id)
        return player.get("handicap", 0.0) if player else 0.0
    
    @staticmethod
    def extract_player_ids(players: List[Dict]) -> List[str]:
        """Extract list of player IDs from player list"""
        return [p["id"] for p in players]
    
    @staticmethod
    def get_players_excluding(players: List[Dict], excluded_ids: List[str]) -> List[str]:
        """Get player IDs excluding specified IDs"""
        return [p["id"] for p in players if p["id"] not in excluded_ids]
    
    @staticmethod
    def create_player_id_mapping(players: List[Dict], default_value: Any = None) -> Dict[str, Any]:
        """Create a mapping from player ID to a default value"""
        return {p["id"]: default_value for p in players}
    
    @staticmethod
    def get_players_by_ids(players: List[Dict], player_ids: List[str]) -> List[Dict]:
        """Get player objects by their IDs"""
        return [p for p in players if p["id"] in player_ids]


class CourseUtils:
    """Utility functions for course-related operations"""
    
    @staticmethod
    def convert_hole_to_dict(hole) -> Dict:
        """Convert a hole object/schema to dictionary format expected by game_state"""
        return {
            "hole_number": hole.hole_number,
            "par": hole.par,
            "yards": hole.yards,
            "stroke_index": hole.handicap,  # Note: handicap in schema = stroke_index in game_state
            "description": hole.description or ""
        }
    
    @staticmethod
    def convert_course_create_to_dict(course) -> Dict:
        """Convert CourseCreate schema to dict format for game_state"""
        return {
            "name": course.name,
            "holes": [CourseUtils.convert_hole_to_dict(hole) for hole in course.holes]
        }
    
    @staticmethod
    def convert_course_update_to_dict(course_update) -> Dict:
        """Convert CourseUpdate schema to dict format for game_state"""
        update_data = {}
        if course_update.name:
            update_data["name"] = course_update.name
        if course_update.holes:
            update_data["holes"] = [
                CourseUtils.convert_hole_to_dict(hole) for hole in course_update.holes
            ]
        return update_data


class GameUtils:
    """Utility functions for game logic"""
    
    @staticmethod
    def assess_hole_difficulty(stroke_index: int, par: int, yards: Optional[int] = None, 
                             player_handicap: float = 15.0) -> float:
        """Assess how difficult a hole is (0=easy, 1=very hard)"""
        if not stroke_index or not par:
            return 0.5
        
        # Lower stroke index = harder hole
        difficulty = (19 - stroke_index) / 18.0
        
        # Factor in distance/yards if available
        if yards:
            expected = EXPECTED_YARDS_BY_PAR.get(par, 400)
            distance_factor = min(1.5, yards / expected)
            # Weight: 70% stroke index, 30% distance
            difficulty = 0.7 * difficulty + 0.3 * (distance_factor - 0.5)
        
        # Adjust based on par and player handicap
        if par == 5:
            difficulty *= 0.9  # Par 5s are generally easier for high handicappers
        if par == 5 and player_handicap > 15:
            difficulty *= 0.8
        elif par == 3 and player_handicap > 20:
            difficulty *= 1.2
            
        return min(1.0, max(0.0, difficulty))
    
    @staticmethod
    def calculate_stroke_advantage(team1_handicaps: List[float], team2_handicaps: List[float], 
                                 team1_strokes: List[int], team2_strokes: List[int]) -> float:
        """Calculate stroke advantage between two teams (-1 to 1)"""
        # Calculate net stroke advantage
        team1_best = min(team1_strokes)
        team2_best = min(team2_strokes)
        stroke_advantage = team2_best - team1_best
        
        # Consider handicap differences
        handicap_advantage = (sum(team2_handicaps) - sum(team1_handicaps)) / 20.0
        
        return min(1.0, max(-1.0, stroke_advantage + handicap_advantage))


class ValidationUtils:
    """Utility functions for validation"""
    
    @staticmethod
    def validate_player_count(players: List[Dict], min_players: int, max_players: int) -> bool:
        """Validate player count is within acceptable range"""
        return min_players <= len(players) <= max_players
    
    @staticmethod
    def validate_handicap_range(handicap: float, min_val: float = 0.0, max_val: float = 36.0) -> bool:
        """Validate handicap is within acceptable range"""
        return min_val <= handicap <= max_val
    
    @staticmethod
    def validate_hole_number_sequence(holes: List[Dict]) -> bool:
        """Validate holes have proper 1-18 sequence"""
        hole_numbers = sorted([hole["hole_number"] for hole in holes])
        return hole_numbers == list(range(1, 19))
    
    @staticmethod
    def validate_unique_handicaps(holes: List[Dict]) -> bool:
        """Validate all stroke indexes (handicaps) are unique 1-18"""
        handicaps = [hole.get("stroke_index", hole.get("handicap", 0)) for hole in holes]
        return len(set(handicaps)) == 18 and set(handicaps) == set(range(1, 19))


class SerializationUtils:
    """Utility functions for serialization"""
    
    @staticmethod
    def serialize_game_state(game_state) -> Dict:
        """Serialize game state to dictionary for API responses"""
        return {
            "players": game_state.players,
            "current_hole": game_state.current_hole,
            "hitting_order": game_state.hitting_order,
            "captain_id": game_state.captain_id,
            "teams": game_state.teams,
            "base_wager": game_state.base_wager,
            "doubled_status": game_state.doubled_status,
            "game_phase": game_state.game_phase,
            "hole_scores": game_state.hole_scores,
            "game_status_message": game_state.game_status_message,
            "player_float_used": game_state.player_float_used,
            "carry_over": game_state.carry_over,
            "hole_history": game_state.get_hole_history(),
            "hole_stroke_indexes": game_state.hole_stroke_indexes,
            "hole_pars": game_state.hole_pars,
            "selected_course": game_state.selected_course,
        }


class SimulationUtils:
    """Utility functions for simulation operations"""
    
    @staticmethod
    def convert_computer_player_configs(computer_configs: List) -> List[Dict]:
        """Convert computer player configs to dict format"""
        return [
            {
                "id": cp.id,
                "name": cp.name,
                "handicap": cp.handicap,
                "personality": cp.personality
            } for cp in computer_configs
        ]
    
    @staticmethod
    def setup_all_players(human_player: Dict, computer_configs: List[Dict]) -> List[Dict]:
        """Setup combined list of human and computer players"""
        return [
            {
                "id": human_player["id"],
                "name": human_player["name"],
                "handicap": human_player["handicap"],
                "strength": PlayerUtils.handicap_to_strength(human_player["handicap"])
            }
        ] + [
            {
                "id": cp["id"],
                "name": cp["name"],
                "handicap": cp["handicap"],
                "strength": PlayerUtils.handicap_to_strength(cp["handicap"])
            } for cp in computer_configs
        ]


class GameStateUtils:
    """Utility functions for game state management"""
    
    @staticmethod
    def create_hitting_order(players: List[Dict]) -> List[str]:
        """Create and shuffle hitting order from players"""
        import random
        hitting_order = PlayerUtils.extract_player_ids(players)
        random.shuffle(hitting_order)
        return hitting_order
    
    @staticmethod
    def initialize_player_tracking_dicts(players: List[Dict]) -> Dict[str, Dict]:
        """Initialize all player tracking dictionaries at once"""
        return {
            "hole_scores": PlayerUtils.create_player_id_mapping(players, None),
            "player_float_used": PlayerUtils.create_player_id_mapping(players, False),
            "_last_points": PlayerUtils.create_player_id_mapping(players, 0)
        }
    
    @staticmethod
    def format_winner_names(player_names: List[str]) -> str:
        """Format winner names for display messages"""
        if not player_names:
            return "Nobody"
        elif len(player_names) == 1:
            return player_names[0]
        elif len(player_names) == 2:
            return f"{player_names[0]} and {player_names[1]}"
        else:
            return f"{', '.join(player_names[:-1])}, and {player_names[-1]}"