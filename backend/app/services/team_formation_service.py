"""
Random team formation service for creating balanced 4-player groups from daily signups.
Handles scenarios where more than 4 players are signed up for a given day.
"""

import logging
from random import Random, SystemRandom

from ..utils.time import utc_now

logger = logging.getLogger(__name__)


class TeamFormationService:
    """Service for creating random team formations from daily signups."""

    @staticmethod
    def generate_random_teams(
        players: list[dict],
        seed: int | None = None,
        max_teams: int | None = None,
        rng: Random | None = None,
    ) -> list[dict]:
        """
        Generate random 4-player teams from a list of signed-up players.

        Args:
            players: List of player dictionaries with player info
            seed: Optional random seed for reproducible results
            max_teams: Maximum number of teams to create (default: all possible)

        Returns:
            List of team dictionaries with 4 players each
        """
        if len(players) < 4:
            logger.warning(f"Not enough players for team formation: {len(players)} < 4")
            return []

        # Build a local random number generator so we don't mutate global state
        if rng is not None:
            local_rng = rng
        elif seed is not None:
            local_rng = Random(seed)
        else:
            system_seed = SystemRandom().randrange(0, 2**32)
            local_rng = Random(system_seed)

        # Create a copy to avoid modifying original list
        available_players = players.copy()
        local_rng.shuffle(available_players)

        teams = []
        team_number = 1

        # Create teams of 4 players
        while len(available_players) >= 4:
            team_players = available_players[:4]
            available_players = available_players[4:]

            team = {
                "team_id": team_number,
                "players": team_players,
                "created_at": utc_now().isoformat(),
                "formation_method": "random",
            }
            teams.append(team)
            team_number += 1

            # Check if we've reached max teams limit
            if max_teams and len(teams) >= max_teams:
                break

        # Log remaining players who couldn't form a complete team
        if available_players:
            logger.info(f"Remaining players not assigned to teams: {len(available_players)}")

        return teams
