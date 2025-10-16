"""Helper utilities for simulation BDD tests."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi.testclient import TestClient


def refresh_state(client: TestClient) -> Dict[str, Any]:
    """Fetch the latest simulation snapshot and expose handy top-level keys."""

    response = client.get("/simulation/state")
    assert response.status_code == 200, f"Failed to get state: {response.text}"

    state: Dict[str, Any] = response.json()
    hole_state: Dict[str, Any] = state.get("hole_state", {}) or {}

    # Normalise ball positions into a flat list for easier assertions
    ball_positions_raw = hole_state.get("ball_positions", {}) or {}
    if isinstance(ball_positions_raw, dict):
        ball_positions: List[Dict[str, Any]] = []
        for player_id, payload in ball_positions_raw.items():
            entry: Dict[str, Any]
            if payload is None:
                entry = {"player_id": player_id}
            else:
                entry = dict(payload)
                entry.setdefault("player_id", player_id)
            ball_positions.append(entry)
    elif isinstance(ball_positions_raw, list):
        ball_positions = ball_positions_raw
    else:
        ball_positions = []

    # Bubble up commonly accessed fields
    enriched: Dict[str, Any] = dict(state)
    enriched["ball_positions"] = ball_positions

    betting_raw = hole_state.get("betting", {}) or {}
    betting = dict(betting_raw)
    special_rules = betting.pop("special_rules", {})
    if isinstance(special_rules, dict):
        for key, value in special_rules.items():
            betting.setdefault(key, value)
    enriched["betting_state"] = betting

    teams_raw = hole_state.get("teams") or {}
    enriched["team_formation"] = dict(teams_raw) if isinstance(teams_raw, dict) else {}
    enriched["current_hole"] = state.get("current_hole", hole_state.get("hole_number"))
    enriched["next_player_to_hit"] = hole_state.get("next_player_to_hit")
    enriched["wagering_closed"] = hole_state.get("wagering_closed")
    enriched["hole_complete"] = hole_state.get("hole_complete")

    return enriched


def seed_state(client: TestClient, seed_data: Dict[str, Any]) -> Dict[str, Any]:
    """Seed the active simulation and return the resulting game state."""

    response = client.post("/simulation/test/seed-state", json=seed_data)
    assert response.status_code == 200, f"Failed to seed state: {response.text}"
    payload = response.json()
    return payload.get("game_state", {})


def setup_simulation(
    client: TestClient,
    *,
    players: Optional[List[Dict[str, Any]]] = None,
    course: str = "Wing Point Golf & Country Club",
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Bootstrap a simulation round with the provided parameters."""

    default_players = [
        {"id": "p1", "name": "Test Captain", "handicap": 10, "is_human": True},
        {"id": "p2", "name": "Computer 1", "handicap": 12, "is_human": False},
        {"id": "p3", "name": "Computer 2", "handicap": 14, "is_human": False},
        {"id": "p4", "name": "Computer 3", "handicap": 16, "is_human": False},
    ]

    payload = {
        "players": players or default_players,
        "course": course,
        "options": options or {"double_points_round": False, "annual_banquet": False},
    }

    response = client.post("/simulation/setup", json=payload)
    assert response.status_code == 200, f"Failed to setup simulation: {response.text}"
    return response.json()


def make_simulation_request(
    client: TestClient,
    method: str,
    endpoint: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Issue a request to a simulation endpoint and capture the response."""

    path = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    method_upper = method.upper()

    if method_upper == "GET":
        response = client.get(path)
    elif method_upper == "POST":
        response = client.post(path, json=payload or {})
    elif method_upper == "PUT":
        response = client.put(path, json=payload or {})
    elif method_upper == "DELETE":
        response = client.delete(path)
    else:
        response = client.request(method_upper, path, json=payload or {})

    body: Any
    try:
        body = response.json()
    except Exception:  # pragma: no cover - fallback for invalid JSON
        body = {}

    return {
        "status_code": response.status_code,
        "body": body,
        "text": response.text,
    }


def parse_table_to_dict(table, key_column: int = 0, value_column: int = 1) -> Dict[str, str]:
    """Convert a Behave table to a dictionary."""
    result: Dict[str, str] = {}
    for row in table:
        result[row[key_column]] = row[value_column]
    return result


def parse_table_to_list_of_dicts(table) -> List[Dict[str, Any]]:
    """Convert a Behave table to a list of dictionaries."""

    if not table:
        return []

    headers = table.headings
    parsed: List[Dict[str, Any]] = []

    for row in table:
        entry: Dict[str, Any] = {}
        for index, header in enumerate(headers):
            value = row[index]
            lowered = value.lower()

            if value.startswith(("{", "[")) and value.endswith(("}", "]")):
                try:
                    entry[header] = json.loads(value)
                    continue
                except json.JSONDecodeError:
                    pass

            if lowered in {"true", "false"}:
                entry[header] = lowered == "true"
            elif lowered in {"none", "null", ""}:
                entry[header] = None
            else:
                try:
                    entry[header] = int(value)
                except ValueError:
                    try:
                        entry[header] = float(value)
                    except ValueError:
                        entry[header] = value

        parsed.append(entry)

    return parsed


def get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """Retrieve a nested value using dot-notation with optional list indices."""

    current: Any = data
    for key in path.split("."):
        if "[" in key and key.endswith("]"):
            name, index_str = key[:-1].split("[")
            current = current.get(name) if isinstance(current, dict) else None
            if not isinstance(current, (list, tuple)):
                return None
            try:
                current = current[int(index_str)]
            except (ValueError, IndexError):
                return None
        else:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None

    return current


def set_nested_value(data: Dict[str, Any], path: str, value: Any) -> None:
    """Set a nested value using dot-notation with optional list indices."""

    keys = path.split(".")
    current = data

    for key in keys[:-1]:
        if "[" in key and key.endswith("]"):
            name, index_str = key[:-1].split("[")
            index = int(index_str)

            current.setdefault(name, [])
            target_list = current[name]
            while len(target_list) <= index:
                target_list.append({})
            current = target_list[index]
        else:
            current = current.setdefault(key, {})

    final_key = keys[-1]
    if "[" in final_key and final_key.endswith("]"):
        name, index_str = final_key[:-1].split("[")
        index = int(index_str)

        current.setdefault(name, [])
        target_list = current[name]
        while len(target_list) <= index:
            target_list.append(None)
        target_list[index] = value
    else:
        current[final_key] = value


def format_value_for_comparison(value: Any) -> str:
    """Normalise values so textual comparisons are stable."""

    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    if value is None:
        return "null"
    return str(value)
