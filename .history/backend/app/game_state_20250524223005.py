from typing import List, Dict
import random

# Default player names for MVP
DEFAULT_PLAYERS = [
    {"id": "p1", "name": "Bob", "points": 0},
    {"id": "p2", "name": "Scott", "points": 0},
    {"id": "p3", "name": "Vince", "points": 0},
    {"id": "p4", "name": "Mike", "points": 0},
]

class GameState:
    def __init__(self):
        self.reset()

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
        return "Advanced to next hole."

    def _player_name(self, pid):
        for p in self.players:
            if p["id"] == pid:
                return p["name"]
        return pid

    def get_hole_history(self):
        return self.hole_history

# Singleton game state for MVP (in-memory)
game_state = GameState() 