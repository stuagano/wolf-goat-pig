"""Contract tests for the GroupMe integration (league chat bridge, read side).

`groupme_service._api_get` performs its GET with the **stdlib**
`urllib.request.urlopen` (NOT httpx, NOT requests), so neither respx nor the
`responses` library intercepts it. We mock at that seam: patch
`urllib.request.urlopen` to return a fake response object (`.read()` ->
bytes, context-manager protocol) or to raise the real exception type.

GroupMe wraps payloads as ``{"response": <payload>, "meta": {"code": <int>}}``;
`_api_get` returns ``parsed.get("response")``. `list_groups()` maps each group
to ``{"id", "name", "members": <count>}`` and returns ``[]`` when the payload
is falsy.

Behaviors pinned here (verified against the real code):
- success            -> list of mapped groups
- missing `response` -> `_api_get` returns None -> `list_groups()` -> []
- 401 / 500          -> urlopen raises urllib.error.HTTPError; `list_groups`
                        does NOT catch it, so it propagates
- timeout            -> urlopen raises TimeoutError (socket timeout); propagates
- malformed (non-JSON) body -> json.loads raises json.JSONDecodeError; propagates
- missing token      -> `_token()` is None -> `_api_get` raises RuntimeError
"""

import io
import json
import urllib.error
import urllib.request

import pytest

from app.services import groupme_service

GROUPS_OK = {
    "response": [{"id": "123", "name": "LivSOW 2026", "members": [{"id": "m1"}]}],
    "meta": {"code": 200},
}


class _FakeResp:
    """Minimal stand-in for the urlopen() context-manager response."""

    def __init__(self, body: str):
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResp":
        return self

    def __exit__(self, *_exc) -> bool:
        return False


def _patch_urlopen(monkeypatch, *, body: str | None = None, exc: BaseException | None = None):
    """Intercept the stdlib HTTP fetch that _api_get uses."""

    def fake_urlopen(req, timeout=None):
        if exc is not None:
            raise exc
        return _FakeResp(body if body is not None else "")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)


def test_success_returns_visible_group(monkeypatch):
    monkeypatch.setenv("GROUPME_ACCESS_TOKEN", "test-token")
    _patch_urlopen(monkeypatch, body=json.dumps(GROUPS_OK))

    groups = groupme_service.list_groups()

    assert isinstance(groups, list)
    assert {"id": groups[0]["id"], "name": groups[0]["name"]} == {
        "id": "123",
        "name": "LivSOW 2026",
    }
    # list_groups maps the members array to a count.
    assert groups[0]["members"] == 1


def test_missing_response_key_returns_empty(monkeypatch):
    # GroupMe envelope without a `response` payload -> _api_get returns None
    # -> list_groups() coalesces to []. Pin this graceful-empty behavior.
    monkeypatch.setenv("GROUPME_ACCESS_TOKEN", "test-token")
    _patch_urlopen(monkeypatch, body=json.dumps({"meta": {"code": 200}}))

    assert groupme_service.list_groups() == []


def test_unauthorized_401_propagates(monkeypatch):
    monkeypatch.setenv("GROUPME_ACCESS_TOKEN", "test-token")
    err = urllib.error.HTTPError(
        url="https://api.groupme.com/v3/groups",
        code=401,
        msg="Unauthorized",
        hdrs={},  # type: ignore[arg-type]
        fp=io.BytesIO(b'{"meta": {"code": 401, "errors": ["unauthorized"]}}'),
    )
    _patch_urlopen(monkeypatch, exc=err)

    # list_groups() does not catch HTTPError (only get_messages does), so the
    # 401 surfaces to the caller. Assert the specific type + code.
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        groupme_service.list_groups()
    assert excinfo.value.code == 401


def test_server_error_500_propagates(monkeypatch):
    monkeypatch.setenv("GROUPME_ACCESS_TOKEN", "test-token")
    err = urllib.error.HTTPError(
        url="https://api.groupme.com/v3/groups",
        code=500,
        msg="Internal Server Error",
        hdrs={},  # type: ignore[arg-type]
        fp=io.BytesIO(b"server error"),
    )
    _patch_urlopen(monkeypatch, exc=err)

    with pytest.raises(urllib.error.HTTPError) as excinfo:
        groupme_service.list_groups()
    assert excinfo.value.code == 500


def test_timeout_propagates(monkeypatch):
    monkeypatch.setenv("GROUPME_ACCESS_TOKEN", "test-token")
    # urlopen(timeout=15) raises a socket timeout (TimeoutError subclass) on
    # timeout. Specific type: a bare Exception would green-wash an unrelated
    # construction error.
    _patch_urlopen(monkeypatch, exc=TimeoutError("timed out"))

    with pytest.raises(TimeoutError):
        groupme_service.list_groups()


def test_malformed_body_raises_json_error(monkeypatch):
    monkeypatch.setenv("GROUPME_ACCESS_TOKEN", "test-token")
    # Non-JSON 200 body -> json.loads(...) in _api_get raises. Assert the
    # decode path actually fired, not just "some exception".
    _patch_urlopen(monkeypatch, body="not json at all")

    with pytest.raises(json.JSONDecodeError):
        groupme_service.list_groups()


def test_missing_token_raises_runtime_error(monkeypatch):
    monkeypatch.delenv("GROUPME_ACCESS_TOKEN", raising=False)
    # No HTTP should happen: _token() is None so _api_get raises before any
    # urlopen call.
    with pytest.raises(RuntimeError, match="GROUPME_ACCESS_TOKEN not configured"):
        groupme_service.list_groups()
