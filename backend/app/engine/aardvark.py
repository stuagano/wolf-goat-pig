"""Aardvark mechanics for WolfGoatPigGame — 5/6-player 5th-wheel team joining and tosses."""

import random
from typing import Any

from ..domain.game_types import HoleState, TeamFormation


class AardvarkMixin:
    """Aardvark (5th/6th player) team requests, acceptance, tosses, and ping-pong."""

    def aardvark_request_team(self, aardvark_id: str, target_team: str) -> dict[str, Any]:
        """Aardvark requests to join a team (5-man and 6-man games)"""
        if self.player_count == 4:
            raise ValueError("No aardvark in 4-man game")

        hole_state = self.hole_states[self.current_hole]

        # Validate aardvark status
        if not self._is_aardvark(aardvark_id, hole_state):
            raise ValueError("Player is not an aardvark on this hole")

        # Set pending aardvark request
        hole_state.teams.pending_request = {
            "type": "aardvark",
            "aardvark": aardvark_id,
            "target_team": target_team,
        }

        return {
            "status": "pending",
            "message": f"Aardvark {self._get_player_name(aardvark_id)} requests to join {target_team}",
            "awaiting_response": target_team,
        }

    def respond_to_aardvark(self, team_id: str, accept: bool) -> dict[str, Any]:
        """Respond to aardvark request"""
        hole_state = self.hole_states[self.current_hole]

        pending = hole_state.teams.pending_request
        if not pending or pending.get("type") != "aardvark":
            raise ValueError("No pending aardvark request")

        aardvark_id = pending["aardvark"]

        if accept:
            return self._accept_aardvark(aardvark_id, team_id, hole_state)
        return self._toss_aardvark(aardvark_id, team_id, hole_state)

    def aardvark_go_solo(self, aardvark_id: str, use_tunkarri: bool = False) -> dict[str, Any]:
        """Aardvark decides to go solo (5-man and 6-man games)"""
        if self.player_count == 4:
            raise ValueError("No aardvark in 4-man game")

        hole_state = self.hole_states[self.current_hole]

        if not self._is_aardvark(aardvark_id, hole_state):
            raise ValueError("Player is not an aardvark on this hole")

        # Set up aardvark solo play
        others = [p.id for p in self.players if p.id != aardvark_id]
        hole_state.teams = TeamFormation(type="solo", solo_player=aardvark_id, opponents=others)

        # Apply wager multipliers
        multiplier = 2  # Base solo multiplier

        if use_tunkarri:
            # The Tunkarri: 3 quarters for every 2 wagered
            hole_state.betting.tunkarri_invoked = True
            multiplier = 2  # Still doubles the base wager

        hole_state.betting.current_wager *= multiplier

        return {
            "status": "solo",
            "message": f"Aardvark {self._get_player_name(aardvark_id)} goes solo!",
            "tunkarri": use_tunkarri,
            "wager": hole_state.betting.current_wager,
        }

    def _is_aardvark(self, player_id: str, hole_state: HoleState) -> bool:
        """Check if player is an aardvark on this hole"""
        if self.player_count == 4:
            return False  # No aardvark in 4-man game (only invisible)
        if self.player_count == 5:
            return hole_state.hitting_order.index(player_id) == 4  # 5th position
        # 6-man
        index = hole_state.hitting_order.index(player_id)
        return index in [4, 5]  # 5th or 6th position

    def _accept_aardvark(self, aardvark_id: str, team_id: str, hole_state: HoleState) -> dict[str, Any]:
        """Handle aardvark acceptance to team"""
        # Add aardvark to the specified team
        if team_id == "team1":
            hole_state.teams.team1.append(aardvark_id)
        elif team_id == "team2":
            hole_state.teams.team2.append(aardvark_id)
        else:
            raise ValueError("Invalid team ID")

        hole_state.teams.pending_request = None

        return {
            "status": "aardvark_accepted",
            "message": f"Aardvark {self._get_player_name(aardvark_id)} joins {team_id}",
            "teams": {"team1": hole_state.teams.team1, "team2": hole_state.teams.team2},
        }

    def _toss_aardvark(self, aardvark_id: str, rejecting_team: str, hole_state: HoleState) -> dict[str, Any]:
        """Handle aardvark being tossed to other team"""
        # Add to tossed list
        hole_state.betting.tossed_aardvarks.append(aardvark_id)

        # Double the wager
        hole_state.betting.current_wager *= 2

        # Add aardvark to the other team
        other_team = "team2" if rejecting_team == "team1" else "team1"
        if other_team == "team1":
            hole_state.teams.team1.append(aardvark_id)
        else:
            hole_state.teams.team2.append(aardvark_id)

        hole_state.teams.pending_request = None

        return {
            "status": "aardvark_tossed",
            "message": f"Aardvark {self._get_player_name(aardvark_id)} tossed to {other_team}",
            "new_wager": hole_state.betting.current_wager,
            "teams": {"team1": hole_state.teams.team1, "team2": hole_state.teams.team2},
        }

    def ping_pong_aardvark(self, team_id: str, aardvark_id: str) -> dict[str, Any]:
        """
        Ping Pong the Aardvark: Team can re-toss an Aardvark, doubling the bet again
        A team cannot toss the same Aardvark twice on the same hole
        """
        hole_state = self.hole_states[self.current_hole]

        # Check if this aardvark was already tossed to this team
        if aardvark_id in hole_state.betting.tossed_aardvarks:
            raise ValueError("Cannot ping pong the same Aardvark twice on the same hole")

        # Add to tossed list
        hole_state.betting.tossed_aardvarks.append(aardvark_id)
        hole_state.betting.ping_pong_count += 1

        # Double the bet again
        hole_state.betting.current_wager *= 2

        # Determine where the aardvark goes next
        available_teams = [t for t in ["team1", "team2", "team3"] if t != team_id]
        if available_teams:
            next_team = random.choice(available_teams)

            return {
                "status": "aardvark_ping_ponged",
                "message": f"Aardvark {self._get_player_name(aardvark_id)} ping ponged to {next_team}! Wager doubled to {hole_state.betting.current_wager}.",
                "new_wager": hole_state.betting.current_wager,
                "ping_pong_count": hole_state.betting.ping_pong_count,
                "aardvark_destination": next_team,
            }
        return {
            "status": "aardvark_stuck",
            "message": f"No more teams available! Aardvark {self._get_player_name(aardvark_id)} must stay.",
            "new_wager": hole_state.betting.current_wager,
        }
