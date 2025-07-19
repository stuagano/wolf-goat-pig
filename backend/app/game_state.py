from typing import List, Dict
import random
import json
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import GameStateModel
from .constants import DEFAULT_PLAYERS, DEFAULT_COURSES, GAME_CONSTANTS
from .utils import PlayerUtils, ValidationUtils, GameStateUtils
from .exceptions import GameStateException, ValidationException

class GameState:
    def __init__(self):
        self._db_session = SessionLocal()
        self._load_from_db()
        self.courses = dict(DEFAULT_COURSES)
        self.selected_course = None
        self._initialize_course_data()
        # If the DB is empty (first run), do NOT auto-populate players or state
        if not hasattr(self, 'players') or self.players is None:
            self._initialize_empty_state()

    def _initialize_course_data(self):
        """Initialize course-related data using constants"""
        default_course = DEFAULT_COURSES["Wing Point"]
        self.hole_stroke_indexes = [h["stroke_index"] for h in default_course]
        self.hole_pars = [h["par"] for h in default_course]
        self.hole_yards = [h["yards"] for h in default_course]
        self.hole_descriptions = [h.get("description", "") for h in default_course]

    def _initialize_empty_state(self):
        """Initialize empty game state using constants"""
        self.players = []
        self.current_hole = None
        self.hitting_order = []
        self.captain_id = None
        self.teams = {}
        self.base_wager = GAME_CONSTANTS["DEFAULT_BASE_WAGER"]
        self.doubled_status = False
        self.game_phase = None
        self.hole_scores = {}
        self.game_status_message = "Please set up a new game."
        self.player_float_used = {}
        self.carry_over = False
        self.hole_history = []
        self._last_points = {}
        self.hole_stroke_indexes = []
        self.hole_pars = []
        self.selected_course = None

    def reset(self):
        """Reset game state to default values"""
        self.players: List[Dict] = [dict(player) for player in DEFAULT_PLAYERS]
        self.current_hole: int = 1
        self.hitting_order: List[str] = self._random_order()
        self.captain_id: str = self.hitting_order[0]
        self.teams: Dict = {}
        self.base_wager: int = GAME_CONSTANTS["DEFAULT_BASE_WAGER"]
        self.doubled_status: bool = False
        self.game_phase: str = GAME_CONSTANTS["DEFAULT_GAME_PHASE"]
        # Initialize player tracking dictionaries using utility
        tracking_dicts = GameStateUtils.initialize_player_tracking_dicts(self.players)
        self.hole_scores = tracking_dicts["hole_scores"]
        self.player_float_used = tracking_dicts["player_float_used"]
        self._last_points = tracking_dicts["_last_points"]
        
        self.game_status_message: str = GAME_CONSTANTS["DEFAULT_STATUS_MESSAGE"]
        self.carry_over: bool = False
        self.hole_history: List[Dict] = []
        self._initialize_course_data()
        self._save_to_db()

    def _random_order(self) -> List[str]:
        """Generate random hitting order for players"""
        ids = PlayerUtils.extract_player_ids(DEFAULT_PLAYERS)
        random.shuffle(ids)
        return ids

    def dispatch_action(self, action, payload):
        """Dispatch game actions with improved error handling"""
        action_map = {
            "request_partner": lambda: self.request_partner(payload.get("captain_id"), payload.get("partner_id")),
            "accept_partner": lambda: self.accept_partner(payload.get("partner_id")),
            "decline_partner": lambda: self.decline_partner(payload.get("partner_id")),
            "go_solo": lambda: self.go_solo(payload.get("captain_id")),
            "offer_double": lambda: self.offer_double(payload.get("offering_team_id"), payload.get("target_team_id")),
            "accept_double": lambda: self.accept_double(payload.get("team_id")),
            "decline_double": lambda: self.decline_double(payload.get("team_id")),
            "invoke_float": lambda: self.invoke_float(payload.get("captain_id")),
            "toggle_option": lambda: self.toggle_option(payload.get("captain_id")),
            "record_net_score": lambda: self.record_net_score(payload.get("player_id"), payload.get("score")),
            "calculate_hole_points": lambda: self.calculate_hole_points(),
            "next_hole": lambda: self.next_hole(),
        }
        
        if action not in action_map:
            raise GameStateException(f"Unknown action: {action}")
        
        return action_map[action]()

    def request_partner(self, captain_id, partner_id):
        """Request a partner for the captain"""
        self.game_status_message = f"Captain {self._get_player_name(captain_id)} requests {self._get_player_name(partner_id)} as partner. Awaiting response."
        # For MVP, just set teams as pending
        self.teams = {"type": "pending", "captain": captain_id, "requested": partner_id}
        return "Partner requested."

    def accept_partner(self, partner_id):
        """Accept a partnership request"""
        if self.teams.get("type") != "pending" or self.teams.get("requested") != partner_id:
            raise GameStateException("No pending partner request for this player.")
        captain_id = self.teams["captain"]
        others = PlayerUtils.get_players_excluding(self.players, [captain_id, partner_id])
        self.teams = {"type": "partners", "team1": [captain_id, partner_id], "team2": others}
        self.game_status_message = f"{self._get_player_name(partner_id)} accepted. Teams formed."
        return "Partnership accepted."

    def decline_partner(self, partner_id):
        """Decline a partnership request"""
        if self.teams.get("type") != "pending" or self.teams.get("requested") != partner_id:
            raise GameStateException("No pending partner request for this player.")
        captain_id = self.teams["captain"]
        others = PlayerUtils.get_players_excluding(self.players, [captain_id])
        self.teams = {"type": "solo", "captain": captain_id, "opponents": others}
        self.base_wager *= 2  # On your own rule
        self.game_status_message = f"{self._get_player_name(partner_id)} declined. {self._get_player_name(captain_id)} goes solo! Wager doubled."
        return "Partnership declined. Captain goes solo."

    def go_solo(self, captain_id):
        """Captain chooses to go solo"""
        others = PlayerUtils.get_players_excluding(self.players, [captain_id])
        self.teams = {"type": "solo", "captain": captain_id, "opponents": others}
        self.base_wager *= 2
        self.game_status_message = f"{self._get_player_name(captain_id)} goes solo! Wager doubled."
        return "Captain goes solo."

    def offer_double(self, offering_team_id, target_team_id):
        """Offer to double the wager"""
        if self.doubled_status:
            raise GameStateException("Double already offered or accepted on this hole.")
        self.doubled_status = True
        self.game_status_message = f"Team {offering_team_id} offers to double Team {target_team_id}. Awaiting response."
        return "Double offered."

    def accept_double(self, team_id):
        """Accept a double offer"""
        if not self.doubled_status:
            raise GameStateException("No double to accept.")
        self.base_wager *= 2
        self.doubled_status = False
        self.game_status_message = f"Team {team_id} accepted the double. Wager doubled!"
        return "Double accepted."

    def decline_double(self, team_id):
        """Decline a double offer"""
        if not self.doubled_status:
            raise GameStateException("No double to decline.")
        self.doubled_status = False
        self.game_status_message = f"Team {team_id} declined the double. Offering team wins at prior stake."
        # For MVP, just set a flag; real logic would award points here
        return "Double declined. Offering team wins hole."

    def invoke_float(self, captain_id):
        """Invoke the float option"""
        if self.player_float_used.get(captain_id):
            raise GameStateException("Float already used by this captain.")
        self.base_wager *= 2
        self.player_float_used[captain_id] = True
        self.game_status_message = f"{self._get_player_name(captain_id)} invoked the float! Wager doubled."
        return "Float invoked."

    def toggle_option(self, captain_id):
        """Toggle the option (for MVP, just double wager)"""
        self.base_wager *= 2
        self.game_status_message = f"{self._get_player_name(captain_id)} toggled the option. Wager doubled."
        return "Option toggled."

    def record_net_score(self, player_id, score):
        """Record a net score for a player"""
        if player_id not in PlayerUtils.extract_player_ids(self.players):
            raise GameStateException(f"Player {player_id} not found.")
        self.hole_scores[player_id] = score
        self.game_status_message = f"Score recorded for {self._get_player_name(player_id)}: {score}."
        return "Score recorded."

    def calculate_hole_points(self):
        """Calculate points for the current hole"""
        # For MVP, simple point calculation
        if not self.hole_scores or all(score is None for score in self.hole_scores.values()):
            return "No scores to calculate."
        
        # Find the lowest score
        valid_scores = {pid: score for pid, score in self.hole_scores.items() if score is not None}
        if not valid_scores:
            return "No valid scores."
        
        lowest_score = min(valid_scores.values())
        winners = [pid for pid, score in valid_scores.items() if score == lowest_score]
        
        # Award points (simplified)
        for player in self.players:
            if player["id"] in winners:
                player["points"] += self.base_wager
        
        # Record in history
        self.hole_history.append({
            "hole": self.current_hole,
            "scores": dict(self.hole_scores),
            "winners": winners,
            "wager": self.base_wager
        })
        
        self.game_status_message = f"Hole {self.current_hole} complete. Winners: {', '.join([self._get_player_name(pid) for pid in winners])}"
        return "Points calculated."

    def next_hole(self):
        """Advance to the next hole"""
        if self.current_hole >= GAME_CONSTANTS["MAX_HOLES"]:
            self.game_status_message = "Game complete!"
            return "Game finished."
        
        self.current_hole += 1
        self.hole_scores = PlayerUtils.create_player_id_mapping(self.players, None)
        self.doubled_status = False
        self.teams = {}
        
        # Rotate hitting order
        if self.hitting_order:
            self.hitting_order = self.hitting_order[1:] + [self.hitting_order[0]]
            self.captain_id = self.hitting_order[0]
        
        self.game_status_message = f"Starting hole {self.current_hole}. Captain: {self._get_player_name(self.captain_id)}"
        self._save_to_db()
        return f"Advanced to hole {self.current_hole}."

    def _get_player_name(self, player_id: str) -> str:
        """Get player name by ID using utility function"""
        return PlayerUtils.get_player_name(self.players, player_id)

    def get_hole_history(self):
        """Get the hole history"""
        return self.hole_history

    def setup_players(self, players: List[Dict], course_name: str = None):
        """Setup players for the game with validation"""
        if not ValidationUtils.validate_player_count(players, GAME_CONSTANTS["MIN_PLAYERS"], GAME_CONSTANTS["MAX_PLAYERS"]):
            raise ValidationException(f"Must have between {GAME_CONSTANTS['MIN_PLAYERS']} and {GAME_CONSTANTS['MAX_PLAYERS']} players")
        
        # Validate player data
        for player in players:
            if not player.get("id") or not player.get("name"):
                raise ValidationException("Each player must have an id and name")
            if not ValidationUtils.validate_handicap_range(player.get("handicap", 0)):
                raise ValidationException(f"Invalid handicap for player {player['name']}")
        
        self.players = []
        for player in players:
            self.players.append({
                "id": player["id"],
                "name": player["name"],
                "handicap": player.get("handicap", 18.0),
                "points": 0,
                "strength": PlayerUtils.handicap_to_strength(player.get("handicap", 18.0))
            })
        
        # Set up course if provided
        if course_name and course_name in self.courses:
            self.selected_course = course_name
            course = self.courses[course_name]
            self.hole_stroke_indexes = [h["stroke_index"] for h in course]
            self.hole_pars = [h["par"] for h in course]
            self.hole_yards = [h["yards"] for h in course]
            self.hole_descriptions = [h.get("description", "") for h in course]
        
        # Initialize game state
        self.current_hole = 1
        self.hitting_order = GameStateUtils.create_hitting_order(self.players)
        self.captain_id = self.hitting_order[0]
        
        # Initialize all player tracking dictionaries at once
        tracking_dicts = GameStateUtils.initialize_player_tracking_dicts(self.players)
        self.hole_scores = tracking_dicts["hole_scores"]
        self.player_float_used = tracking_dicts["player_float_used"]
        self._last_points = tracking_dicts["_last_points"]
        
        self.game_status_message = f"Game set up with {len(self.players)} players. Captain: {self._get_player_name(self.captain_id)}"
        self._save_to_db()

    def get_player_strokes(self):
        """Get net strokes for each player on each hole"""
        strokes = {}
        for player in self.players:
            player_id = player["id"]
            handicap = player["handicap"]
            strokes[player_id] = {}
            
            for hole in range(1, GAME_CONSTANTS["MAX_HOLES"] + 1):
                if hole <= len(self.hole_stroke_indexes):
                    stroke_index = self.hole_stroke_indexes[hole - 1]
                    # Calculate strokes received based on handicap and stroke index
                    strokes_received = 1 if handicap >= stroke_index else 0
                    # Add additional stroke for very high handicaps
                    if handicap >= stroke_index + 18:
                        strokes_received += 1
                    strokes[player_id][hole] = strokes_received
                else:
                    strokes[player_id][hole] = 0
        
        return strokes

    def get_courses(self):
        """Get all available courses"""
        return list(self.courses.keys())

    def add_course(self, course_data: Dict):
        """Add a new course with validation"""
        if not course_data.get("name"):
            raise ValidationException("Course name is required")
        
        if course_data["name"] in self.courses:
            raise ValidationException("Course already exists")
        
        holes = course_data.get("holes", [])
        if len(holes) != GAME_CONSTANTS["MAX_HOLES"]:
            raise ValidationException(f"Course must have exactly {GAME_CONSTANTS['MAX_HOLES']} holes")
        
        if not ValidationUtils.validate_hole_number_sequence(holes):
            raise ValidationException("Holes must be numbered 1-18")
        
        if not ValidationUtils.validate_unique_handicaps(holes):
            raise ValidationException("All handicaps must be unique (1-18)")
        
        self.courses[course_data["name"]] = holes

    def update_course(self, course_name: str, update_data: Dict):
        """Update an existing course"""
        if course_name not in self.courses:
            raise ValidationException("Course not found")
        
        if "name" in update_data:
            new_name = update_data["name"]
            if new_name != course_name and new_name in self.courses:
                raise ValidationException("Course name already exists")
            # Rename course
            self.courses[new_name] = self.courses.pop(course_name)
            course_name = new_name
        
        if "holes" in update_data:
            holes = update_data["holes"]
            if len(holes) != GAME_CONSTANTS["MAX_HOLES"]:
                raise ValidationException(f"Course must have exactly {GAME_CONSTANTS['MAX_HOLES']} holes")
            
            if not ValidationUtils.validate_hole_number_sequence(holes):
                raise ValidationException("Holes must be numbered 1-18")
            
            if not ValidationUtils.validate_unique_handicaps(holes):
                raise ValidationException("All handicaps must be unique (1-18)")
            
            self.courses[course_name] = holes

    def delete_course(self, course_name: str):
        """Delete a course"""
        if course_name not in self.courses:
            raise ValidationException("Course not found")
        
        # Don't allow deletion of default courses
        if course_name in DEFAULT_COURSES:
            raise ValidationException("Cannot delete default courses")
        
        del self.courses[course_name]

    def get_course_stats(self, course_name: str) -> Dict:
        """Get statistics for a course"""
        if course_name not in self.courses:
            raise ValidationException("Course not found")
        
        course = self.courses[course_name]
        total_par = sum(hole["par"] for hole in course)
        total_yards = sum(hole["yards"] for hole in course)
        
        # Calculate difficulty rating (simplified)
        avg_stroke_index = sum(hole["stroke_index"] for hole in course) / len(course)
        difficulty_rating = (19 - avg_stroke_index) / 18.0 * 10  # Scale 0-10
        
        return {
            "total_par": total_par,
            "total_yards": total_yards,
            "difficulty_rating": round(difficulty_rating, 2),
            "par_3_count": sum(1 for hole in course if hole["par"] == 3),
            "par_4_count": sum(1 for hole in course if hole["par"] == 4),
            "par_5_count": sum(1 for hole in course if hole["par"] == 5),
            "longest_hole": max(hole["yards"] for hole in course),
            "shortest_hole": min(hole["yards"] for hole in course),
        }

    def get_current_hole_info(self) -> Dict:
        """Get information about the current hole"""
        if not self.current_hole or self.current_hole > GAME_CONSTANTS["MAX_HOLES"]:
            return None
        
        hole_idx = self.current_hole - 1
        if hole_idx >= len(self.hole_pars):
            return None
        
        return {
            "hole_number": self.current_hole,
            "par": self.hole_pars[hole_idx],
            "stroke_index": self.hole_stroke_indexes[hole_idx] if hole_idx < len(self.hole_stroke_indexes) else 0,
            "yards": self.hole_yards[hole_idx] if hole_idx < len(self.hole_yards) else 0,
            "description": self.hole_descriptions[hole_idx] if hole_idx < len(self.hole_descriptions) else ""
        }

    def get_betting_tips(self):
        """Get context-aware betting tips"""
        tips = []
        
        # Add basic tips based on game state
        if self.doubled_status:
            tips.append("A double has been offered. Consider your position carefully before accepting.")
        
        if self.teams and self.teams.get("type") == "solo":
            tips.append("Going solo doubles the wager but you must beat the best ball of the other players.")
        
        # Add hole-specific tips
        if self.current_hole and self.current_hole >= GAME_CONSTANTS["VINNIE_VARIATION_START_HOLE"]:
            tips.append("Vinnie's Variation is in effect - base wager is doubled!")
        
        if self.current_hole and self.current_hole >= GAME_CONSTANTS["HOEPFINGER_START_HOLE"]:
            tips.append("Hoepfinger phase: The player furthest down chooses their spot in the rotation.")
        
        # Add player-specific tips
        if self.captain_id and not self.player_float_used.get(self.captain_id, False):
            tips.append("You haven't used your float yet. Save it for a strategic moment.")
        
        tips.append("Remember: If you decline a double, the offering team wins the hole at current stakes.")
        
        return tips

    def get_hole_difficulty_factor(self, hole_number):
        """Calculate difficulty factor for a specific hole for simulation"""
        hole_idx = hole_number - 1
        if hole_idx < 0 or hole_idx >= len(self.hole_stroke_indexes):
            return 1.0
        
        # Combine stroke index difficulty with distance
        stroke_index = self.hole_stroke_indexes[hole_idx]
        stroke_difficulty = (19 - stroke_index) / 18  # 0-1, higher = more difficult
        
        if hasattr(self, 'hole_yards') and hole_idx < len(self.hole_yards):
            par = self.hole_pars[hole_idx]
            yards = self.hole_yards[hole_idx]
            # Normalize yards by par (longer than expected = harder)
            expected_yards = {3: 150, 4: 400, 5: 550}
            yard_difficulty = min(1.5, yards / expected_yards.get(par, 400))
            
            # Combine factors
            return 0.7 * stroke_difficulty + 0.3 * (yard_difficulty - 0.5)
        
        return stroke_difficulty

    def _serialize(self):
        """Serialize game state to dictionary for database storage"""
        return {
            "players": self.players,
            "current_hole": self.current_hole,
            "hitting_order": self.hitting_order,
            "captain_id": self.captain_id,
            "teams": self.teams,
            "base_wager": self.base_wager,
            "doubled_status": self.doubled_status,
            "game_phase": self.game_phase,
            "hole_scores": self.hole_scores,
            "game_status_message": self.game_status_message,
            "player_float_used": self.player_float_used,
            "carry_over": self.carry_over,
            "hole_history": self.hole_history,
            "_last_points": self._last_points,
            "hole_stroke_indexes": self.hole_stroke_indexes,
            "hole_pars": self.hole_pars,
            "selected_course": self.selected_course,
        }

    def _deserialize(self, data):
        """Deserialize game state from database"""
        self.players = data.get("players", [dict(player) for player in DEFAULT_PLAYERS])
        self.current_hole = data.get("current_hole", 1)
        self.hitting_order = data.get("hitting_order", PlayerUtils.extract_player_ids(DEFAULT_PLAYERS))
        self.captain_id = data.get("captain_id", self.hitting_order[0] if self.hitting_order else None)
        self.teams = data.get("teams", {})
        self.base_wager = data.get("base_wager", GAME_CONSTANTS["DEFAULT_BASE_WAGER"])
        self.doubled_status = data.get("doubled_status", False)
        self.game_phase = data.get("game_phase", GAME_CONSTANTS["DEFAULT_GAME_PHASE"])
        self.hole_scores = data.get("hole_scores", PlayerUtils.create_player_id_mapping(self.players, None))
        self.game_status_message = data.get("game_status_message", GAME_CONSTANTS["DEFAULT_STATUS_MESSAGE"])
        self.player_float_used = data.get("player_float_used", PlayerUtils.create_player_id_mapping(self.players, False))
        self.carry_over = data.get("carry_over", False)
        self.hole_history = data.get("hole_history", [])
        self._last_points = data.get("_last_points", PlayerUtils.create_player_id_mapping(self.players, 0))
        self.hole_stroke_indexes = data.get("hole_stroke_indexes", [h["stroke_index"] for h in DEFAULT_COURSES["Wing Point"]])
        self.hole_pars = data.get("hole_pars", [h["par"] for h in DEFAULT_COURSES["Wing Point"]])
        self.selected_course = data.get("selected_course", None)

    def _save_to_db(self):
        """Save the current state as JSON in the database"""
        state_json = self._serialize()
        session = self._db_session
        obj = session.query(GameStateModel).get(1)
        if obj:
            obj.state = state_json
        else:
            obj = GameStateModel(id=1, state=state_json)
            session.add(obj)
        session.commit()

    def _load_from_db(self):
        """Load the state from database if present"""
        session = self._db_session
        obj = session.query(GameStateModel).get(1)
        if obj and obj.state:
            self._deserialize(obj.state)
        else:
            # Initialize with empty state if no DB data
            pass  # Will be handled in __init__

# Singleton game state for MVP (in-memory)
game_state = GameState() 