from typing import List, Dict
import random
import json
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import GameStateModel

# Default player names for MVP
DEFAULT_PLAYERS = [
    {"id": "p1", "name": "Bob", "points": 0, "handicap": 10.5},
    {"id": "p2", "name": "Scott", "points": 0, "handicap": 15},
    {"id": "p3", "name": "Vince", "points": 0, "handicap": 8},
    {"id": "p4", "name": "Mike", "points": 0, "handicap": 20.5},
]

# Example stroke index for 18 holes (1 = hardest, 18 = easiest)
DEFAULT_HOLE_STROKE_INDEXES = [1, 15, 7, 13, 3, 17, 9, 11, 5, 2, 16, 8, 14, 4, 18, 10, 12, 6]

class GameState:
    def __init__(self):
        self._db_session = SessionLocal()
        self._load_from_db()
        self.hole_stroke_indexes = list(DEFAULT_HOLE_STROKE_INDEXES)

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
        self.hole_stroke_indexes = list(DEFAULT_HOLE_STROKE_INDEXES)
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
        self.hole_stroke_indexes = data.get("hole_stroke_indexes", list(DEFAULT_HOLE_STROKE_INDEXES))

    def _save_to_db(self):
        # Save the current state as JSON in the DB (id=1)
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
        # Load the state from DB if present
        session = self._db_session
        obj = session.query(GameStateModel).get(1)
        if obj and obj.state:
            self._deserialize(obj.state)
        else:
            self.reset()

    def get_betting_tips(self):
        tips = []
        # --- Double offered ---
        if self.doubled_status:
            tips.append("A double has been offered. If you're ahead, accepting can increase your winnings, but beware of a comeback! If you're behind, declining gives the other team the hole at the current stake.")
        # --- Opportunity to double back ---
        if self.teams and self.teams.get("type") in ("partners", "solo") and not self.doubled_status:
            tips.append("Consider offering a double if you feel confident in your team's position, or to pressure the opponents.")
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

# Singleton game state for MVP (in-memory)
game_state = GameState() 