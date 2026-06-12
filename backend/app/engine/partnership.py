"""Partnership mechanics for WolfGoatPigGame — captain/partner requests and resolution."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PartnershipMixin:
    """Captain/partner formation: requests, accept/decline, eligibility."""

    def _check_partnership_requests(self, human_player_id: str) -> list[dict[str, Any]]:
        """Check if any computer players want to request the human as partner"""
        self.hole_states[self.current_hole]
        requests = []

        for player in self.players:
            if player.id != human_player_id and player.id in self.computer_players:
                computer_player = self.computer_players[player.id]

                # Check if computer player wants to request human as partner
                if computer_player.should_request_partner(human_player_id, self.get_game_state()):
                    requests.append(
                        {
                            "requesting_player": player.id,
                            "requesting_player_name": player.name,
                            "target_player": human_player_id,
                            "message": f"{player.name} wants you as a partner!",
                        }
                    )

        return requests

    def _get_available_partners(self, human_player_id: str) -> list[dict[str, Any]]:
        """Get list of players the human can request as partners"""
        hole_state = self.hole_states[self.current_hole]
        available = []

        for player in self.players:
            if player.id != human_player_id:
                # Check if player is still eligible for partnership
                if self._is_player_eligible_for_partnership(player.id, hole_state):
                    available.append(
                        {
                            "player_id": player.id,
                            "player_name": player.name,
                            "handicap": player.handicap,
                            "is_computer": player.id in self.computer_players,
                        }
                    )

        return available
