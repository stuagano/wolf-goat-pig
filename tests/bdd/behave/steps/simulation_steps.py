"""Step definitions for simulation BDD tests."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from behave import given, then, when
from fastapi.testclient import TestClient

from utils.simulation_helpers import (
    format_value_for_comparison,
    get_nested_value,
    make_simulation_request,
    parse_table_to_dict,
    parse_table_to_list_of_dicts,
    refresh_state,
    seed_state,
    set_nested_value,
    setup_simulation,
)


class _BehaveResponse:
    """Simple adapter so Behave assertions can inspect responses uniformly."""

    def __init__(self, status_code: int, body: Any, text: str) -> None:
        self.status_code = status_code
        self._body = body
        self.text = text

    def json(self) -> Any:  # pragma: no cover - trivial accessor
        return self._body


def _parse_raw_value(raw_value: str) -> Any:
    """Parse tables cells into Python values with JSON/bool/number support."""

    value = raw_value.strip()
    if value.startswith(("[", "{")) and value.endswith(("]", "}")):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"none", "null", ""}:
        return None

    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def _extract_payload_and_headers(context) -> Any:
    """Split a behave table into payload and header dictionaries."""

    payload: Dict[str, Any] = {}
    headers: Dict[str, str] = {}

    if hasattr(context, "table") and context.table:
        for row in context.table:
            key = row[0].strip()
            value = _parse_raw_value(row[1])

            if key.startswith("headers."):
                header_key = key.split(".", 1)[1]
                headers[header_key] = "" if value is None else str(value)
            else:
                set_nested_value(payload, key, value)

    return payload, headers


def _record_response(context, result: Dict[str, Any]) -> None:
    """Store the latest HTTP response on the behave context."""

    response = _BehaveResponse(result["status_code"], result["body"], result["text"])
    context.response = response
    context.responses.append(response)


def _build_test_client() -> TestClient:
    """Create a FastAPI TestClient configured for deterministic testing."""

    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("DATABASE_URL", "sqlite:///./reports/wolf_goat_pig.db")
    os.environ.setdefault("ENABLE_TEST_ENDPOINTS", "true")

    from backend.app.main import app  # Imported lazily so sys.path tweaks take effect

    return TestClient(app)


# ============================================================================
# Environment toggles
# ============================================================================


@given('ENABLE_TEST_ENDPOINTS is set to "{flag}"')
def step_set_enable_test_endpoints(context, flag: str) -> None:
    """Toggle ENABLE_TEST_ENDPOINTS for scenarios that need explicit control."""

    enabled = flag.lower() in {"true", "1", "yes", "on"}
    os.environ["ENABLE_TEST_ENDPOINTS"] = "true" if enabled else "false"

    # Rebuild the client so subsequent calls honour the new flag.
    if hasattr(context, "client"):
        context.client = _build_test_client()
        # Discard any cached state, it belongs to the previous client instance.
        if hasattr(context, "current_state"):
            delattr(context, "current_state")


# ============================================================================
# Setup and initialization steps
# ============================================================================


@given("the simulation API is available")
def step_api_available(context) -> None:
    """Initialise the HTTP client and response collection."""

    context.client = _build_test_client()
    context.responses: List[Any] = []
    context.hole_progression: List[int] = []


@given("a simulation is set up with {player_count:d} players")
def step_setup_simulation_with_count(context, player_count: int) -> None:
    """Set up a simulation with generated players."""

    if not hasattr(context, "client"):
        context.client = _build_test_client()

    players = [
        {"id": "p1", "name": "Test Captain", "handicap": 10, "is_human": True}
    ]
    for index in range(1, player_count):
        players.append(
            {
                "id": f"bot{index}",
                "name": f"Computer {index}",
                "handicap": 12 + index,
                "is_human": False,
                "personality": "balanced",
            }
        )

    context.setup_response = setup_simulation(context.client, players=players)
    context.current_state = refresh_state(context.client)


@given("a simulation is set up with the following players")
def step_setup_simulation_with_table(context) -> None:
    """Set up a simulation using table-driven player data."""

    if not hasattr(context, "client"):
        context.client = _build_test_client()

    players = parse_table_to_list_of_dicts(context.table)
    context.setup_response = setup_simulation(context.client, players=players)
    context.current_state = refresh_state(context.client)


# ============================================================================
# State seeding steps (table-driven)
# ============================================================================


@given("the simulation is at hole {hole_number:d}")
@when("the simulation is moved to hole {hole_number:d}")
def step_seed_hole_number(context, hole_number: int) -> None:
    """Seed the round to a particular hole number."""

    seed_state(context.client, {"current_hole": hole_number})
    context.current_state = refresh_state(context.client)


@given("the next player to hit is {player_id}")
@when("the next player to hit is set to {player_id}")
def step_seed_next_player(context, player_id: str) -> None:
    """Force the next player to hit."""

    seed_state(context.client, {"next_player_to_hit": player_id})
    context.current_state = refresh_state(context.client)


@given("the ball positions are")
@when("I seed ball positions with")
def step_seed_ball_positions(context) -> None:
    """Seed ball positions using a behaviour table."""

    ball_positions = parse_table_to_list_of_dicts(context.table)
    seed_state(context.client, {"ball_positions": ball_positions})
    context.current_state = refresh_state(context.client)


@given("the betting state is")
@when("I seed the betting state with")
def step_seed_betting_state(context) -> None:
    """Seed betting metadata using a table."""

    betting_dict = parse_table_to_dict(context.table)
    betting: Dict[str, Any] = {}

    for key, raw_value in betting_dict.items():
        lowered = raw_value.lower()
        if lowered in {"true", "false"}:
            betting[key] = lowered == "true"
        elif lowered in {"none", "null", ""}:
            betting[key] = None
        else:
            try:
                betting[key] = int(raw_value)
            except ValueError:
                try:
                    betting[key] = float(raw_value)
                except ValueError:
                    betting[key] = raw_value

    seed_state(context.client, {"betting": betting})
    context.current_state = refresh_state(context.client)


@given("the team formation is")
@when("I seed the team formation with")
def step_seed_team_formation(context) -> None:
    """Seed team formation from a table."""

    team_dict = parse_table_to_dict(context.table)
    formation: Dict[str, Any] = {}

    for key, raw_value in team_dict.items():
        lowered = raw_value.lower()

        if raw_value.startswith(("[", "{")) and raw_value.endswith(("]", "}")):
            try:
                formation[key] = json.loads(raw_value)
                continue
            except json.JSONDecodeError:
                formation[key] = raw_value
        elif lowered in {"none", "null", ""}:
            formation[key] = None
        else:
            formation[key] = raw_value

    seed_state(context.client, {"team_formation": formation})
    context.current_state = refresh_state(context.client)


@given("the wagering is {state}")
@given("wagering is set to {state}")
@when("wagering is set to {state}")
def step_seed_wagering_state(context, state: str) -> None:
    """Toggle the wagering closed flag."""

    seed_state(context.client, {"wagering_closed": state.lower() in {"closed", "locked"}})
    context.current_state = refresh_state(context.client)


@given("the line of scrimmage is {player_id}")
@when("the line of scrimmage is set to {player_id}")
def step_seed_line_of_scrimmage(context, player_id: str) -> None:
    """Assign the line of scrimmage to a player."""

    seed_state(context.client, {"betting": {"line_of_scrimmage": player_id}})
    context.current_state = refresh_state(context.client)


@given("the simulation state is seeded with")
@when("I seed the simulation state with")
def step_seed_complete_state(context) -> None:
    """Seed arbitrary aspects of the state using dot-notation paths."""

    seed_payload: Dict[str, Any] = {}

    for row in context.table:
        path, raw_value = row[0], row[1]

        if raw_value.startswith(("[", "{")) and raw_value.endswith(("]", "}")):
            try:
                parsed_value = json.loads(raw_value)
            except json.JSONDecodeError:
                parsed_value = raw_value
        elif raw_value.lower() in {"true", "false"}:
            parsed_value = raw_value.lower() == "true"
        elif raw_value.lower() in {"none", "null", ""}:
            parsed_value = None
        else:
            try:
                parsed_value = int(raw_value)
            except ValueError:
                try:
                    parsed_value = float(raw_value)
                except ValueError:
                    parsed_value = raw_value

        set_nested_value(seed_payload, path, parsed_value)

    # Normalise aliases expected by the API
    if "betting_state" in seed_payload:
        betting_state = seed_payload.pop("betting_state")
        existing = seed_payload.get("betting", {})
        if isinstance(existing, dict):
            existing.update(betting_state)
            seed_payload["betting"] = existing
        else:
            seed_payload["betting"] = betting_state

    seed_state(context.client, seed_payload)
    context.current_state = refresh_state(context.client)


# ============================================================================
# Action steps
# ============================================================================


@when('I request the "{method}" "{endpoint}" endpoint')
@when('I request the "{method}" "{endpoint}" endpoint with')
def step_request_endpoint(context, method: str, endpoint: str) -> None:
    """Issue a request to a simulation endpoint, optionally with a payload table."""

    payload, headers = _extract_payload_and_headers(context)
    result = make_simulation_request(
        context.client,
        method,
        endpoint,
        payload or None,
        headers=headers or None,
    )

    _record_response(context, result)


@when('I request the "{method}" "{endpoint}" endpoint without admin headers')
@when('I request the "{method}" "{endpoint}" endpoint without admin headers with')
def step_request_endpoint_without_admin(context, method: str, endpoint: str) -> None:
    """Issue a request while skipping default admin authentication headers."""

    payload, headers = _extract_payload_and_headers(context)
    result = make_simulation_request(
        context.client,
        method,
        endpoint,
        payload or None,
        headers=headers or None,
        omit_admin_header=True,
    )

    _record_response(context, result)


@when("I submit a simulation setup request with {player_count:d} players")
def step_submit_simulation_setup(context, player_count: int) -> None:
    """Submit a setup request directly via the API."""

    players = [
        {"id": "p1", "name": "Test Captain", "handicap": 10, "is_human": True}
    ]
    for index in range(1, player_count):
        players.append(
            {
                "id": f"bot{index}",
                "name": f"Computer {index}",
                "handicap": 12 + index,
                "is_human": False,
                "personality": "balanced",
            }
        )

    payload = {
        "players": players,
        "course": "Wing Point Golf & Country Club",
        "options": {"double_points_round": False, "annual_banquet": False},
    }

    context.response = context.client.post("/simulation/setup", json=payload)
    context.responses.append(context.response)


@when("I refresh the simulation state")
def step_refresh_state(context) -> None:
    """Refresh the cached simulation state."""

    context.current_state = refresh_state(context.client)


@when("I progress through the following holes")
def step_progress_through_holes(context) -> None:
    """Advance the simulation across multiple holes using a table-driven flow."""

    if not hasattr(context, "client"):
        context.client = _build_test_client()

    context.hole_progression = []

    raw_headings = [heading.strip() for heading in context.table.headings]

    for row in context.table:
        row_data = {
            heading.lower(): row[heading].strip()
            for heading in raw_headings
        }

        hole_number = int(row_data.get("hole", row[0]).strip())

        payload: Dict[str, Any] = {"current_hole": hole_number}

        if "team_type" in row_data or "captain" in row_data:
            team_payload: Dict[str, Any] = {}
            team_type_value = row_data.get("team_type", "")
            if team_type_value:
                team_payload["type"] = team_type_value

            captain_value = row_data.get("captain", "")
            if captain_value:
                team_payload["captain"] = captain_value
            if team_payload:
                payload["team_formation"] = team_payload

        wager_value = row_data.get("current_wager", "")
        if wager_value:
            payload.setdefault("betting", {})["current_wager"] = int(wager_value)

        closed_value = row_data.get("wagering_closed", "").lower()
        if closed_value:
            payload["wagering_closed"] = closed_value in {"true", "closed", "yes", "1"}

        seed_state(context.client, payload)
        context.current_state = refresh_state(context.client)
        context.hole_progression.append(hole_number)


# ============================================================================
# Assertion steps
# ============================================================================


@then("the response code is {status_code:d}")
def step_assert_status(context, status_code: int) -> None:
    """Assert the most recent response status code."""

    assert (
        context.response.status_code == status_code
    ), f"Expected status {status_code}, got {context.response.status_code}: {context.response.text}"


@then("the JSON response contains")
@then("the JSON response contains:")
def step_json_contains(context) -> None:
    """Assert selected keys in the JSON response match expected values."""

    body = context.response.json()
    for row in context.table:
        key, expected = row[0], row[1]
        actual = get_nested_value(body, key)
        actual_str = format_value_for_comparison(actual)
        assert (
            actual_str == expected
        ), f"Expected '{key}' to be '{expected}' but got '{actual_str}'"


@when("the simulation state contains")
@then("the simulation state contains")
def step_state_contains(context) -> None:
    """Assert selected keys in the cached simulation state match expected values."""

    state = context.current_state
    for row in context.table:
        key, expected = row[0], row[1]
        actual = get_nested_value(state, key)
        actual_str = format_value_for_comparison(actual)
        assert (
            actual_str == expected
        ), f"Expected state.{key} to be '{expected}' but got '{actual_str}'"


@then("the hole progression is")
def step_assert_hole_progression(context) -> None:
    """Assert the recorded hole traversal matches expectations."""

    expected = [int(row[0].strip()) for row in context.table]
    actual = getattr(context, "hole_progression", [])

    assert actual == expected, (
        f"Expected hole progression {expected}, got {actual}"
    )


@then("the current hole is {hole_number:d}")
def step_assert_current_hole(context, hole_number: int) -> None:
    """Assert the current hole number."""

    state = context.current_state
    assert state.get("current_hole") == hole_number, (
        f"Expected hole {hole_number}, got {state.get('current_hole')}"
    )


@then("the next player to hit is {player_id}")
def step_assert_next_player(context, player_id: str) -> None:
    """Assert the next player to hit."""

    state = context.current_state
    assert state.get("next_player_to_hit") == player_id, (
        f"Expected next player {player_id}, got {state.get('next_player_to_hit')}"
    )


@then('player "{player_id}" has a ball {distance:g} yards from the pin')
def step_assert_ball_position(context, player_id: str, distance: float) -> None:
    """Assert a player's ball distance from the pin."""

    positions = context.current_state.get("ball_positions", [])
    for position in positions:
        if position.get("player_id") == player_id:
            actual = position.get("distance_to_pin")
            assert actual is not None and abs(actual - distance) < 0.1, (
                f"Expected {player_id}'s ball at {distance} yards, got {actual}"
            )
            return

    raise AssertionError(f"No ball position found for player {player_id}")


@then('player "{player_id}" is in the {lie_type}')
def step_assert_ball_lie(context, player_id: str, lie_type: str) -> None:
    """Assert a player's lie type."""

    positions = context.current_state.get("ball_positions", [])
    for position in positions:
        if position.get("player_id") == player_id:
            assert position.get("lie_type") == lie_type, (
                f"Expected {player_id} in {lie_type}, got {position.get('lie_type')}"
            )
            return

    raise AssertionError(f"No ball position found for player {player_id}")


@then('player "{player_id}" has holed out')
def step_assert_player_holed(context, player_id: str) -> None:
    """Assert the player has holed out."""

    positions = context.current_state.get("ball_positions", [])
    for position in positions:
        if position.get("player_id") == player_id:
            assert position.get("holed") is True, f"Player {player_id} has not holed out"
            return

    raise AssertionError(f"No ball position found for player {player_id}")


@then("the betting is doubled")
def step_assert_betting_doubled(context) -> None:
    """Assert the betting state is doubled."""

    betting = context.current_state.get("betting_state", {})
    assert betting.get("doubled") is True, "Betting is not doubled"


@then("the current wager is {amount:d} quarters")
def step_assert_current_wager(context, amount: int) -> None:
    """Assert the current wager value."""

    betting = context.current_state.get("betting_state", {})
    assert betting.get("current_wager") == amount, (
        f"Expected wager of {amount}, got {betting.get('current_wager')}"
    )


@then("the teams are formed as {team_type}")
def step_assert_team_type(context, team_type: str) -> None:
    """Assert the team formation type."""

    teams = context.current_state.get("team_formation", {})
    assert teams.get("type") == team_type, (
        f"Expected team type {team_type}, got {teams.get('type')}"
    )


@then("team 1 contains players {players}")
def step_assert_team1_players(context, players: str) -> None:
    """Assert team 1 membership."""

    expected = {player.strip() for player in players.split(",")}
    actual = set(context.current_state.get("team_formation", {}).get("team1", []))
    assert actual == expected, f"Expected team1 to have {expected}, got {actual}"


@then("team 2 contains players {players}")
def step_assert_team2_players(context, players: str) -> None:
    """Assert team 2 membership."""

    expected = {player.strip() for player in players.split(",")}
    actual = set(context.current_state.get("team_formation", {}).get("team2", []))
    assert actual == expected, f"Expected team2 to have {expected}, got {actual}"


@then('player "{player_id}" is going solo')
def step_assert_player_solo(context, player_id: str) -> None:
    """Assert the solo player is as expected."""

    formation = context.current_state.get("team_formation", {})
    assert formation.get("type") == "solo", "Team formation is not solo"
    assert formation.get("solo_player") == player_id, (
        f"Expected solo player {player_id}, got {formation.get('solo_player')}"
    )


@then("wagering is {state}")
def step_assert_wagering_state(context, state: str) -> None:
    """Assert wagering open/closed state."""

    wagering_closed = context.current_state.get("wagering_closed", False)
    if state.lower() in {"closed", "locked"}:
        assert wagering_closed is True, "Wagering is not closed"
    else:
        assert wagering_closed is False, "Wagering is not open"


@then("the hole is complete")
def step_assert_hole_complete(context) -> None:
    """Assert the hole has been marked complete."""

    assert context.current_state.get("hole_complete") is True, "Hole is not complete"


@then("the hole is not complete")
def step_assert_hole_not_complete(context) -> None:
    """Assert the hole is not complete."""

    assert context.current_state.get("hole_complete") is False, "Hole is complete"


@then('player "{player_id}" has {points:d} points')
def step_assert_player_points(context, player_id: str, points: int) -> None:
    """Assert a player's quarter tally."""

    for player in context.current_state.get("players", []):
        if player.get("id") == player_id:
            assert player.get("points") == points, (
                f"Expected {player_id} to have {points} points, got {player.get('points')}"
            )
            return

    raise AssertionError(f"Player {player_id} not found in current state")
