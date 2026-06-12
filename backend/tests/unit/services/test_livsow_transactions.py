"""Unit tests for the LivSow transaction diff engine (pure functions)."""

from app.services.livsow_transactions import (
    compact_roster,
    describe_transaction,
    diff_rosters,
    player_count,
    roster_hash,
)


def _leaderboard(teams, free_agents=()):
    """Build a leaderboard-shaped dict from {team: [(name, role), ...]}."""
    return {
        "teams": [
            {
                "name": team,
                "players": [{"name": n, "role": r, "total": 7, "count": 2, "weeks": {"6/1": 3}} for n, r in players],
            }
            for team, players in teams.items()
        ],
        "free_agents": [{"name": n, "total": 0, "count": 0, "weeks": {}} for n in free_agents],
        "weeks": ["6/1", "6/8"],
    }


BASE = _leaderboard(
    {
        "High Beta": [("Gregg Colburn", "Captain"), ("Allen Avery", "Starter")],
        "Vice Grips": [("Hart Williams", "Captain"), ("Stuart Gano", "Alternate")],
    },
    free_agents=["Dom Lacie", "Scott Morrison"],
)


class TestCompactRoster:
    def test_strips_stats_and_sorts(self):
        compact = compact_roster(BASE)
        assert compact["teams"]["High Beta"] == [
            {"name": "Gregg Colburn", "role": "Captain"},
            {"name": "Allen Avery", "role": "Starter"},
        ]
        assert compact["free_agents"] == ["Dom Lacie", "Scott Morrison"]

    def test_hash_stable_under_stats_churn(self):
        a = compact_roster(BASE)
        churned = _leaderboard(
            {
                "High Beta": [("Gregg Colburn", "Captain"), ("Allen Avery", "Starter")],
                "Vice Grips": [("Hart Williams", "Captain"), ("Stuart Gano", "Alternate")],
            },
            free_agents=["Dom Lacie", "Scott Morrison"],
        )
        churned["teams"][0]["players"][0]["total"] = 99  # weekly score change
        assert roster_hash(a) == roster_hash(compact_roster(churned))

    def test_player_count(self):
        assert player_count(compact_roster(BASE)) == 6


class TestDiffRosters:
    def _diff(self, curr_leaderboard):
        return diff_rosters(compact_roster(BASE), compact_roster(curr_leaderboard))

    def test_no_change(self):
        assert self._diff(BASE) == []

    def test_signing_from_free_agency(self):
        curr = _leaderboard(
            {
                "High Beta": [
                    ("Gregg Colburn", "Captain"),
                    ("Allen Avery", "Starter"),
                    ("Dom Lacie", "Alternate"),
                ],
                "Vice Grips": [("Hart Williams", "Captain"), ("Stuart Gano", "Alternate")],
            },
            free_agents=["Scott Morrison"],
        )
        txns = self._diff(curr)
        assert len(txns) == 1
        t = txns[0]
        assert t["type"] == "signed"
        assert t["player_name"] == "Dom Lacie"
        assert t["to_team"] == "High Beta"
        assert t["to_role"] == "Alternate"

    def test_release_to_free_agency(self):
        curr = _leaderboard(
            {
                "High Beta": [("Gregg Colburn", "Captain")],
                "Vice Grips": [("Hart Williams", "Captain"), ("Stuart Gano", "Alternate")],
            },
            free_agents=["Dom Lacie", "Scott Morrison", "Allen Avery"],
        )
        txns = self._diff(curr)
        assert len(txns) == 1
        assert txns[0]["type"] == "released"
        assert txns[0]["from_team"] == "High Beta"

    def test_trade_between_teams(self):
        curr = _leaderboard(
            {
                "High Beta": [("Gregg Colburn", "Captain")],
                "Vice Grips": [
                    ("Hart Williams", "Captain"),
                    ("Stuart Gano", "Alternate"),
                    ("Allen Avery", "Starter"),
                ],
            },
            free_agents=["Dom Lacie", "Scott Morrison"],
        )
        txns = self._diff(curr)
        assert len(txns) == 1
        t = txns[0]
        assert t["type"] == "traded"
        assert (t["from_team"], t["to_team"]) == ("High Beta", "Vice Grips")

    def test_role_change_same_team(self):
        curr = _leaderboard(
            {
                "High Beta": [("Gregg Colburn", "Captain"), ("Allen Avery", "Alternate")],
                "Vice Grips": [("Hart Williams", "Captain"), ("Stuart Gano", "Alternate")],
            },
            free_agents=["Dom Lacie", "Scott Morrison"],
        )
        txns = self._diff(curr)
        assert len(txns) == 1
        assert txns[0]["type"] == "role_change"
        assert (txns[0]["from_role"], txns[0]["to_role"]) == ("Starter", "Alternate")

    def test_rename_detection_not_departed_joined(self):
        # Typo fix in the same team+role slot must be a single 'renamed' row
        curr = _leaderboard(
            {
                "High Beta": [("Gregg Colburn", "Captain"), ("Alan Avery", "Starter")],
                "Vice Grips": [("Hart Williams", "Captain"), ("Stuart Gano", "Alternate")],
            },
            free_agents=["Dom Lacie", "Scott Morrison"],
        )
        txns = self._diff(curr)
        assert len(txns) == 1
        t = txns[0]
        assert t["type"] == "renamed"
        assert t["details"] == {"from_name": "Allen Avery", "to_name": "Alan Avery"}

    def test_genuinely_different_player_not_renamed(self):
        # Different name in the same slot → departed + signed, not renamed
        curr = _leaderboard(
            {
                "High Beta": [("Gregg Colburn", "Captain"), ("Zeke Brand", "Starter")],
                "Vice Grips": [("Hart Williams", "Captain"), ("Stuart Gano", "Alternate")],
            },
            free_agents=["Dom Lacie", "Scott Morrison"],
        )
        types = sorted(t["type"] for t in self._diff(curr))
        assert types == ["departed", "signed"]

    def test_new_free_agent_joins_league(self):
        curr = _leaderboard(
            {
                "High Beta": [("Gregg Colburn", "Captain"), ("Allen Avery", "Starter")],
                "Vice Grips": [("Hart Williams", "Captain"), ("Stuart Gano", "Alternate")],
            },
            free_agents=["Dom Lacie", "Scott Morrison", "Billy Moses"],
        )
        txns = self._diff(curr)
        assert len(txns) == 1
        assert txns[0]["type"] == "joined"
        assert txns[0]["player_name"] == "Billy Moses"

    def test_departure_from_league(self):
        curr = _leaderboard(
            {
                "High Beta": [("Gregg Colburn", "Captain"), ("Allen Avery", "Starter")],
                "Vice Grips": [("Hart Williams", "Captain"), ("Stuart Gano", "Alternate")],
            },
            free_agents=["Dom Lacie"],  # Scott Morrison gone entirely
        )
        txns = self._diff(curr)
        assert len(txns) == 1
        assert txns[0]["type"] == "departed"

    def test_whitespace_and_case_normalization(self):
        curr = _leaderboard(
            {
                "High Beta": [("gregg  colburn", "Captain"), ("Allen Avery", "Starter")],
                "Vice Grips": [("Hart Williams", "Captain"), ("Stuart Gano", "Alternate")],
            },
            free_agents=["Dom Lacie", "Scott Morrison"],
        )
        # Same person, just formatting noise — same normalized key, same slot
        assert self._diff(curr) == []


class TestDescriptions:
    def test_each_type_has_readable_description(self):
        samples = [
            {
                "type": "signed",
                "player_name": "A",
                "to_team": "T",
                "to_role": "Starter",
                "from_team": None,
                "from_role": None,
                "details": None,
            },
            {
                "type": "released",
                "player_name": "A",
                "from_team": "T",
                "to_team": None,
                "from_role": "Starter",
                "to_role": None,
                "details": None,
            },
            {
                "type": "traded",
                "player_name": "A",
                "from_team": "T1",
                "to_team": "T2",
                "from_role": "Starter",
                "to_role": "Alternate",
                "details": None,
            },
            {
                "type": "role_change",
                "player_name": "A",
                "from_team": "T",
                "to_team": "T",
                "from_role": "Starter",
                "to_role": "Captain",
                "details": None,
            },
            {
                "type": "joined",
                "player_name": "A",
                "from_team": None,
                "to_team": None,
                "from_role": None,
                "to_role": "Free Agent",
                "details": None,
            },
            {
                "type": "departed",
                "player_name": "A",
                "from_team": "T",
                "to_team": None,
                "from_role": "Starter",
                "to_role": None,
                "details": None,
            },
            {
                "type": "renamed",
                "player_name": "B",
                "from_team": "T",
                "to_team": "T",
                "from_role": "Starter",
                "to_role": "Starter",
                "details": {"from_name": "A", "to_name": "B"},
            },
        ]
        for s in samples:
            desc = describe_transaction(s)
            assert isinstance(desc, str) and len(desc) > 5


class TestMigrationsRunner:
    """Statement splitting + dialect guard for the SQL migration runner."""

    def test_statement_splitting_strips_comments(self):
        from app.migrations_runner import _statements

        sql = """-- Migration: add emoji column
ALTER TABLE badges ADD COLUMN IF NOT EXISTS emoji VARCHAR;
-- another comment
CREATE INDEX IF NOT EXISTS ix_x ON badges (emoji);
"""
        stmts = _statements(sql)
        assert len(stmts) == 2
        assert stmts[0].startswith("ALTER TABLE badges")
        assert stmts[1].startswith("CREATE INDEX")

    def test_sqlite_engine_is_skipped(self):
        from app.database import engine
        from app.migrations_runner import run_sql_migrations

        if engine.dialect.name != "postgresql":
            assert run_sql_migrations(engine) == {"skipped": "not_postgres"}

    def test_benign_error_detection(self):
        from app.migrations_runner import _BENIGN_ERROR_RE

        assert _BENIGN_ERROR_RE.search('column "emoji" of relation "badges" already exists')
        assert _BENIGN_ERROR_RE.search("duplicate column name: emoji")
        assert not _BENIGN_ERROR_RE.search("syntax error at or near ALTER")
