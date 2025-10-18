"""Minimal simulation helper for integration tests."""

from copy import deepcopy

from typing import Any, Dict, List, Optional

from app.wolf_goat_pig_simulation import WolfGoatPigSimulation


def _serialize_team_state(teams, *, default_captain: Optional[str] = None) -> Dict[str, Any]:
    """Convert the simulation's TeamFormation into the legacy dict structure."""

    if teams is None:
        return {}

    pending = getattr(teams, "pending_request", None) or {}
    if pending:
        captain = pending.get("captain") or getattr(teams, "captain", default_captain)
        return {
            "type": "pending",
            "captain": captain,
            "requested": pending.get("requested"),
        }

    team_type = getattr(teams, "type", None)
    captain = getattr(teams, "captain", default_captain)

    if team_type == "partners":
        return {
            "type": "partners",
            "captain": captain,
            "team1": list(getattr(teams, "team1", []) or []),
            "team2": list(getattr(teams, "team2", []) or []),
        }

    if team_type == "solo":
        solo_captain = captain or getattr(teams, "solo_player", None)
        return {
            "type": "solo",
            "captain": solo_captain,
            "opponents": list(getattr(teams, "opponents", []) or []),
        }

    if team_type == "pending" and not pending:
        return {}

    if team_type:
        data = {"type": team_type}
        if captain:
            data["captain"] = captain
        return data

    return {}


_BETTING_SYNC_FIELDS: List[str] = [
    "base_wager",
    "current_wager",
    "doubled",
    "redoubled",
    "carry_over",
    "float_invoked",
    "option_invoked",
    "duncan_invoked",
    "tunkarri_invoked",
    "big_dick_invoked",
    "joes_special_value",
    "ackerley_gambit",
    "line_of_scrimmage",
    "doubles_history",
    "tossed_aardvarks",
    "ping_pong_count",
]


def _sync_betting_state(betting_state: Any, hole_state) -> Any:
    """Mirror the simulation betting snapshot back into the legacy shell."""

    if betting_state is None or hole_state is None or hole_state.betting is None:
        return betting_state

    source = hole_state.betting
    for attr in _BETTING_SYNC_FIELDS:
        if hasattr(betting_state, attr) and hasattr(source, attr):
            setattr(betting_state, attr, getattr(source, attr))

    if hasattr(betting_state, "base_wager") and hasattr(source, "current_wager"):
        setattr(betting_state, "base_wager", getattr(source, "current_wager"))

    teams_dict = _serialize_team_state(
        getattr(hole_state, "teams", None),
        default_captain=getattr(hole_state.teams, "captain", None),
    )
    setattr(betting_state, "teams", teams_dict)
    return betting_state


DEFAULT_BOTS = [
    {
        "id": "bot_alpha",
        "name": "Alpha Bot",
        "handicap": 10.0,
        "personality": "balanced",
    },
    {
        "id": "bot_bravo",
        "name": "Bravo Bot",
        "handicap": 14.0,
        "personality": "aggressive",
    },
    {
        "id": "bot_charlie",
        "name": "Charlie Bot",
        "handicap": 18.0,
        "personality": "conservative",
    },
]


class _LegacyPlayerManager:
    """Minimal shim providing access to hitting order, captain, and players."""

    def __init__(self, hitting_order, captain_id, players) -> None:
        self.hitting_order = []
        self.captain_index = 0
        self.captain_id = captain_id
        self.players = list(players or [])
        self.update(hitting_order, captain_id, players)

    def update(self, hitting_order, captain_id, players=None, advance_captain=False) -> None:
        if hitting_order:
            self.hitting_order = list(hitting_order)
        if players is not None:
            self.players = list(players)

        if advance_captain and self.hitting_order:
            self.captain_index = (self.captain_index + 1) % len(self.hitting_order)
            self.captain_id = self.hitting_order[self.captain_index]
        elif captain_id is not None:
            self.captain_id = captain_id
            if self.captain_id in self.hitting_order:
                self.captain_index = self.hitting_order.index(self.captain_id)


class SimulationEngine:
    """Lightweight wrapper exposing only the methods exercised in tests."""

    def __init__(self) -> None:
        self._simulation: WolfGoatPigSimulation | None = None

    def setup_simulation(self, human_player, computer_configs, course_name=None):
        configs = deepcopy(list(computer_configs or []))

        required_bot_count = 3
        existing_ids = {
            cfg.get("id")
            for cfg in configs
            if isinstance(cfg, dict) and cfg.get("id")
        }

        for default in DEFAULT_BOTS:
            if len(configs) >= required_bot_count:
                break

            candidate = default.copy()
            suffix = 1
            original_id = candidate["id"]
            while candidate["id"] in existing_ids:
                candidate["id"] = f"{original_id}_{suffix}"
                suffix += 1

            configs.append(candidate)
            existing_ids.add(candidate["id"])

        if len(configs) < required_bot_count:
            next_index = 1
            while len(configs) < required_bot_count:
                candidate_id = f"bot_extra_{next_index}"
                next_index += 1
                if candidate_id in existing_ids:
                    continue
                configs.append(
                    {
                        "id": candidate_id,
                        "name": f"Extra Bot {next_index}",
                        "handicap": 16.0,
                        "personality": "balanced",
                    }
                )
                existing_ids.add(candidate_id)

        player_count = max(4, 1 + len(configs))
        base_simulation = WolfGoatPigSimulation(player_count=player_count)
        game_state = base_simulation.setup_simulation(
            human_player,
            configs,
            course_name,
        )

        self._simulation = game_state.wgp_sim

        betting_state = game_state.betting_state
        if betting_state is None:
            current_hole_state = self._simulation.hole_states[self._simulation.current_hole]
            betting_state = current_hole_state.betting
            game_state.betting_state = betting_state
        else:
            current_hole_state = self._simulation.hole_states[self._simulation.current_hole]

        _sync_betting_state(betting_state, current_hole_state)

        human_id = getattr(human_player, "id", None) or "human"
        setattr(game_state, "compat_human_id", human_id)

        game_state.player_manager = _LegacyPlayerManager(
            current_hole_state.hitting_order,
            current_hole_state.teams.captain,
            self._simulation.players,
        )
        game_state.player_manager.update(
            current_hole_state.hitting_order,
            human_id,
            players=self._simulation.players,
        )
        game_state.hole_scores = {
            pid: (score if score is not None else 0)
            for pid, score in (current_hole_state.scores or {}).items()
        }

        def request_partner_adapter(captain_id: str, partner_id: str) -> Dict[str, Any]:
            current = getattr(betting_state, "teams", {}) or {}
            if current.get("type") == "pending":
                raise ValueError("Partnership already pending.")

            hole_state = self._simulation.hole_states[self._simulation.current_hole]
            actual_captain = self._ensure_captain(hole_state, captain_id)
            result = self._simulation.request_partner(actual_captain, partner_id)

            _sync_betting_state(betting_state, hole_state)

            return result

        def accept_partner_adapter(partner_id: str) -> Dict[str, Any]:
            current = getattr(betting_state, "teams", {}) or {}
            if current.get("type") != "pending" or current.get("requested") != partner_id:
                raise ValueError("No pending partner request for this player.")

            result = self._simulation.respond_to_partnership(partner_id, True)

            hole_state = self._simulation.hole_states[self._simulation.current_hole]
            _sync_betting_state(betting_state, hole_state)

            return result

        def decline_partner_adapter(partner_id: str) -> Dict[str, Any]:
            current = getattr(betting_state, "teams", {}) or {}
            if current.get("type") != "pending" or current.get("requested") != partner_id:
                raise ValueError("No pending partner request for this player.")

            result = self._simulation.respond_to_partnership(partner_id, False)

            hole_state = self._simulation.hole_states[self._simulation.current_hole]
            _sync_betting_state(betting_state, hole_state)

            return result

        setattr(betting_state, "request_partner", request_partner_adapter)
        setattr(betting_state, "accept_partner", accept_partner_adapter)
        setattr(betting_state, "decline_partner", decline_partner_adapter)

        return game_state

    def _ensure_captain(self, hole_state, player_id: Optional[str]) -> Optional[str]:
        """Ensure the given player is treated as captain for the active hole."""

        if not player_id or hole_state is None or getattr(hole_state, "teams", None) is None:
            return getattr(hole_state.teams, "captain", None)

        if hole_state.teams.captain == player_id:
            return player_id

        order = list(getattr(hole_state, "hitting_order", []) or [])
        if player_id in order and order:
            index = order.index(player_id)
            hole_state.hitting_order = order[index:] + order[:index]

        hole_state.teams.captain = player_id
        return player_id

    def simulate_hole(self, game_state, human_decisions):
        if self._simulation is None:
            raise RuntimeError("setup_simulation must be called before simulate_hole")

        decisions: Dict[str, Any] = dict(human_decisions or {})

        hole_state = self._simulation.hole_states[self._simulation.current_hole]
        betting_state = getattr(game_state, "betting_state", None)
        if betting_state is not None:
            _sync_betting_state(betting_state, hole_state)

        interaction: Optional[Dict[str, Any]] = None
        finished_hole = False

        if "accept" in decisions and "partner_id" in decisions:
            try:
                result = self._simulation.respond_to_partnership(
                    decisions["partner_id"], bool(decisions["accept"])
                )
            except ValueError as exc:
                result = {
                    "status": "invalid_partnership_response",
                    "message": str(exc),
                }
            finished_hole = True
        elif decisions.get("action") == "go_solo":
            human_id = getattr(game_state, "compat_human_id", None)
            captain_id = self._ensure_captain(hole_state, human_id)
            result = self._simulation.captain_go_solo(captain_id)
            finished_hole = True
        elif decisions.get("action") == "request_partner":
            requested_partner = decisions.get("requested_partner")
            if requested_partner is None:
                raise ValueError("requested_partner is required when requesting a partner")

            human_id = getattr(game_state, "compat_human_id", None)
            promoted_captain = self._ensure_captain(hole_state, human_id)

            actual_captain = promoted_captain or hole_state.teams.captain or decisions.get("captain_id")
            actual_captain = actual_captain or decisions.get("caller") or decisions.get("player_id")
            actual_captain = actual_captain or "human"

            result = self._simulation.request_partner(actual_captain, requested_partner)
            if betting_state is not None:
                _sync_betting_state(betting_state, hole_state)

            interaction = {
                "type": "partnership_response",
                "captain": actual_captain,
                "requested_partner": requested_partner,
            }
            if isinstance(result, dict):
                interaction.update(result)
            else:
                interaction["result"] = result
        else:
            result = self._simulation.simulate_hole(game_state, decisions)
            finished_hole = True
            hole_state = self._simulation.hole_states[self._simulation.current_hole]

        # Capture scoring snapshot before potentially advancing.
        scores_snapshot = {
            pid: (score if score is not None else 0)
            for pid, score in (hole_state.scores or {}).items()
        }

        if finished_hole:
            if betting_state is not None:
                _sync_betting_state(betting_state, hole_state)

            self._simulation.advance_to_next_hole()

        game_state.current_hole = self._simulation.current_hole

        active_hole_state = self._simulation.hole_states[self._simulation.current_hole]

        player_manager = getattr(game_state, "player_manager", None)
        if isinstance(player_manager, _LegacyPlayerManager):
            player_manager.update(
                active_hole_state.hitting_order,
                active_hole_state.teams.captain,
                players=self._simulation.players,
            )
        else:
            game_state.player_manager = _LegacyPlayerManager(
                active_hole_state.hitting_order,
                active_hole_state.teams.captain,
                self._simulation.players,
            )

        game_state.hole_scores = scores_snapshot

        return game_state, result, interaction
