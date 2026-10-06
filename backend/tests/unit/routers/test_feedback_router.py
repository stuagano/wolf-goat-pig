"""Feedback stays authenticated, bounded, and server-authored on GitHub."""

from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.middleware.rate_limiting import rate_limiter
from app.models import PlayerProfile
from app.services.auth_service import get_current_user

PAYLOAD = {
    "type": "bug",
    "title": " Scores disappear ",
    "description": "After saving a round.",
    "steps": "Save, then reload.",
}
ISSUE_URL = "https://github.com/stuagano/wolf-goat-pig/issues/123"


@pytest.fixture
def feedback_client(monkeypatch):
    monkeypatch.setenv("WGP_FEEDBACK_GITHUB_TOKEN", "test-server-token")
    app.dependency_overrides[get_current_user] = lambda: PlayerProfile(
        id=901, name="Private Name", email="private@example.com"
    )
    rate_limiter.reset("feedback", "901")
    post = AsyncMock(return_value=httpx.Response(201, json={"number": 123, "html_url": ISSUE_URL}))
    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    try:
        yield TestClient(app), post
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        rate_limiter.reset("feedback", "901")


def test_feedback_creates_one_issue_without_publishing_account_details(feedback_client):
    client, post = feedback_client
    response = client.post("/feedback", json=PAYLOAD)
    assert response.status_code == 201, response.text
    assert response.json() == {"number": 123, "url": ISSUE_URL}
    assert post.call_args.args[0] == "https://api.github.com/repos/stuagano/wolf-goat-pig/issues"
    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer test-server-token"
    issue = post.call_args.kwargs["json"]
    assert issue["title"] == "[Feedback: Bug] Scores disappear"
    assert "After saving a round." in issue["body"] and "Save, then reload." in issue["body"]
    assert "private@example.com" not in issue["body"] and "Private Name" not in issue["body"]
    assert "test-server-token" not in response.text
    duplicate = client.post("/feedback", json=PAYLOAD)
    assert duplicate.status_code == 429
    assert "Retry-After" in duplicate.headers
    post.assert_awaited_once()


@pytest.mark.parametrize(
    "change",
    [
        {"title": "   "},
        {"description": "\n "},
        {"title": "x" * 121},
        {"description": "x" * 5001},
        {"steps": "x" * 3001},
        {"type": "invalid"},
        {"repo": "another/repo"},
    ],
)
def test_invalid_feedback_never_reaches_github(feedback_client, change):
    client, post = feedback_client
    assert client.post("/feedback", json={**PAYLOAD, **change}).status_code == 422
    post.assert_not_awaited()


def test_feedback_requires_login(feedback_client):
    client, post = feedback_client
    app.dependency_overrides.pop(get_current_user)
    assert client.post("/feedback", json=PAYLOAD).status_code in (401, 403)
    post.assert_not_awaited()


def test_missing_server_credential_is_actionable(feedback_client, monkeypatch):
    client, post = feedback_client
    monkeypatch.delenv("WGP_FEEDBACK_GITHUB_TOKEN")
    response = client.post("/feedback", json=PAYLOAD)
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]
    post.assert_not_awaited()


def test_github_rejection_does_not_leak_upstream_details(feedback_client):
    client, post = feedback_client
    post.return_value = httpx.Response(403, json={"message": "sensitive upstream error"})
    response = client.post("/feedback", json=PAYLOAD)
    assert response.status_code == 502
    assert "sensitive" not in response.text
    post.assert_awaited_once()


def test_uncertain_delivery_is_not_retried(feedback_client):
    client, post = feedback_client
    post.side_effect = httpx.ReadTimeout("sensitive network details")
    response = client.post("/feedback", json=PAYLOAD)
    assert response.status_code == 504
    assert "before submitting again" in response.json()["detail"]
    assert "sensitive" not in response.text
    post.assert_awaited_once()
