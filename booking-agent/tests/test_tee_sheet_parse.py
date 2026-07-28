from pathlib import Path

from app.tee_sheet import parse_tee_sheet

FIXTURE = Path(__file__).parent / "fixtures" / "member_sheet_sample.html"


def test_parse_tee_sheet_extracts_players_and_open_slots():
    html = FIXTURE.read_text()
    slots = parse_tee_sheet(html, "2026-07-28")
    assert len(slots) == 1
    slot = slots[0]
    assert slot["date"] == "2026-07-28"
    assert slot["time"] == "11:00 AM"
    assert slot["ttdata"] == "abc123"
    assert slot["jump"] == 7
    assert slot["p5_allowed"] is False
    assert slot["players"] == [{"name": "Jane D", "transport": "WLK"}]
    assert slot["max_players"] == 4
    assert slot["open_slots"] == 3
    assert slot["front_back"] == "F"


def test_parse_tee_sheet_skips_non_member_slot():
    html = '<a data-ftjson="{&quot;type&quot;:&quot;Event&quot;,&quot;jump&quot;:1}"></a>'
    assert parse_tee_sheet(html, "2026-07-28") == []
