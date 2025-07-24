from typing import List, Dict
import random
import json
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import GameStateModel

# Default player names for MVP
DEFAULT_PLAYERS = [
    {"id": "p1", "name": "Bob", "points": 0, "handicap": 10.5, "strength": "Average"},
    {"id": "p2", "name": "Scott", "points": 0, "handicap": 15, "strength": "Average"},
    {"id": "p3", "name": "Vince", "points": 0, "handicap": 8, "strength": "Average"},
    {"id": "p4", "name": "Mike", "points": 0, "handicap": 20.5, "strength": "Average"},
]

# Example stroke index for 18 holes (1 = hardest, 18 = easiest)
DEFAULT_HOLE_STROKE_INDEXES = [1, 15, 7, 13, 3, 17, 9, 11, 5, 2, 16, 8, 14, 4, 18, 10, 12, 6]

# Enhanced course data with yards for simulation mode
DEFAULT_COURSES = {
    "Wing Point": [
        {"hole_number": 1, "stroke_index": 5, "par": 5, "yards": 476, "description": "Par 5 opening hole. Long, straight, reachable in two for long hitters."},
        {"hole_number": 2, "stroke_index": 15, "par": 3, "yards": 175, "description": "Short par 3. Watch for wind and tricky green."},
        {"hole_number": 3, "stroke_index": 1, "par": 4, "yards": 401, "description": "Difficult par 4. Long and demanding with a tough approach."},
        {"hole_number": 4, "stroke_index": 17, "par": 3, "yards": 133, "description": "Shortest hole on the course. Precision required."},
        {"hole_number": 5, "stroke_index": 7, "par": 5, "yards": 498, "description": "Par 5 with risk/reward second shot. Birdie opportunity."},
        {"hole_number": 6, "stroke_index": 11, "par": 4, "yards": 351, "description": "Dogleg par 4. Position off the tee is key."},
        {"hole_number": 7, "stroke_index": 9, "par": 4, "yards": 316, "description": "Short par 4. Play for position, not distance."},
        {"hole_number": 8, "stroke_index": 13, "par": 4, "yards": 294, "description": "Drivable par 4 for long hitters. Risk/reward."},
        {"hole_number": 9, "stroke_index": 3, "par": 4, "yards": 340, "description": "Tough finishing hole on the front. Demanding approach."},
        {"hole_number": 10, "stroke_index": 16, "par": 3, "yards": 239, "description": "Long par 3. Club selection is crucial."},
        {"hole_number": 11, "stroke_index": 2, "par": 4, "yards": 401, "description": "Strong par 4. Demands accuracy off the tee."},
        {"hole_number": 12, "stroke_index": 14, "par": 3, "yards": 204, "description": "Mid-length par 3. Green is well protected."},
        {"hole_number": 13, "stroke_index": 8, "par": 4, "yards": 310, "description": "Short par 4. Good birdie chance."},
        {"hole_number": 14, "stroke_index": 10, "par": 4, "yards": 317, "description": "Dogleg par 4. Play to the corner for best angle."},
        {"hole_number": 15, "stroke_index": 18, "par": 4, "yards": 396, "description": "Easiest hole on the course. Play aggressively."},
        {"hole_number": 16, "stroke_index": 4, "par": 4, "yards": 358, "description": "Challenging par 4. Demanding approach shot."},
        {"hole_number": 17, "stroke_index": 12, "par": 5, "yards": 490, "description": "Par 5. Reachable in two for long hitters."},
        {"hole_number": 18, "stroke_index": 6, "par": 4, "yards": 394, "description": "Strong finishing hole. Demanding tee shot and approach."},
    ],
    "Championship Links": [
        {"hole_number": 1, "stroke_index": 7, "par": 4, "yards": 450, "description": "Opening hole with wide fairway but challenging approach to elevated green."},
        {"hole_number": 2, "stroke_index": 15, "par": 3, "yards": 185, "description": "Long par 3 with deep bunkers and wind factor."},
        {"hole_number": 3, "stroke_index": 1, "par": 5, "yards": 620, "description": "Monster par 5 requiring three solid shots. Water hazard on the right."},
        {"hole_number": 4, "stroke_index": 3, "par": 4, "yards": 485, "description": "Long par 4 with narrow fairway and difficult green complex."},
        {"hole_number": 5, "stroke_index": 11, "par": 4, "yards": 420, "description": "Dogleg left with strategic bunkering. Position is key."},
        {"hole_number": 6, "stroke_index": 17, "par": 5, "yards": 580, "description": "Reachable par 5 with risk/reward second shot over water."},
        {"hole_number": 7, "stroke_index": 5, "par": 4, "yards": 465, "description": "Long par 4 with out of bounds left and water right."},
        {"hole_number": 8, "stroke_index": 13, "par": 3, "yards": 195, "description": "Elevated tee with wind factor. Green slopes severely."},
        {"hole_number": 9, "stroke_index": 9, "par": 4, "yards": 440, "description": "Finishing hole with water hazard and dramatic green setting."},
        {"hole_number": 10, "stroke_index": 2, "par": 4, "yards": 470, "description": "Challenging par 4 with narrow landing area and difficult approach."},
        {"hole_number": 11, "stroke_index": 16, "par": 5, "yards": 600, "description": "Long par 5 requiring three solid shots. Strategic layup area."},
        {"hole_number": 12, "stroke_index": 14, "par": 3, "yards": 175, "description": "Short par 3 with island green. Wind and pressure factor."},
        {"hole_number": 13, "stroke_index": 18, "par": 4, "yards": 400, "description": "Short par 4, drivable for long hitters. Risk/reward hole."},
        {"hole_number": 14, "stroke_index": 4, "par": 4, "yards": 480, "description": "Long par 4 with narrow fairway and challenging green."},
        {"hole_number": 15, "stroke_index": 12, "par": 5, "yards": 590, "description": "Three-shot par 5 with water hazard crossing the fairway."},
        {"hole_number": 16, "stroke_index": 8, "par": 4, "yards": 460, "description": "Dogleg right with water hazard. Demanding tee shot and approach."},
        {"hole_number": 17, "stroke_index": 10, "par": 3, "yards": 165, "description": "Short par 3 with deep bunkers and wind factor."},
        {"hole_number": 18, "stroke_index": 6, "par": 4, "yards": 655, "description": "Epic finishing hole with water hazard and dramatic green setting."},
    ],
    "Executive Course": [
        {"hole_number": 1, "stroke_index": 9, "par": 4, "yards": 320, "description": "Short opening hole with wide fairway. Good for building confidence."},
        {"hole_number": 2, "stroke_index": 17, "par": 3, "yards": 140, "description": "Short par 3 with large green. Good for practicing irons."},
        {"hole_number": 3, "stroke_index": 5, "par": 4, "yards": 350, "description": "Straightaway par 4 with minimal hazards. Fairway is generous."},
        {"hole_number": 4, "stroke_index": 15, "par": 4, "yards": 155, "description": "Elevated tee with wind factor. Green slopes from back to front."},
        {"hole_number": 5, "stroke_index": 3, "par": 4, "yards": 365, "description": "Slight dogleg with bunkers protecting the green."},
        {"hole_number": 6, "stroke_index": 11, "par": 5, "yards": 480, "description": "Short par 5 reachable in two. Good for practicing long approach shots."},
        {"hole_number": 7, "stroke_index": 7, "par": 4, "yards": 340, "description": "Straight par 4 with water hazard on the right."},
        {"hole_number": 8, "stroke_index": 13, "par": 3, "yards": 150, "description": "Short par 3 with bunkers around the green."},
        {"hole_number": 9, "stroke_index": 1, "par": 4, "yards": 355, "description": "Finishing hole with elevated green. Approach shot requires extra club."},
        {"hole_number": 10, "stroke_index": 8, "par": 4, "yards": 330, "description": "Short par 4 with wide fairway. Good scoring opportunity."},
        {"hole_number": 11, "stroke_index": 16, "par": 4, "yards": 145, "description": "Short par 4 with large green. Wind can be a factor."},
        {"hole_number": 12, "stroke_index": 4, "par": 4, "yards": 360, "description": "Straightaway par 4 with bunkers protecting the green."},
        {"hole_number": 13, "stroke_index": 14, "par": 4, "yards": 160, "description": "Elevated tee with wind factor. Green slopes from back to front."},
        {"hole_number": 14, "stroke_index": 2, "par": 4, "yards": 375, "description": "Longest par 4 on the course. Requires solid tee shot and approach."},
        {"hole_number": 15, "stroke_index": 12, "par": 5, "yards": 490, "description": "Short par 5 reachable in two. Water hazard on the right."},
        {"hole_number": 16, "stroke_index": 6, "par": 4, "yards": 345, "description": "Dogleg left with strategic bunkering. Position is key."},
        {"hole_number": 17, "stroke_index": 18, "par": 4, "yards": 135, "description": "Shortest hole on the course. Good for practicing short irons."},
        {"hole_number": 18, "stroke_index": 10, "par": 4, "yards": 350, "description": "Finishing hole with water hazard and dramatic green setting."},
    ],
}

class GameState:
    def __init__(self):
        self._db_session = SessionLocal()
        self._load_from_db()
        self.courses = dict(DEFAULT_COURSES)
        self.selected_course = None
        self.hole_stroke_indexes = [h["stroke_index"] for h in DEFAULT_COURSES["Wing Point"]]
        self.hole_pars = [h["par"] for h in DEFAULT_COURSES["Wing Point"]]
        self.hole_yards = [h["yards"] for h in DEFAULT_COURSES["Wing Point"]]
        self.hole_descriptions = [h.get("description", "") for h in DEFAULT_COURSES["Wing Point"]]
        # If the DB is empty (first run), do NOT auto-populate players or state
        if not hasattr(self, 'players') or self.players is None:
            self.players = []
            self.current_hole = None
            self.hitting_order = []
            self.captain_id = None
            self.teams = {}
            self.base_wager = 1
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
        self.players: List[Dict] = [dict(player) for player in DEFAULT_PLAYERS]
        self.current_hole: int = 1
        self.hitting_order: List[str] = self._random_order()
        self.captain_id: str = self.hitting_order[0]
        self.teams: Dict = {}
        self.base_wager: int = 1
        self.doubled_status: bool = False
        self.game_phase: str = 'Regular'
        self.hole_scores: Dict[str, int] = {p["id"]: None for p in self.players}
        self.game_status_message: str = "Time to toss the tees!"
        self.player_float_used: Dict[str, bool] = {p["id"]: False for p in self.players}
        self.carry_over: bool = False
        self.hole_history: List[Dict] = []
        self._last_points: Dict[str, int] = {p["id"]: 0 for p in self.players}
        self.hole_stroke_indexes = [h["stroke_index"] for h in DEFAULT_COURSES["Wing Point"]]
        self.hole_pars = [h["par"] for h in DEFAULT_COURSES["Wing Point"]]
        self.hole_yards = [h["yards"] for h in DEFAULT_COURSES["Wing Point"]]
        self.hole_descriptions = [h.get("description", "") for h in DEFAULT_COURSES["Wing Point"]]
        self._save_to_db()

    def _random_order(self) -> List[str]:
        ids = [p["id"] for p in DEFAULT_PLAYERS]
        random.shuffle(ids)
        return ids

    def dispatch_action(self, action, payload):
        if action == "request_partner":
            return self.request_partner(payload.get("captain_id"), payload.get("partner_id"))
        elif action == "accept_partner":
            return self.accept_partner(payload.get("partner_id"))
        elif action == "decline_partner":
            return self.decline_partner(payload.get("partner_id"))
        elif action == "go_solo":
            return self.go_solo(payload.get("captain_id"))
        elif action == "offer_double":
            return self.offer_double(payload.get("offering_team_id"), payload.get("target_team_id"))
        elif action == "accept_double":
            return self.accept_double(payload.get("team_id"))
        elif action == "decline_double":
            return self.decline_double(payload.get("team_id"))
        elif action == "invoke_float":
            return self.invoke_float(payload.get("captain_id"))
        elif action == "toggle_option":
            return self.toggle_option(payload.get("captain_id"))
        elif action == "record_net_score":
            return self.record_net_score(payload.get("player_id"), payload.get("score"))
        elif action == "calculate_hole_points":
            return self.calculate_hole_points()
        elif action == "next_hole":
            return self.next_hole()
        else:
            raise ValueError(f"Unknown action: {action}")

    def request_partner(self, captain_id, partner_id):
        self.game_status_message = f"Captain {self._player_name(captain_id)} requests {self._player_name(partner_id)} as partner. Awaiting response."
        # For MVP, just set teams as pending
        self.teams = {"type": "pending", "captain": captain_id, "requested": partner_id}
        return "Partner requested."

    def accept_partner(self, partner_id):
        # For MVP, finalize teams
        if self.teams.get("type") != "pending" or self.teams.get("requested") != partner_id:
            raise ValueError("No pending partner request for this player.")
        captain_id = self.teams["captain"]
        others = [p["id"] for p in self.players if p["id"] not in [captain_id, partner_id]]
        self.teams = {"type": "partners", "team1": [captain_id, partner_id], "team2": others}
        self.game_status_message = f"{self._player_name(partner_id)} accepted. Teams formed."
        return "Partnership accepted."

    def decline_partner(self, partner_id):
        # For MVP, captain goes solo
        if self.teams.get("type") != "pending" or self.teams.get("requested") != partner_id:
            raise ValueError("No pending partner request for this player.")
        captain_id = self.teams["captain"]
        others = [p["id"] for p in self.players if p["id"] != captain_id]
        self.teams = {"type": "solo", "captain": captain_id, "opponents": others}
        self.base_wager *= 2  # On your own rule
        self.game_status_message = f"{self._player_name(partner_id)} declined. {self._player_name(captain_id)} goes solo! Wager doubled."
        return "Partnership declined. Captain goes solo."

    def go_solo(self, captain_id):
        others = [p["id"] for p in self.players if p["id"] != captain_id]
        self.teams = {"type": "solo", "captain": captain_id, "opponents": others}
        self.base_wager *= 2
        self.game_status_message = f"{self._player_name(captain_id)} goes solo! Wager doubled."
        return "Captain goes solo."

    def offer_double(self, offering_team_id, target_team_id):
        if self.doubled_status:
            raise ValueError("Double already offered or accepted on this hole.")
        self.doubled_status = True
        self.game_status_message = f"Team {offering_team_id} offers to double Team {target_team_id}. Awaiting response."
        return "Double offered."

    def accept_double(self, team_id):
        if not self.doubled_status:
            raise ValueError("No double to accept.")
        self.base_wager *= 2
        self.doubled_status = False
        self.game_status_message = f"Team {team_id} accepted the double. Wager doubled!"
        return "Double accepted."

    def decline_double(self, team_id):
        if not self.doubled_status:
            raise ValueError("No double to decline.")
        self.doubled_status = False
        self.game_status_message = f"Team {team_id} declined the double. Offering team wins at prior stake."
        # For MVP, just set a flag; real logic would award points here
        return "Double declined. Offering team wins hole."

    def invoke_float(self, captain_id):
        if self.player_float_used.get(captain_id):
            raise ValueError("Float already used by this captain.")
        self.base_wager *= 2
        self.player_float_used[captain_id] = True
        self.game_status_message = f"{self._player_name(captain_id)} invoked the float! Wager doubled."
        return "Float invoked."

    def toggle_option(self, captain_id):
        # For MVP, just double wager if captain is eligible
        self.base_wager *= 2
        self.game_status_message = f"{self._player_name(captain_id)} toggled the option. Wager doubled."
        return "Option toggled."

    def record_net_score(self, player_id, score):
        if player_id not in self.hole_scores:
            raise ValueError("Invalid player ID.")
        self.hole_scores[player_id] = score
        self.game_status_message = f"Score recorded for {self._player_name(player_id)}."
        return "Score recorded."

    def calculate_hole_points(self):
        # Ensure all scores are entered
        if any(v is None for v in self.hole_scores.values()):
            raise ValueError("Not all scores entered.")
        if not self.teams or self.teams.get("type") not in ("partners", "solo"):
            raise ValueError("Teams not set for this hole.")
        base = self.base_wager
        msg = ""
        # Determine teams
        if self.teams["type"] == "partners":
            team1 = self.teams["team1"]  # [captain, partner]
            team2 = self.teams["team2"]  # [other1, other2]
            team1_score = min(self.hole_scores[pid] for pid in team1)
            team2_score = min(self.hole_scores[pid] for pid in team2)
            if team1_score < team2_score:
                # team1 wins
                msg = self._distribute_points_karl_marx(winners=team1, losers=team2, base=base)
            elif team2_score < team1_score:
                msg = self._distribute_points_karl_marx(winners=team2, losers=team1, base=base)
            else:
                msg = "Hole halved. No points awarded."
        elif self.teams["type"] == "solo":
            captain = self.teams["captain"]
            opponents = self.teams["opponents"]
            captain_score = self.hole_scores[captain]
            opp_score = min(self.hole_scores[pid] for pid in opponents)
            if captain_score < opp_score:
                # Captain wins against 3
                msg = self._distribute_points_karl_marx(winners=[captain], losers=opponents, base=base)
            elif opp_score < captain_score:
                msg = self._distribute_points_karl_marx(winners=opponents, losers=[captain], base=base)
            else:
                msg = "Hole halved. No points awarded."
        else:
            msg = "Invalid team type for scoring."
        # Record hole history
        points_now = {p["id"]: p["points"] for p in self.players}
        points_delta = {pid: points_now[pid] - self._last_points.get(pid, 0) for pid in points_now}
        self.hole_history.append({
            "hole": self.current_hole,
            "hitting_order": list(self.hitting_order),
            "net_scores": dict(self.hole_scores),
            "points_delta": dict(points_delta),
            "teams": dict(self.teams),
        })
        self._last_points = dict(points_now)
        self.game_status_message = msg
        self._save_to_db()
        return msg

    def _distribute_points_karl_marx(self, winners, losers, base):
        n_win = len(winners)
        n_lose = len(losers)
        total_quarters = base * n_lose
        per_winner = total_quarters // n_win
        odd_quarters = total_quarters % n_win
        # Award base points to all winners
        for p in self.players:
            if p["id"] in winners:
                p["points"] += per_winner
            elif p["id"] in losers:
                p["points"] -= base
        msg = f"{' & '.join(self._player_name(pid) for pid in winners)} win {per_winner} quarter(s) each."
        # Karl Marx rule: assign odd quarter(s) to lowest scorer(s)
        if odd_quarters > 0:
            # Find winner(s) with lowest total points
            winner_points = [(p["id"], p["points"]) for p in self.players if p["id"] in winners]
            min_points = min(points for _, points in winner_points)
            lowest = [pid for pid, points in winner_points if points == min_points]
            if len(lowest) == 1:
                # Assign odd quarter(s) to the lowest
                for p in self.players:
                    if p["id"] == lowest[0]:
                        p["points"] += odd_quarters
                msg += f" Karl Marx rule: {self._player_name(lowest[0])} receives {odd_quarters} extra quarter(s)."
            else:
                msg += f" Karl Marx rule: Odd quarter(s) ({odd_quarters}) in limbo (tie among: {' & '.join(self._player_name(pid) for pid in lowest)})."
        return msg

    def next_hole(self):
        self.current_hole += 1
        # Rotate hitting order
        self.hitting_order = self.hitting_order[1:] + [self.hitting_order[0]]
        self.captain_id = self.hitting_order[0]
        self.teams = {}
        self.doubled_status = False
        self.hole_scores = {p["id"]: None for p in self.players}
        self.game_status_message = f"Hole {self.current_hole}. {self._player_name(self.captain_id)} is captain."
        self._save_to_db()
        return "Advanced to next hole."

    def _player_name(self, pid):
        for p in self.players:
            if p["id"] == pid:
                return p["name"]
        return pid

    def get_hole_history(self):
        return self.hole_history

    def _serialize(self):
        # Return a dict of all stateful fields
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
            "hole_yards": getattr(self, "hole_yards", []),
            "hole_descriptions": getattr(self, "hole_descriptions", []),
            "selected_course": self.selected_course,
            # Event-driven simulation state
            "shot_sequence": getattr(self, "shot_sequence", None),
            "tee_shot_results": getattr(self, "tee_shot_results", None),
        }

    def _deserialize(self, data):
        self.players = data.get("players", [dict(player) for player in DEFAULT_PLAYERS])
        self.current_hole = data.get("current_hole", 1)
        self.hitting_order = data.get("hitting_order", [p["id"] for p in DEFAULT_PLAYERS])
        self.captain_id = data.get("captain_id", self.hitting_order[0])
        self.teams = data.get("teams", {})
        self.base_wager = data.get("base_wager", 1)
        self.doubled_status = data.get("doubled_status", False)
        self.game_phase = data.get("game_phase", 'Regular')
        self.hole_scores = data.get("hole_scores", {p["id"]: None for p in self.players})
        self.game_status_message = data.get("game_status_message", "Time to toss the tees!")
        self.player_float_used = data.get("player_float_used", {p["id"]: False for p in self.players})
        self.carry_over = data.get("carry_over", False)
        self.hole_history = data.get("hole_history", [])
        self._last_points = data.get("_last_points", {p["id"]: 0 for p in self.players})
        self.hole_stroke_indexes = data.get("hole_stroke_indexes", [h["stroke_index"] for h in DEFAULT_COURSES["Wing Point"]])
        self.hole_pars = data.get("hole_pars", [h["par"] for h in DEFAULT_COURSES["Wing Point"]])
        self.hole_yards = data.get("hole_yards", [h["yards"] for h in DEFAULT_COURSES["Wing Point"]])
        self.hole_descriptions = data.get("hole_descriptions", [h.get("description", "") for h in DEFAULT_COURSES["Wing Point"]])
        self.selected_course = data.get("selected_course", None)
        # Event-driven simulation state
        self.shot_sequence = data.get("shot_sequence", None)
        self.tee_shot_results = data.get("tee_shot_results", None)

    def _save_to_db(self):
        """Save the current state as JSON in the DB (id=1) with error handling"""
        try:
            state_json = self._serialize()
            session = self._db_session
            obj = session.query(GameStateModel).get(1)
            if obj:
                obj.state = state_json
            else:
                obj = GameStateModel(id=1, state=state_json)
                session.add(obj)
            session.commit()
        except Exception as e:
            print(f"⚠️ Database save failed: {e}")
            # Continue without saving - this allows the app to work even if DB is down
            pass

    def _load_from_db(self):
        """Load the state from DB if present with error handling"""
        try:
            session = self._db_session
            obj = session.query(GameStateModel).get(1)
            if obj and obj.state:
                self._deserialize(obj.state)
            else:
                self.reset()
        except Exception as e:
            print(f"⚠️ Database load failed: {e}")
            # Fall back to default state if DB is unavailable
            self.reset()

    def get_betting_tips(self):
        tips = []
        # --- Double offered ---
        if self.doubled_status:
            tips.append("A double has been offered. If you're ahead, accepting can increase your winnings, but beware of a comeback! If you're behind, declining gives the other team the hole at the current stake.")
            # Context-aware: compare handicaps
            if self.teams and self.teams.get("type") in ("partners", "solo"):
                tips.extend(self._handicap_context_tips(double_pending=True))
        # --- Opportunity to double back ---
        if self.teams and self.teams.get("type") in ("partners", "solo") and not self.doubled_status:
            tips.append("Consider offering a double if you feel confident in your team's position, or to pressure the opponents.")
            tips.extend(self._handicap_context_tips(double_pending=False))
        # --- Going solo ---
        if self.teams and self.teams.get("type") == "solo":
            tips.append("Going solo doubles the wager, but you must beat the best ball of the other three. Only go solo if you're confident in your shot or need to catch up.")
        # --- Points/momentum ---
        points = [p["points"] for p in self.players]
        max_points = max(points)
        min_points = min(points)
        if max_points - min_points >= 6:
            leader = [p["name"] for p in self.players if p["points"] == max_points][0]
            trailer = [p["name"] for p in self.players if p["points"] == min_points][0]
            tips.append(f"{leader} is ahead by a large margin. Consider playing conservatively to protect your lead, or offer a double to pressure opponents. {trailer}, if you're behind, taking more risks (like going solo or accepting a double) can help you catch up.")
        # --- Float/option usage ---
        unused_floats = [p["name"] for p in self.players if not self.player_float_used.get(p["id"], False)]
        if self.teams and self.teams.get("type") and self.captain_id in [p["id"] for p in self.players]:
            if not self.player_float_used.get(self.captain_id, False):
                tips.append("You haven't used your float yet. Consider saving it for a high-stakes hole or when you're behind.")
            tips.append("The Option can be powerful if you're the captain and have lost the most quarters. Use it to double the wager and turn the tide.")
        # --- Carry-over/high-stakes holes ---
        if self.carry_over:
            tips.append("There's a carry-over in effect. The current hole is worth extra—play aggressively if you need to catch up, or defensively if you're ahead.")
        if self.current_hole >= 13:
            tips.append("On Hoepfinger or double-value holes, consider your risk tolerance before accepting or offering a double.")
        # --- Endgame ---
        if self.current_hole >= 16:
            tips.append("On the final holes, consider the overall standings. Sometimes it's better to lock in a win than risk it all.")
            tips.append("If you're in contention for the Pettit Trophy, play conservatively on the last few holes.")
        # --- Karl Marx rule awareness ---
        if self.teams and self.teams.get("type") in ("partners", "solo"):
            n_win = 2 if self.teams["type"] == "partners" else 1
            n_lose = 2 if self.teams["type"] == "partners" else 3
            total_quarters = self.base_wager * n_lose
            if total_quarters % n_win != 0:
                tips.append("If quarters can't be divided evenly, the Karl Marx rule applies. The player furthest down will owe fewer quarters—factor this into your risk calculations.")
        # --- Psychological/table talk tips ---
        tips.append("If the other team is offering a double, they may be bluffing. Consider their recent performance before accepting.")
        tips.append("Use table talk to gauge your opponents' confidence before making a big bet.")
        # --- General tip ---
        tips.append("Remember: If you decline a double, the offering team wins the hole at the current wager.")
        # --- Hoepfinger phase ---
        if self.current_hole >= 17:
            tips.append("Hoepfinger phase: The player furthest down chooses their spot in the rotation. Strategic position can be crucial!")
        # --- Player strength context ---
        if self.teams and self.teams.get("type") in ("partners", "solo"):
            player_by_id = {p["id"]: p for p in self.players}
            if self.teams["type"] == "partners":
                t1 = self.teams["team1"]
                t2 = self.teams["team2"]
                t1_strengths = [player_by_id[pid].get("strength", "Average") for pid in t1]
                t2_strengths = [player_by_id[pid].get("strength", "Average") for pid in t2]
                if any(s in ("Strong", "Expert") for s in t1_strengths):
                    tips.append("Team 1 has a strong player—consider aggressive betting if the situation allows.")
                if all(s == "Beginner" for s in t1_strengths):
                    tips.append("Team 1 is all beginners—consider caution with doubles or going solo.")
                if any(s in ("Strong", "Expert") for s in t2_strengths):
                    tips.append("Team 2 has a strong player—be cautious if betting against them.")
                if all(s == "Beginner" for s in t2_strengths):
                    tips.append("Team 2 is all beginners—consider aggressive play if you are stronger.")
            elif self.teams["type"] == "solo":
                captain = self.teams["captain"]
                opps = self.teams["opponents"]
                cap_strength = player_by_id[captain].get("strength", "Average")
                opp_strengths = [player_by_id[pid].get("strength", "Average") for pid in opps]
                if cap_strength in ("Strong", "Expert"):
                    tips.append("The captain is strong—going solo or accepting a double may be favorable.")
                if all(s == "Beginner" for s in opp_strengths):
                    tips.append("All opponents are beginners—captain may want to play aggressively.")
        return tips

    def _handicap_context_tips(self, double_pending):
        """
        Returns a list of context-aware tips based on net strokes for the current hole and teams.
        """
        tips = []
        if not self.teams or self.teams.get("type") not in ("partners", "solo"):
            return tips
        player_by_id = {p["id"]: p for p in self.players}
        strokes = self.get_player_strokes()  # {player_id: {hole_number: stroke_type}}
        hole = self.current_hole
        # For each player, get strokes for this hole
        net_strokes = {pid: strokes[pid][hole] for pid in strokes}
        if self.teams["type"] == "partners":
            t1 = self.teams["team1"]
            t2 = self.teams["team2"]
            # For each team, best net advantage (lowest gross - strokes)
            t1_strokes = [net_strokes[pid] for pid in t1]
            t2_strokes = [net_strokes[pid] for pid in t2]
            t1_hcap = sum(player_by_id[pid]["handicap"] for pid in t1)
            t2_hcap = sum(player_by_id[pid]["handicap"] for pid in t2)
            t1_min = min(t1_strokes)
            t2_min = min(t2_strokes)
            net_diff = t2_min - t1_min  # positive: team1 net advantage
            if abs(net_diff) >= 1:
                if net_diff > 0:
                    tips.append(f"On this hole, Team 1 receives {abs(net_diff):.1f} more net strokes than Team 2. This is a favorable hole for Team 1.")
                else:
                    tips.append(f"On this hole, Team 2 receives {abs(net_diff):.1f} more net strokes than Team 1. This is a favorable hole for Team 2.")
            elif abs(t1_hcap - t2_hcap) >= 6:
                # fallback to overall handicap if net is close
                if t1_hcap < t2_hcap:
                    tips.append(f"Team 1 (avg handicap {t1_hcap/2:.1f}) is much stronger overall, but this hole is even on net strokes.")
                else:
                    tips.append(f"Team 2 (avg handicap {t2_hcap/2:.1f}) is much stronger overall, but this hole is even on net strokes.")
        elif self.teams["type"] == "solo":
            captain = self.teams["captain"]
            opps = self.teams["opponents"]
            cap_stroke = net_strokes[captain]
            opp_strokes = [net_strokes[pid] for pid in opps]
            opp_min = min(opp_strokes)
            net_diff = opp_min - cap_stroke
            cap_hcap = player_by_id[captain]["handicap"]
            opp_hcap = sum(player_by_id[pid]["handicap"] for pid in opps) / len(opps)
            if abs(net_diff) >= 1:
                if net_diff > 0:
                    tips.append(f"On this hole, the captain receives {abs(net_diff):.1f} more net strokes than the best opponent. Favorable for the captain.")
                else:
                    tips.append(f"On this hole, the opponents receive {abs(net_diff):.1f} more net strokes than the captain. Favorable for the opponents.")
            elif abs(cap_hcap - opp_hcap) >= 4:
                if cap_hcap < opp_hcap:
                    tips.append(f"Captain (handicap {cap_hcap}) is much stronger overall, but this hole is even on net strokes.")
                else:
                    tips.append(f"Opponents (avg handicap {opp_hcap:.1f}) are much stronger overall, but this hole is even on net strokes.")
        return tips

    def get_player_strokes(self):
        """
        Returns a dict: {player_id: {hole_number: stroke_type}}, where stroke_type is 1 (full stroke), 0.5 (half), or 0 (none)
        """
        n_holes = len(self.hole_stroke_indexes)
        result = {}
        for player in self.players:
            pid = player["id"]
            hcap = float(player.get("handicap", 0))
            strokes = {i+1: 0 for i in range(n_holes)}
            full_strokes = int(hcap)
            half_stroke = (hcap - full_strokes) >= 0.5
            # Full strokes
            for i, idx in enumerate(self.hole_stroke_indexes):
                if idx <= full_strokes:
                    strokes[i+1] = 1
            # If handicap > n_holes, assign extra strokes (second stroke) to lowest index holes
            if full_strokes > n_holes:
                extra = full_strokes - n_holes
                hardest = sorted(range(n_holes), key=lambda i: self.hole_stroke_indexes[i])[:extra]
                for i in hardest:
                    strokes[i+1] += 1
            # Half stroke: assign to next hardest hole
            if half_stroke:
                # Find the next hardest hole not already getting an extra stroke
                eligible = sorted([(i, self.hole_stroke_indexes[i]) for i in range(n_holes) if strokes[i+1] == 0], key=lambda x: x[1])
                if eligible:
                    strokes[eligible[0][0]+1] = 0.5
            result[pid] = strokes
        return result

    def setup_players(self, players: list[dict], course_name: str = None):
        """
        Set custom players (id, name, handicap, strength) and reset the game state. Optionally set course.
        """
        if len(players) != 4:
            raise ValueError("Exactly 4 players required.")
        for p in players:
            if not all(k in p for k in ("id", "name", "handicap", "strength")):
                raise ValueError("Each player must have id, name, handicap, and strength.")
        self.reset()  # <-- This ensures ALL state is cleared!
        self.players = [dict(id=p["id"], name=p["name"], points=0, handicap=float(p["handicap"]), strength=p["strength"]) for p in players]
        self.current_hole = 1
        self.hitting_order = [p["id"] for p in self.players]
        random.shuffle(self.hitting_order)
        self.captain_id = self.hitting_order[0]
        self.teams = {}
        self.base_wager = 1
        self.doubled_status = False
        self.game_phase = 'Regular'
        self.hole_scores = {p["id"]: None for p in self.players}
        self.game_status_message = "Players set. Time to toss the tees!"
        self.player_float_used = {p["id"]: False for p in self.players}
        self.carry_over = False
        self.hole_history = []
        self._last_points = {p["id"]: 0 for p in self.players}
        if course_name and course_name in self.courses:
            course = self.courses[course_name]
            self.selected_course = course_name
            self.hole_stroke_indexes = [h["stroke_index"] for h in course]
            self.hole_pars = [h["par"] for h in course]
            self.hole_yards = [h["yards"] for h in course]
            self.hole_descriptions = [h.get("description", "") for h in course]
        else:
            self.selected_course = None
            self.hole_stroke_indexes = [h["stroke_index"] for h in DEFAULT_COURSES["Wing Point"]]
            self.hole_pars = [h["par"] for h in DEFAULT_COURSES["Wing Point"]]
            self.hole_yards = [h["yards"] for h in DEFAULT_COURSES["Wing Point"]]
            self.hole_descriptions = [h.get("description", "") for h in DEFAULT_COURSES["Wing Point"]]
        self._save_to_db()

    def get_courses(self):
        return self.courses

    def add_course(self, course_data):
        """Add a new course with validation"""
        name = course_data["name"]
        if name in self.courses:
            raise ValueError(f"Course '{name}' already exists")
        
        holes = course_data["holes"]
        if len(holes) != 18:
            raise ValueError("Course must have exactly 18 holes")
        
        # Validate hole data
        for hole in holes:
            if not all(k in hole for k in ["hole_number", "par", "yards", "stroke_index"]):
                raise ValueError("Each hole must have hole_number, par, yards, and stroke_index")
        
        # Check for unique handicaps and hole numbers
        handicaps = [h["stroke_index"] for h in holes]
        hole_numbers = [h["hole_number"] for h in holes]
        
        if len(set(handicaps)) != 18 or set(handicaps) != set(range(1, 19)):
            raise ValueError("Stroke indexes must be unique and range from 1 to 18")
        
        if len(set(hole_numbers)) != 18 or set(hole_numbers) != set(range(1, 19)):
            raise ValueError("Hole numbers must be unique and range from 1 to 18")
        
        # Sort holes by hole number for consistency
        sorted_holes = sorted(holes, key=lambda h: h["hole_number"])
        self.courses[name] = sorted_holes
        return True

    def delete_course(self, course_name):
        """Delete a course"""
        if course_name not in self.courses:
            raise ValueError(f"Course '{course_name}' not found")
        
        # If this was the selected course, reset to default
        if self.selected_course == course_name:
            self.selected_course = None
            self.hole_stroke_indexes = [h["stroke_index"] for h in DEFAULT_COURSES["Wing Point"]]
            self.hole_pars = [h["par"] for h in DEFAULT_COURSES["Wing Point"]]
            self.hole_yards = [h["yards"] for h in DEFAULT_COURSES["Wing Point"]]
            self.hole_descriptions = [h.get("description", "") for h in DEFAULT_COURSES["Wing Point"]]
        
        del self.courses[course_name]
        return True

    def update_course(self, course_name, course_data):
        """Update an existing course"""
        if course_name not in self.courses:
            raise ValueError(f"Course '{course_name}' not found")
        
        # If renaming, check new name doesn't exist
        new_name = course_data.get("name", course_name)
        if new_name != course_name and new_name in self.courses:
            raise ValueError(f"Course '{new_name}' already exists")
        
        # Update course data
        if "holes" in course_data:
            holes = course_data["holes"]
            if len(holes) != 18:
                raise ValueError("Course must have exactly 18 holes")
            
            # Validate as in add_course
            handicaps = [h["stroke_index"] for h in holes]
            hole_numbers = [h["hole_number"] for h in holes]
            
            if len(set(handicaps)) != 18 or set(handicaps) != set(range(1, 19)):
                raise ValueError("Stroke indexes must be unique and range from 1 to 18")
            
            if len(set(hole_numbers)) != 18 or set(hole_numbers) != set(range(1, 19)):
                raise ValueError("Hole numbers must be unique and range from 1 to 18")
            
            sorted_holes = sorted(holes, key=lambda h: h["hole_number"])
            
            # If renaming, delete old and add new
            if new_name != course_name:
                del self.courses[course_name]
                self.courses[new_name] = sorted_holes
                # Update selected course if it was this one
                if self.selected_course == course_name:
                    self.selected_course = new_name
            else:
                self.courses[course_name] = sorted_holes
            
            # If this is the currently selected course, update game state
            if self.selected_course in [course_name, new_name]:
                self.hole_stroke_indexes = [h["stroke_index"] for h in sorted_holes]
                self.hole_pars = [h["par"] for h in sorted_holes]
                self.hole_yards = [h["yards"] for h in sorted_holes]
                self.hole_descriptions = [h.get("description", "") for h in sorted_holes]
        
        return True

    def get_course_stats(self, course_name):
        """Get statistics for a course"""
        if course_name not in self.courses:
            raise ValueError(f"Course '{course_name}' not found")
        
        course = self.courses[course_name]
        total_par = sum(h["par"] for h in course)
        total_yards = sum(h["yards"] for h in course)
        
        par_counts = {3: 0, 4: 0, 5: 0, 6: 0}
        for hole in course:
            par_counts[hole["par"]] += 1
        
        longest_hole = max(course, key=lambda h: h["yards"])
        shortest_hole = min(course, key=lambda h: h["yards"])
        
        # Calculate difficulty rating based on yards and par
        difficulty_score = 0
        for hole in course:
            # Higher difficulty for longer holes and harder stroke indexes
            yard_factor = hole["yards"] / (hole["par"] * 100)  # Normalize by par
            stroke_factor = (19 - hole["stroke_index"]) / 18  # Lower stroke index = harder
            difficulty_score += yard_factor * stroke_factor
        
        return {
            "total_par": total_par,
            "total_yards": total_yards,
            "par_3_count": par_counts[3],
            "par_4_count": par_counts[4], 
            "par_5_count": par_counts[5],
            "par_6_count": par_counts[6],
            "average_yards_per_hole": total_yards / 18,
            "longest_hole": longest_hole,
            "shortest_hole": shortest_hole,
            "difficulty_rating": round(difficulty_score, 2)
        }

    def get_current_hole_info(self):
        """Get detailed information about the current hole"""
        if not hasattr(self, 'current_hole') or self.current_hole is None:
            return None
        
        hole_idx = self.current_hole - 1
        if hole_idx < 0 or hole_idx >= len(self.hole_pars):
            return None
        
        return {
            "hole_number": self.current_hole,
            "par": self.hole_pars[hole_idx],
            "yards": self.hole_yards[hole_idx] if hasattr(self, 'hole_yards') else None,
            "stroke_index": self.hole_stroke_indexes[hole_idx],
            "description": self.hole_descriptions[hole_idx] if hasattr(self, 'hole_descriptions') else "",
            "selected_course": self.selected_course
        }

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

# Singleton game state for MVP (in-memory)
game_state = GameState() 