"""Write endpoints that used to accept anonymous callers.

Each route below changed data, sent email, spent API or LLM credit, or pushed to
an outside system (GHIN, the legacy tee sheet) without checking who was calling.
Paths are read from the live app so a renamed route cannot silently pass.
"""

import re

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app
from app.services import auth_service as auth_module

client = TestClient(app)

ADMIN_ONLY = {
    "add_course",
    "update_course",
    "delete_course",
    "import_course_by_search",
    "import_course_from_file",
    "preview_course_import",
    "run_saturday_pairing_job",
    "delete_generated_pairings",
    "create_and_notify_matches",
    "analyze_sheet_structure",
    "create_leaderboard_from_sheet",
    "sync_sheet_data",
    "sync_wgp_sheet_data",
    "fetch_google_sheet",
    "compare_sheet_to_db_data",
    "create_test_game",
    "sync_player_ghin_handicap",
    "replicate_signup_to_legacy",
}
SIGNED_IN = {"post_score", "commissioner_chat", "commissioner_data_chat"}
SELF_OR_ADMIN = {"set_player_availability", "get_email_preferences", "update_email_preferences"}
ADMIN_OR_JOB = {"sync_ghin_handicaps", "groupme_media_harvest", "post_livsow_snapshot"}


def _api_routes(routes) -> list[APIRoute]:
    """Flatten the app's routes; FastAPI wraps each included router."""
    out = []
    for route in routes:
        if isinstance(route, APIRoute):
            out.append(route)
        elif hasattr(route, "original_router"):
            out.extend(_api_routes(route.original_router.routes))
    return out


def _routes(names: set[str]) -> list[tuple[str, str, str]]:
    found = []
    for route in _api_routes(app.routes):
        if route.name not in names:
            continue
        # Resolve through the app so any include_router prefix is applied.
        params = dict.fromkeys(re.findall(r"\{([^}:]+)", route.path), "1")
        path = app.url_path_for(route.name, **params)
        for method in route.methods - {"HEAD", "OPTIONS"}:
            if method == "GET" and route.name != "get_email_preferences":
                continue
            found.append((route.name, method, path))
    missing = names - {name for name, _, _ in found}
    assert not missing, f"routes not found on app: {missing}"
    return found


@pytest.mark.parametrize(
    ("name", "method", "path"),
    _routes(ADMIN_ONLY | SIGNED_IN | SELF_OR_ADMIN | ADMIN_OR_JOB),
)
def test_anonymous_caller_is_rejected(name, method, path, monkeypatch):
    monkeypatch.setenv("INTERNAL_JOB_TOKEN", "right")
    resp = client.request(method, path)
    assert resp.status_code in (401, 403), f"{name} {method} {path} -> {resp.status_code}"


@pytest.mark.parametrize(("name", "method", "path"), _routes(ADMIN_ONLY))
def test_signed_in_non_admin_is_rejected(name, method, path, mock_admin_identity, monkeypatch):
    monkeypatch.setenv("SUPER_ADMIN_EMAILS", "boss@example.com")
    resp = client.request(method, path, headers={"X-Admin-Email": "member@example.com"})
    assert resp.status_code == 403, f"{name} {method} {path} -> {resp.status_code}"


@pytest.mark.parametrize(("name", "method", "path"), _routes(SELF_OR_ADMIN))
def test_player_cannot_touch_another_players_settings(name, method, path, mock_admin_identity, monkeypatch):
    # The mocked signed-in player is id 999; the route targets player 1.
    monkeypatch.setenv("SUPER_ADMIN_EMAILS", "boss@example.com")
    body = {"player_profile_id": 1, "day_of_week": 0, "is_available": True} if name == "set_player_availability" else {}
    resp = client.request(method, path, headers={"X-Admin-Email": "member@example.com"}, json=body)
    assert resp.status_code == 403, f"{name} {method} {path} -> {resp.status_code}"


@pytest.mark.parametrize(("name", "method", "path"), _routes(ADMIN_OR_JOB))
def test_job_route_disabled_when_token_unset(name, method, path, monkeypatch):
    monkeypatch.delenv("INTERNAL_JOB_TOKEN", raising=False)
    resp = client.request(method, path, headers={"X-Internal-Job-Token": "anything"})
    assert resp.status_code == 503


@pytest.mark.parametrize(("name", "method", "path"), _routes(ADMIN_OR_JOB))
def test_job_route_rejects_wrong_token(name, method, path, monkeypatch):
    monkeypatch.setenv("INTERNAL_JOB_TOKEN", "right")
    resp = client.request(method, path, headers={"X-Internal-Job-Token": "wrong"})
    assert resp.status_code == 403


def test_job_route_accepts_right_token(monkeypatch):
    from app.routers import groupme

    monkeypatch.setenv("INTERNAL_JOB_TOKEN", "right")
    monkeypatch.setattr(groupme, "harvest_media", lambda db, max_pages: {"archived": 0})
    resp = client.post("/groupme/media/harvest", headers={"X-Internal-Job-Token": "right"})
    assert resp.status_code == 200
    assert resp.json() == {"archived": 0}


def test_job_route_accepts_signed_in_admin(monkeypatch):
    from app.routers import groupme

    monkeypatch.setenv("SUPER_ADMIN_EMAILS", "boss@example.com")
    monkeypatch.setattr(
        auth_module, "get_current_auth0_user", lambda credentials: {"sub": "auth0|boss", "email": "boss@example.com"}
    )
    monkeypatch.setattr(groupme, "harvest_media", lambda db, max_pages: {"archived": 0})
    resp = client.post("/groupme/media/harvest", headers={"Authorization": "Bearer test"})
    assert resp.status_code == 200


def test_job_route_rejects_signed_in_non_admin(monkeypatch):
    monkeypatch.setenv("SUPER_ADMIN_EMAILS", "boss@example.com")
    monkeypatch.setattr(
        auth_module, "get_current_auth0_user", lambda credentials: {"sub": "auth0|member", "email": "m@example.com"}
    )
    resp = client.post("/groupme/media/harvest", headers={"Authorization": "Bearer test"})
    assert resp.status_code == 403
