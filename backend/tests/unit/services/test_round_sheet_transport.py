"""Actual HTTP request construction with synthetic provider responses; no network."""

import json

from app.services import spreadsheet_sync_service as sheet


class Response:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return b'{"spreadsheetId": "synthetic", "updatedRows": 2}'


def test_update_transport_changes_cells_only_preserving_other_columns(monkeypatch):
    requests = []
    monkeypatch.setattr(sheet, "_get_access_token", lambda: "synthetic-credential")

    def open_request(request, timeout):
        requests.append(request)
        assert timeout == 30
        return Response()

    monkeypatch.setattr(sheet.urllib.request, "urlopen", open_request)
    receipt = sheet._sheets_identity_write(
        "synthetic",
        "'Synthetic ! Tab'!A:J",
        [["new", "keep", "new-operation"]],
        updates=[(9, ["new", "keep", "new-operation"], ["old", "keep", "old-operation"])],
    )
    assert receipt["spreadsheetId"] == "synthetic" and len(requests) == 1
    request = requests[0]
    body = json.loads(request.data)
    assert request.full_url.endswith("/values:batchUpdate")
    assert body == {
        "valueInputOption": "RAW",
        "data": [
            {"range": "'Synthetic ! Tab'!A9", "values": [["new"]]},
            {"range": "'Synthetic ! Tab'!C9", "values": [["new-operation"]]},
        ],
    }


def test_append_transport_is_single_raw_request_and_retains_receipt(monkeypatch):
    requests = []
    monkeypatch.setattr(sheet, "_get_access_token", lambda: "synthetic-credential")
    monkeypatch.setattr(sheet.urllib.request, "urlopen", lambda req, timeout: requests.append(req) or Response())
    rows = [["2026-10-01", "A", "Guest", 1.5, "Course", "", "round", "slot", "operation"]]
    receipt = sheet._sheets_identity_write("synthetic", "'Tab'!A:I", rows)
    assert receipt["updatedRows"] == 2 and len(requests) == 1
    assert "valueInputOption=RAW" in requests[0].full_url
    assert json.loads(requests[0].data) == {"values": rows}


def test_legacy_unbound_write_helper_cannot_reach_transport(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("unbound write bypass")

    monkeypatch.setattr(sheet.urllib.request, "urlopen", forbidden)
    assert sheet.SpreadsheetSyncService("synthetic").add_round_results([]) is False
