"""Contract tests for the Google Sheets integration (leaderboard / round sync).

The Google read client lives in ``app/services/spreadsheet_sync_service.py``.
Unlike the other six reference services, it talks to Google over the stdlib
``urllib.request`` — NOT httpx or requests. So respx/responses are useless here;
the correct seam is ``monkeypatch.setattr("urllib.request.urlopen", fake)``,
which the module reaches via ``import urllib.request``.

urllib specifics that drive the mocking strategy:
- ``urlopen`` RAISES ``HTTPError`` on 4xx/5xx (it does not return a status), so
  the 401/403/500 cases must *raise*, not return a fake response. Only success
  and malformed-body return a fake.
- The success read hits ``urlopen`` TWICE: token exchange at
  ``oauth2.googleapis.com/token`` (because ``GOOGLE_OAUTH_CREDENTIALS`` is set),
  then the values read at ``sheets.googleapis.com``. One fake branches on URL.
- ``urlopen`` is used as a context manager whose ``.read()`` returns bytes.

Real behavior being pinned: EVERY read failure (401, 403, 500, timeout,
malformed body) is swallowed by the broad ``except Exception`` in
``_sheets_api_get`` → returns ``None`` → ``get_all_rounds`` returns ``[]``. There
is NO refresh-retry on 401 — an expired token is observationally identical to
an empty sheet. We pin that as-is (and flag it as a real silent-masking concern)
and additionally assert the sheets request actually fired, so the no-token
short-circuit can't green-wash a test that proves nothing.
"""

import json
import urllib.error

import pytest

from app.services.spreadsheet_sync_service import SpreadsheetSyncService

OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
SHEETS_HOST = "https://sheets.googleapis.com/"
FAKE_ACCESS_TOKEN = "fake-access-token-xyz"

# Real-shaped Google credentials blob; presence routes _get_access_token through
# the patched urlopen (token exchange) rather than the gcloud CLI fallback.
FAKE_OAUTH_CREDS = json.dumps(
    {
        "refresh_token": "fake-refresh-token",
        "client_id": "fake-client-id.apps.googleusercontent.com",
        "client_secret": "fake-client-secret",
    }
)


class _FakeResponse:
    """Context-manager stand-in for an http.client.HTTPResponse."""

    def __init__(self, body: bytes):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self) -> bytes:
        return self._body


def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(url=SHEETS_HOST, code=code, msg="error", hdrs={}, fp=None)


class _UrlopenRecorder:
    """A fake urlopen that branches on the request URL.

    Records every URL it sees so tests can assert which boundary fired (token
    exchange vs. sheets read) and detect the no-token short-circuit.
    """

    def __init__(self, *, sheets_result):
        # sheets_result: either bytes to return, or an Exception to raise.
        self.sheets_result = sheets_result
        self.urls: list[str] = []

    def __call__(self, req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        self.urls.append(url)

        if url.startswith(OAUTH_TOKEN_URL):
            return _FakeResponse(json.dumps({"access_token": FAKE_ACCESS_TOKEN}).encode())

        if url.startswith(SHEETS_HOST):
            if isinstance(self.sheets_result, Exception):
                raise self.sheets_result
            return _FakeResponse(self.sheets_result)

        raise AssertionError(f"unexpected URL hit real network: {url}")

    @property
    def token_called(self) -> bool:
        return any(u.startswith(OAUTH_TOKEN_URL) for u in self.urls)

    @property
    def sheets_called(self) -> bool:
        return any(u.startswith(SHEETS_HOST) for u in self.urls)


@pytest.fixture
def with_creds(monkeypatch):
    monkeypatch.setenv("GOOGLE_OAUTH_CREDENTIALS", FAKE_OAUTH_CREDS)


def test_success_returns_parsed_rounds(monkeypatch, with_creds):
    # Real-shaped Sheets values response for the Details!A2:F range.
    body = json.dumps(
        {
            "range": "Details!A2:F5000",
            "majorDimension": "ROWS",
            "values": [
                ["21-Jul", "A", "Stu", "153", "Wing Point", "3:55:00"],
                ["21-Jul", "A", "Tony", "-153", "Wing Point", "3:55:00"],
            ],
        }
    ).encode()
    fake = _UrlopenRecorder(sheets_result=body)
    monkeypatch.setattr("urllib.request.urlopen", fake)

    rounds = SpreadsheetSyncService("sheet-id").get_all_rounds()

    # Both boundaries fired: token exchange then values read.
    assert fake.token_called
    assert fake.sheets_called
    # Parsed into RoundResult objects with correct field extraction.
    assert len(rounds) == 2
    assert rounds[0].date == "21-Jul"
    assert rounds[0].member == "Stu"
    assert rounds[0].score == 153
    assert rounds[0].location == "Wing Point"
    assert rounds[0].duration == "3:55:00"
    assert rounds[1].member == "Tony"
    assert rounds[1].score == -153


def test_expired_token_401_swallowed_no_retry(monkeypatch, with_creds):
    # urllib raises HTTPError(401); the broad except swallows it. There is NO
    # refresh-retry — a single sheets request fires, then [] is returned.
    fake = _UrlopenRecorder(sheets_result=_http_error(401))
    monkeypatch.setattr("urllib.request.urlopen", fake)

    rounds = SpreadsheetSyncService("sheet-id").get_all_rounds()

    assert rounds == []
    assert fake.sheets_called  # the read was attempted, not short-circuited
    # No retry: exactly one sheets call (plus the one token exchange).
    assert sum(u.startswith(SHEETS_HOST) for u in fake.urls) == 1


def test_forbidden_403_swallowed(monkeypatch, with_creds):
    fake = _UrlopenRecorder(sheets_result=_http_error(403))
    monkeypatch.setattr("urllib.request.urlopen", fake)

    rounds = SpreadsheetSyncService("sheet-id").get_all_rounds()

    assert rounds == []
    assert fake.sheets_called


def test_server_error_500_swallowed(monkeypatch, with_creds):
    fake = _UrlopenRecorder(sheets_result=_http_error(500))
    monkeypatch.setattr("urllib.request.urlopen", fake)

    rounds = SpreadsheetSyncService("sheet-id").get_all_rounds()

    assert rounds == []
    assert fake.sheets_called


def test_timeout_swallowed(monkeypatch, with_creds):
    fake = _UrlopenRecorder(sheets_result=TimeoutError("read timed out"))
    monkeypatch.setattr("urllib.request.urlopen", fake)

    rounds = SpreadsheetSyncService("sheet-id").get_all_rounds()

    assert rounds == []
    assert fake.sheets_called  # request attempted before timing out


def test_malformed_body_swallowed(monkeypatch, with_creds):
    # 200 OK but body is not valid JSON → json.loads raises → swallowed → [].
    fake = _UrlopenRecorder(sheets_result=b"<html>not json</html>")
    monkeypatch.setattr("urllib.request.urlopen", fake)

    rounds = SpreadsheetSyncService("sheet-id").get_all_rounds()

    assert rounds == []
    assert fake.sheets_called


def test_valid_json_without_values_key_returns_empty(monkeypatch, with_creds):
    # 200 OK, valid JSON, but no "values" key (empty sheet shape).
    fake = _UrlopenRecorder(sheets_result=json.dumps({"range": "Details!A2:F5000"}).encode())
    monkeypatch.setattr("urllib.request.urlopen", fake)

    rounds = SpreadsheetSyncService("sheet-id").get_all_rounds()

    assert rounds == []
    assert fake.sheets_called


def test_no_token_short_circuits_without_sheets_call(monkeypatch):
    # No GOOGLE_OAUTH_CREDENTIALS and gcloud fallback neutralized → no token →
    # _sheets_api_get returns None before any sheets request → [].
    monkeypatch.delenv("GOOGLE_OAUTH_CREDENTIALS", raising=False)
    monkeypatch.setattr(
        "app.services.spreadsheet_sync_service._get_access_token",
        lambda: None,
    )
    fake = _UrlopenRecorder(sheets_result=b'{"values": [["x"]]}')
    monkeypatch.setattr("urllib.request.urlopen", fake)

    rounds = SpreadsheetSyncService("sheet-id").get_all_rounds()

    assert rounds == []
    assert fake.sheets_called is False  # short-circuited; no network at all
