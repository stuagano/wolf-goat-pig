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

# Singleton game state for MVP (in-memory)
game_state = GameState() 