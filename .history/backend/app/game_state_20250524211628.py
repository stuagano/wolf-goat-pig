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