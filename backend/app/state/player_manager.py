from typing import List, Dict, Optional
from backend.app.domain.player import Player

class PlayerManager:
    """
    Manages players, hitting order, and captain rotation for the game.
    Extracted from GameState for single responsibility.
    """
    def __init__(self, players: Optional[List[Player]] = None):
        self.players: List[Player] = players if players is not None else []
        self.hitting_order: List[str] = [p.id for p in self.players] if self.players else []
        self.captain_id: Optional[str] = self.hitting_order[0] if self.hitting_order else None

    def setup_players(self, players: List[Player]):
        if len(players) != 4:
            raise ValueError("Exactly 4 players required.")
        self.players = players
        self.hitting_order = [p.id for p in players]
        self.captain_id = self.hitting_order[0]

    def rotate_captain(self):
        if not self.hitting_order:
            return
        self.hitting_order = self.hitting_order[1:] + [self.hitting_order[0]]
        self.captain_id = self.hitting_order[0]

    def get_player_by_id(self, player_id: str) -> Optional[Player]:
        for player in self.players:
            if player.id == player_id:
                return player
        return None

    def to_dict(self) -> Dict:
        return {
            "players": [p.to_dict() for p in self.players],
            "hitting_order": list(self.hitting_order),
            "captain_id": self.captain_id
        }

    def from_dict(self, data: Dict):
        self.players = [Player.from_dict(p) for p in data.get("players", [])]
        self.hitting_order = data.get("hitting_order", [p.id for p in self.players])
        self.captain_id = data.get("captain_id", self.hitting_order[0] if self.hitting_order else None)

    def __repr__(self):
        return f"PlayerManager(players={len(self.players)}, captain_id={self.captain_id})" 