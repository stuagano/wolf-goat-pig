"""Malformed requests (Pydantic validation failures) must return the app's
standard error envelope, not FastAPI's default `{"detail": [...]}` array."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_validation_error_uses_standard_envelope():
    # POST /courses requires name + holes; an empty body fails Pydantic validation.
    resp = client.post("/courses", json={})
    assert resp.status_code == 422
    body = resp.json()
    # Same shape as the HTTPException handler: top-level "error" + string "detail".
    assert body["error"] == "Validation error"
    assert isinstance(body["detail"], str)
    # Plus a structured, frontend-friendly fields list.
    assert isinstance(body["fields"], list) and body["fields"]
    first = body["fields"][0]
    assert {"field", "message", "type"} <= set(first)
    # NOT FastAPI's default array-under-detail format.
    assert not isinstance(body["detail"], list)
