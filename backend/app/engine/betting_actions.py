"""Betting actions for WolfGoatPigGame — doubles, the Float, Big Dick, Ackerley's Gambit."""

import logging
from typing import Any, cast

from ..domain.game_types import HoleState, TeamFormation
from ..validators import BettingValidationError, BettingValidator

logger = logging.getLogger(__name__)


class BettingActionsMixin:
    """Wager escalation: doubles (incl. Ackerley's Gambit), the Float, Big Dick."""

    def offer_double(self, offering_player_id: str, target_team: str | None = None) -> dict[str, Any]:
        """Offer a double to the opposing team"""
        hole_state = self.hole_states[self.current_hole]

        # Validate double using BettingValidator
        try:
            partnership_formed = hole_state.teams.type in ["partners", "solo"]
            BettingValidator.validate_double(
                already_doubled=hole_state.betting.doubled,
                wagering_closed=hole_state.wagering_closed,
                partnership_formed=partnership_formed,
            )
        except BettingValidationError as e:
            logger.error(f"Double validation failed: {e.message}")
            raise ValueError(f"Cannot offer double: {e.message}") from e

        # Check Line of Scrimmage rule - use the proper can_offer_double method
        if not hole_state.can_offer_double(offering_player_id):
            raise ValueError("Cannot offer double - player has passed line of scrimmage or betting is closed")

        # Check if any ball is in the hole
        if hole_state.balls_in_hole:
            raise ValueError("Cannot offer double - ball is in the hole")

        # Record double offer
        hole_state.betting.doubles_history.append(
            {
                "offering_player": offering_player_id,
                "target_team": target_team,
                "wager_before": hole_state.betting.current_wager,
            }
        )

        hole_state.betting.doubled = True

        # Add double offer event to timeline
        offering_player_name = self._get_player_name(offering_player_id)
        if self.hole_progression is not None:
            self.hole_progression.add_timeline_event(
                event_type="double_offer",
                description=f"{offering_player_name} offers a double - wager increases from {hole_state.betting.current_wager} to {hole_state.betting.current_wager * 2} quarters",
                player_id=offering_player_id,
                player_name=offering_player_name,
                details={
                    "offering_player": offering_player_name,
                    "current_wager": hole_state.betting.current_wager,
                    "potential_wager": hole_state.betting.current_wager * 2,
                    "hole_number": self.current_hole,
                },
            )

        return {
            "status": "double_offered",
            "message": f"{offering_player_name} offers a double",
            "current_wager": hole_state.betting.current_wager,
            "potential_wager": hole_state.betting.current_wager * 2,
        }

    def respond_to_double(
        self,
        responding_team: str,
        accept: bool,
        gambit_players: list[str] | None = None,
    ) -> dict[str, Any]:
        """Respond to a double offer, with optional Ackerley's Gambit"""
        hole_state = self.hole_states[self.current_hole]

        if not hole_state.betting.doubled:
            raise ValueError("No double to respond to")

        if accept:
            if gambit_players:
                # Ackerley's Gambit: some players opt out, others stay in
                return self._handle_ackerley_gambit(responding_team, gambit_players, hole_state)
            # Standard double acceptance
            hole_state.betting.current_wager *= 2
            hole_state.betting.doubled = False

            # Add double acceptance event to timeline
            if self.hole_progression is not None:
                self.hole_progression.add_timeline_event(
                    event_type="double_response",
                    description=f"Double accepted - wager increases to {hole_state.betting.current_wager} quarters",
                    details={
                        "accepted": True,
                        "new_wager": hole_state.betting.current_wager,
                        "responding_team": responding_team,
                    },
                )

            return {
                "status": "double_accepted",
                "message": "Double accepted",
                "new_wager": hole_state.betting.current_wager,
            }
        # Double declined - offering team wins hole
        return self._resolve_double_decline(hole_state)

    def invoke_float(self, captain_id: str) -> dict[str, Any]:
        """Captain invokes The Float to increase base wager"""
        captain = next(p for p in self.players if p.id == captain_id)
        hole_state = self.hole_states[self.current_hole]

        if captain.float_used:
            raise ValueError("Player has already used their float this round")

        if hole_state.teams.captain != captain_id:
            raise ValueError("Only the captain can invoke the float")

        # Apply float
        captain.float_used = True
        hole_state.betting.float_invoked = True
        hole_state.betting.current_wager *= 2

        return {
            "status": "float_invoked",
            "message": f"{captain.name} invokes The Float",
            "new_wager": hole_state.betting.current_wager,
        }

    def _handle_ackerley_gambit(
        self, responding_team: str, gambit_players: list[str], hole_state: HoleState
    ) -> dict[str, Any]:
        """Handle Ackerley's Gambit - some players opt out, others stay in"""
        opt_out_players = [p for p in gambit_players if p not in gambit_players]
        opt_in_players = gambit_players

        # Opt-out players forfeit their current quarters at risk
        hole_state.betting.ackerley_gambit = {
            "opt_out": opt_out_players,
            "opt_in": opt_in_players,
        }

        # Double the wager for opt-in players
        hole_state.betting.current_wager *= 2
        hole_state.betting.doubled = False

        return {
            "status": "ackerley_gambit",
            "message": "Ackerley's Gambit invoked",
            "opt_out_players": opt_out_players,
            "opt_in_players": opt_in_players,
            "new_wager": hole_state.betting.current_wager,
        }

    def _resolve_double_decline(self, hole_state: HoleState) -> dict[str, Any]:
        """Handle double decline - offering team wins hole"""
        hole_state.betting.doubled = False

        # Determine offering team from doubles history
        last_double = hole_state.betting.doubles_history[-1]
        offering_player = last_double["offering_player"]

        # Add double decline event to timeline
        offering_player_name = self._get_player_name(offering_player)
        if self.hole_progression is not None:
            self.hole_progression.add_timeline_event(
                event_type="double_response",
                description=f"Double declined - {offering_player_name}'s team wins the hole",
                player_id=offering_player,
                player_name=offering_player_name,
                details={
                    "accepted": False,
                    "offering_player": offering_player_name,
                    "wager": last_double["wager_before"],
                    "hole_winner": "offering_team",
                },
            )

        # Award points to offering team
        points_result = {
            "status": "double_declined",
            "message": "Double declined. Offering team wins hole.",
            "hole_winner": "offering_team",
            "points_changes": {},
        }

        # Calculate points based on team structure
        wager = last_double["wager_before"]

        if hole_state.teams.type == "partners":
            # Determine which team the offering player is on
            if offering_player in hole_state.teams.team1:
                winners = hole_state.teams.team1
                losers = hole_state.teams.team2
            else:
                winners = hole_state.teams.team2
                losers = hole_state.teams.team1

            # Distribute points using Karl Marx rule
            points_changes = self._apply_karl_marx_rule(winners, losers, wager)
            points_result["points_changes"] = points_changes

        elif hole_state.teams.type == "solo":
            if offering_player == hole_state.teams.solo_player:
                # Solo player wins
                points_changes_dict = cast("dict[str, int]", points_result["points_changes"])
                points_changes_dict[offering_player] = wager * len(hole_state.teams.opponents)
                for opp in hole_state.teams.opponents:
                    points_changes_dict[opp] = -wager
            else:
                # Opponents win
                points_changes_dict = cast("dict[str, int]", points_result["points_changes"])
                solo_player_id = hole_state.teams.solo_player
                if solo_player_id:
                    points_changes_dict[solo_player_id] = -wager * len(hole_state.teams.opponents)
                for opp in hole_state.teams.opponents:
                    points_changes_dict[opp] = wager

        return points_result

    def offer_big_dick(self, player_id: str) -> dict[str, Any]:
        """
        The Big Dick: Player with most points can risk all winnings on hole 18
        Others must unanimously accept or individual players can use Ackerley's Gambit
        """
        if self.current_hole != 18:
            raise ValueError("Big Dick can only be offered on hole 18")

        player = next(p for p in self.players if p.id == player_id)

        # Must be the player with the most points
        max_points = max(p.points for p in self.players)
        if player.points != max_points or max_points <= 0:
            raise ValueError("Big Dick can only be offered by player with most points (and positive points)")

        hole_state = self.hole_states[self.current_hole]
        hole_state.betting.big_dick_invoked = True

        # Set up the challenge
        big_dick_wager = abs(player.points)  # Risk all winnings

        return {
            "status": "big_dick_offered",
            "challenger": player_id,
            "challenger_name": player.name,
            "wager_amount": big_dick_wager,
            "message": f"{player.name} offers The Big Dick! Risking {big_dick_wager} quarters against the field.",
            "requires_unanimous_acceptance": True,
        }

    def accept_big_dick(self, accepting_players: list[str]) -> dict[str, Any]:
        """
        Accept or reject The Big Dick challenge
        If not unanimous, individual players can use Ackerley's Gambit
        """
        hole_state = self.hole_states[self.current_hole]
        if not hole_state.betting.big_dick_invoked:
            raise ValueError("No Big Dick challenge active")

        challenger_id = next(p.id for p in self.players if p.points == max(p.points for p in self.players))
        challenger = next(p for p in self.players if p.id == challenger_id)

        other_players = [p for p in self.players if p.id != challenger_id]

        if len(accepting_players) == len(other_players):
            # Unanimous acceptance - standard Big Dick rules
            hole_state.teams = TeamFormation(
                type="solo",
                solo_player=challenger_id,
                opponents=[p.id for p in other_players],
                captain=challenger_id,
            )
            hole_state.betting.current_wager = abs(challenger.points)

            return {
                "status": "big_dick_accepted",
                "message": f"Big Dick unanimously accepted! {challenger.name} vs the field for {abs(challenger.points)} quarters.",
                "teams_formed": True,
            }
        # Not unanimous - handle Ackerley's Gambit
        declining_players = [p.id for p in other_players if p.id not in accepting_players]

        # Accepting players split the challenge
        if accepting_players:
            wager_per_player = abs(challenger.points) // len(accepting_players)
            hole_state.betting.ackerley_gambit = {
                "accepting_players": accepting_players,
                "declining_players": declining_players,
                "wager_per_accepting_player": wager_per_player,
            }

            return {
                "status": "big_dick_gambit",
                "message": f"Ackerley's Gambit invoked! {len(accepting_players)} players accept the challenge.",
                "accepting_players": [self._get_player_name(pid) for pid in accepting_players],
                "declining_players": [self._get_player_name(pid) for pid in declining_players],
                "wager_per_player": wager_per_player,
            }
        # No one accepts
        return {
            "status": "big_dick_declined",
            "message": "Big Dick challenge declined by all players.",
            "teams_formed": False,
        }
