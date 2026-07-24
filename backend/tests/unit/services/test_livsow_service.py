"""CTK-grade contracts for LivSow sheet parsing and cache poisoning guard."""

from app.services import livsow_service


def test_parse_stats_builds_weekly_totals():
    rows = [
        ["Player", "x", "y", "z", "w", "Count", "1/5", "1/12"],
        ["Stuart", "", "", "", "", "2", "10", "8"],
        ["Jeff", "", "", "", "", "1", "4", ""],
    ]
    weeks, players = livsow_service._parse_stats(rows)
    assert weeks == ["1/5", "1/12"]
    assert players["Stuart"]["total"] == 18
    assert players["Stuart"]["weeks"]["1/5"] == 10
    assert players["Jeff"]["weeks"]["1/12"] is None
    assert players["Jeff"]["total"] == 4


def test_parse_roster_ranks_teams_and_lists_free_agents():
    weeks = ["1/5"]
    player_stats = {
        "Alice": {"total": 20, "count": 1, "weeks": {"1/5": 20}},
        "Bob": {"total": 10, "count": 1, "weeks": {"1/5": 10}},
        "Cara": {"total": 5, "count": 1, "weeks": {"1/5": 5}},
    }
    # Row layout: col0 role, then team blocks at offsets 2 and 5
    rows = [
        ["hdr"],
        ["", "", "Team Alpha", "", "", "Team Beta"],
        ["Captain", "", "Alice", "12", "8", "Bob", "6", "4"],
        ["Starter", "", "", "", "", "", "", ""],
        ["", "", "Point Totals"],
        ["", "", "", "30", "", "", "12"],
        ["Free Agent", "", "Cara"],
    ]
    teams, free_agents = livsow_service._parse_roster(rows, weeks, player_stats)
    assert [t["name"] for t in teams] == ["Team Alpha", "Team Beta"]
    assert teams[0]["rank"] == 1
    assert teams[0]["total"] == 30
    assert teams[1]["rank"] == 2
    assert free_agents[0]["name"] == "Cara"


def test_empty_fetch_does_not_poison_cache(monkeypatch):
    livsow_service._cache = {
        "teams": [{"name": "Keep Me", "total": 1, "players": [], "rank": 1}],
        "weeks": [],
        "free_agents": [],
    }
    livsow_service._cache_ts = 0.0
    monkeypatch.setattr(livsow_service, "_fetch_csv", lambda gid: [])

    result = livsow_service.get_livsow_leaderboard(force_refresh=True)
    assert result["teams"] == []
    assert livsow_service._cache["teams"][0]["name"] == "Keep Me"
