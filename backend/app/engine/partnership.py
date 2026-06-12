"""Partnership mechanics for WolfGoatPigGame — captain/partner requests and resolution."""

import logging
from typing import Any

from ..domain.game_types import HoleState, TeamFormation
from ..validators import (
    BettingValidationError,
    BettingValidator,
    GameStateValidationError,
    GameStateValidator,
)

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

    def request_partner(self, captain_id: str, partner_id: str) -> dict[str, Any]:
        """Captain requests a specific player as partner"""
        hole_state = self.hole_states[self.current_hole]

        # Validate partnership formation using GameStateValidator
        try:
            GameStateValidator.validate_partnership_formation(
                captain_id=captain_id,
                partner_id=partner_id,
                tee_shots_complete=hole_state.partnership_deadline_passed,
            )
        except GameStateValidationError as e:
            logger.error(f"Partnership validation failed: {e.message}")
            raise ValueError(f"Cannot request partnership: {e.message}") from e

        # Validate request
        if hole_state.teams.captain != captain_id:
            raise ValueError("Only the captain can request a partner")

        if partner_id not in [p.id for p in self.players]:
            raise ValueError("Invalid partner ID")

        # Check eligibility based on hitting order and shots taken
        if not self._is_player_eligible_for_partnership(partner_id, hole_state):
            raise ValueError("Player is no longer eligible for partnership")

        # Set pending request
        hole_state.teams.pending_request = {
            "type": "partnership",
            "captain": captain_id,
            "requested": partner_id,
        }

        # Add partnership request event to timeline
        captain_name = self._get_player_name(captain_id)
        partner_name = self._get_player_name(partner_id)
        if self.hole_progression is not None:
            self.hole_progression.add_timeline_event(
                event_type="partnership_request",
                description=f"{captain_name} requests {partner_name} as partner",
                player_id=captain_id,
                player_name=captain_name,
                details={
                    "captain": captain_name,
                    "requested_partner": partner_name,
                    "captain_handicap": next(p.handicap for p in self.players if p.id == captain_id),
                    "partner_handicap": next(p.handicap for p in self.players if p.id == partner_id),
                    "hole_number": self.current_hole,
                },
            )

        return {
            "status": "pending",
            "message": f"Partnership request sent to {partner_name}",
            "awaiting_response": partner_id,
        }

    def respond_to_partnership(self, partner_id: str, accept: bool) -> dict[str, Any]:
        """Respond to partnership request"""
        hole_state = self.hole_states[self.current_hole]

        # Validate response
        pending = hole_state.teams.pending_request
        if not pending or pending.get("requested") != partner_id:
            raise ValueError("No pending partnership request for this player")

        captain_id = pending["captain"]

        if accept:
            return self._accept_partnership(captain_id, partner_id, hole_state)
        return self._decline_partnership(captain_id, partner_id, hole_state)

    def go_solo(self, captain_id: str, use_duncan: bool = False) -> dict[str, Any]:
        """Alias for captain_go_solo for backward compatibility"""
        return self.captain_go_solo(captain_id, use_duncan)

    def captain_go_solo(self, captain_id: str, use_duncan: bool = False) -> dict[str, Any]:
        """Captain decides to go solo (Pig)"""
        hole_state = self.hole_states[self.current_hole]

        if hole_state.teams.captain != captain_id:
            raise ValueError("Only the captain can go solo")

        # Validate Duncan using BettingValidator if requested
        if use_duncan:
            try:
                is_captain = hole_state.teams.captain == captain_id
                partnership_formed = hole_state.teams.type in ["partners", "solo"]
                BettingValidator.validate_duncan(
                    is_captain=is_captain,
                    partnership_formed=partnership_formed,
                    tee_shots_complete=hole_state.partnership_deadline_passed,
                )
            except BettingValidationError as e:
                logger.error(f"Duncan validation failed: {e.message}")
                raise ValueError(f"Cannot invoke The Duncan: {e.message}") from e

        captain = next(p for p in self.players if p.id == captain_id)

        # Track solo count for 4-man game requirement
        if self.player_count == 4:
            captain.solo_count += 1

        # Set up solo play
        opponents = [p.id for p in self.players if p.id != captain_id]
        hole_state.teams = TeamFormation(type="solo", captain=captain_id, solo_player=captain_id, opponents=opponents)

        # Apply wager multipliers
        multiplier = 2  # Base "On Your Own" multiplier

        if use_duncan:
            # The Duncan: 3 quarters for every 2 wagered
            hole_state.betting.duncan_invoked = True
            multiplier = 2  # Still doubles the base wager

        hole_state.betting.current_wager *= multiplier

        # Add solo decision event to timeline
        captain_name = self._get_player_name(captain_id)
        if self.hole_progression is not None:
            self.hole_progression.add_timeline_event(
                event_type="partnership_decision",
                description=f"{captain_name} decides to go solo",
                player_id=captain_id,
                player_name=captain_name,
                details={
                    "decision": "solo",
                    "captain": captain_name,
                    "duncan": use_duncan,
                    "new_wager": hole_state.betting.current_wager,
                    "opponents": [self._get_player_name(p) for p in opponents],
                },
            )

        return {
            "status": "solo",
            "message": f"Captain {captain_name} goes solo!",
            "duncan": use_duncan,
            "wager": hole_state.betting.current_wager,
        }

    def _is_player_eligible_for_partnership(self, player_id: str, hole_state: HoleState) -> bool:
        """Check if player is still eligible to be requested as partner"""
        # Player becomes ineligible once next player has hit
        player_index = hole_state.hitting_order.index(player_id)

        # Check if next player has already hit
        if player_index < len(hole_state.hitting_order) - 1:
            next_player = hole_state.hitting_order[player_index + 1]
            return not hole_state.shots_completed.get(next_player, False)

        # Last player is eligible until first second shot
        return not any(hole_state.shots_completed.values())

    def _accept_partnership(self, captain_id: str, partner_id: str, hole_state: HoleState) -> dict[str, Any]:
        """Handle partnership acceptance"""
        others = [p.id for p in self.players if p.id not in [captain_id, partner_id]]

        hole_state.teams = TeamFormation(
            type="partners",
            captain=captain_id,
            team1=[captain_id, partner_id],
            team2=others,
        )

        hole_state.teams.pending_request = None

        # Add partnership acceptance event to timeline
        captain_name = self._get_player_name(captain_id)
        partner_name = self._get_player_name(partner_id)
        if self.hole_progression is not None:
            self.hole_progression.add_timeline_event(
                event_type="partnership_response",
                description=f"{partner_name} accepts partnership with {captain_name}",
                player_id=partner_id,
                player_name=partner_name,
                details={
                    "accepted": True,
                    "captain": captain_name,
                    "partner": partner_name,
                    "team1": [captain_name, partner_name],
                    "team2": [self._get_player_name(p) for p in others],
                },
            )

        return {
            "status": "partnership_formed",
            "message": f"Partnership formed: {captain_name} & {partner_name}",
            "team1": [captain_id, partner_id],
            "team2": others,
        }

    def _decline_partnership(self, captain_id: str, partner_id: str, hole_state: HoleState) -> dict[str, Any]:
        """Handle partnership decline - captain goes solo"""
        others = [p.id for p in self.players if p.id != captain_id]

        # Track solo count for 4-man requirement
        if self.player_count == 4:
            captain = next(p for p in self.players if p.id == captain_id)
            captain.solo_count += 1

        hole_state.teams = TeamFormation(type="solo", captain=captain_id, solo_player=captain_id, opponents=others)

        # Double the wager due to partnership decline
        hole_state.betting.current_wager *= 2
        hole_state.teams.pending_request = None

        # Add partnership decline event to timeline
        captain_name = self._get_player_name(captain_id)
        partner_name = self._get_player_name(partner_id)
        if self.hole_progression is not None:
            self.hole_progression.add_timeline_event(
                event_type="partnership_response",
                description=f"{partner_name} declines partnership - {captain_name} goes solo",
                player_id=partner_id,
                player_name=partner_name,
                details={
                    "accepted": False,
                    "captain": captain_name,
                    "partner": partner_name,
                    "new_wager": hole_state.betting.current_wager,
                    "solo_player": captain_name,
                    "opponents": [self._get_player_name(p) for p in others],
                },
            )

        return {
            "status": "partnership_declined",
            "message": f"{partner_name} declined. {captain_name} goes solo!",
            "new_wager": hole_state.betting.current_wager,
        }
