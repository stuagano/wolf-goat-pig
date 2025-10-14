"""Step definitions for simulation BDD tests."""

from __future__ import annotations

import json
import os
from typing import Dict

from behave import given, when, then
from fastapi.testclient import TestClient


def _build_test_client() -> TestClient:
    """Create a FastAPI TestClient with a predictable SQLite database location."""
    # Ensure the FastAPI app initialises against the lightweight SQLite database bundled with the repo
    os.environ.setdefault("DATABASE_URL", "sqlite:///./reports/wolf_goat_pig.db")

    from backend.app.main import app  # Imported lazily so sys.path tweaks in conftest take effect

    return TestClient(app)


@given("the simulation API is available")
def step_api_available(context) -> None:
    context.client = _build_test_client()


@when('I request the "{method}" "{endpoint}" endpoint')
def step_request_endpoint(context, method: str, endpoint: str) -> None:
    client: TestClient = context.client
    path = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    context.response = client.request(method.upper(), path)


@when("I submit a simulation setup request with {player_count:d} players")
def step_submit_simulation_setup(context, player_count: int) -> None:
    client: TestClient = context.client
    payload: Dict[str, object] = {
        "players": [
            {"id": "p1", "name": "Test Captain", "handicap": 10, "is_human": True},
        ]
        + [
            {
                "id": f"bot{i}",
                "name": f"Computer {i}",
                "handicap": 12 + i,
                "is_human": False,
                "personality": "balanced",
            }
            for i in range(1, player_count)
        ],
        "course": "Wing Point Golf & Country Club",
        "options": {"double_points_round": False, "annual_banquet": False},
    }

    context.response = client.post("/simulation/setup", json=payload)


@then("the response code is {status_code:d}")
def step_assert_status(context, status_code: int) -> None:
    assert context.response.status_code == status_code, context.response.text


@then("the JSON response contains:")
def step_json_contains(context) -> None:
    body = context.response.json()
    for row in context.table:
        key, expected = row[0], row[1]
        actual = body
        for fragment in key.split('.'):
            if isinstance(actual, dict):
                actual = actual.get(fragment)
            else:
                raise AssertionError(f"Cannot drill into non-dict segment '{fragment}'")

        if isinstance(actual, (dict, list)):
            actual_str = json.dumps(actual, sort_keys=True)
        else:
            actual_str = str(actual)

        assert actual_str == expected, f"Expected '{key}' to be '{expected}' but got '{actual_str}'"
