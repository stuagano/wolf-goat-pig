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
        # Determine teams
        if self.teams["type"] == "partners":
            team1 = self.teams["team1"]  # [captain, partner]
            team2 = self.teams["team2"]  # [other1, other2]
            team1_score = min(self.hole_scores[pid] for pid in team1)
            team2_score = min(self.hole_scores[pid] for pid in team2)
            if team1_score < team2_score:
                # team1 wins
                for p in self.players:
                    if p["id"] in team1:
                        p["points"] += base
                    else:
                        p["points"] -= base
                msg = f"Team {self._player_name(team1[0])} & {self._player_name(team1[1])} win {base} quarter(s) each."
            elif team2_score < team1_score:
                for p in self.players:
                    if p["id"] in team2:
                        p["points"] += base
                    else:
                        p["points"] -= base
                msg = f"Team {self._player_name(team2[0])} & {self._player_name(team2[1])} win {base} quarter(s) each."
            else:
                msg = "Hole halved. No points awarded."
        elif self.teams["type"] == "solo":
            captain = self.teams["captain"]
            opponents = self.teams["opponents"]
            captain_score = self.hole_scores[captain]
            opp_score = min(self.hole_scores[pid] for pid in opponents)
            # On your own: wager is already doubled
            if captain_score < opp_score:
                # Captain wins against 3
                for p in self.players:
                    if p["id"] == captain:
                        p["points"] += base * 3
                    else:
                        p["points"] -= base
                msg = f"{self._player_name(captain)} goes solo and wins {base*3} quarters!"
            elif opp_score < captain_score:
                for p in self.players:
                    if p["id"] == captain:
                        p["points"] -= base * 3
                    else:
                        p["points"] += base
                msg = f"Opponents win {base} quarter(s) each from {self._player_name(captain)}."
            else:
                msg = "Hole halved. No points awarded."
        else:
            msg = "Invalid team type for scoring."
        self.game_status_message = msg
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

# Singleton game state for MVP (in-memory)
game_state = GameState() 