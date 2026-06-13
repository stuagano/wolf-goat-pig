"""Router tests for LivSow transactions/teams/snapshot endpoints.

The Google Sheet fetch is mocked via get_livsow_leaderboard so tests are
hermetic; snapshot state lives in the test DB.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services import livsow_transactions

client = TestClient(app)


def _leaderboard(avery_team="High Beta"):
    """Two-team league; avery_team controls where Allen Avery plays."""
    teams = {
        "High Beta": [("Gregg Colburn", "Captain")],
        "Vice Grips": [("Hart Williams", "Captain"), ("Stuart Gano", "Alternate")],
    }
    teams[avery_team] = teams[avery_team] + [("Allen Avery", "Starter")]
    return {
        "teams": [
            {
                "name": name,
                "rank": i + 1,
                "total": 10 - i,
                "players": [
                    {
                        "name": n,
                        "role": r,
                        "total": 5,
                        "count": 2,
                        "weeks": {"6/1": 2},
                        "best_scores": [3, 2],
                        "team_contribution": 5,
                    }
                    for n, r in players
                ],
            }
            for i, (name, players) in enumerate(teams.items())
        ],
        "free_agents": [{"name": "Dom Lacie", "total": 0, "count": 0, "weeks": {}}],
        "weeks": ["6/1"],
        "sheet_url": "https://example.com/sheet",
    }


def _clear_livsow_tables():
    from app import models
    from app.database import SessionLocal

    db = SessionLocal()
    db.query(models.LivSowTransaction).delete()
    db.query(models.LivSowRosterSnapshot).delete()
    db.commit()
    db.close()


PATCH_TARGET = "app.routers.unified_data.get_livsow_leaderboard"


class TestSnapshotEndpoint:
    def setup_method(self):
        _clear_livsow_tables()

    def test_first_snapshot_is_baseline(self):
        with patch(PATCH_TARGET, return_value=_leaderboard()):
            resp = client.post("/data/livsow/snapshot")
        assert resp.status_code == 200
        assert resp.json()["status"] == "baseline"

    def test_same_roster_is_no_change(self):
        with patch(PATCH_TARGET, return_value=_leaderboard()):
            client.post("/data/livsow/snapshot")
            resp = client.post("/data/livsow/snapshot")
        assert resp.json()["status"] == "no_change"

    def test_changed_roster_pends_then_force_records(self):
        with patch(PATCH_TARGET, return_value=_leaderboard()):
            client.post("/data/livsow/snapshot")
        with patch(PATCH_TARGET, return_value=_leaderboard(avery_team="Vice Grips")):
            resp = client.post("/data/livsow/snapshot")
            assert resp.json()["status"] == "pending"  # debounce
            resp = client.post("/data/livsow/snapshot?force=true")
        body = resp.json()
        assert body["status"] == "recorded"
        assert body["transactions"] == 1

    def test_empty_fetch_skipped(self):
        with patch(PATCH_TARGET, return_value={"teams": [], "free_agents": [], "weeks": []}):
            resp = client.post("/data/livsow/snapshot")
        assert resp.json() == {"status": "skipped", "reason": "empty_fetch"}


class TestTransactionsEndpoint:
    def setup_method(self):
        _clear_livsow_tables()
        with patch(PATCH_TARGET, return_value=_leaderboard()):
            client.post("/data/livsow/snapshot")
        with patch(PATCH_TARGET, return_value=_leaderboard(avery_team="Vice Grips")):
            client.post("/data/livsow/snapshot?force=true")

    def test_lists_trade_with_description(self):
        resp = client.get("/data/livsow/transactions")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        t = body["transactions"][0]
        assert t["type"] == "traded"
        assert t["player"] == "Allen Avery"
        assert "High Beta" in t["description"] and "Vice Grips" in t["description"]

    def test_filter_by_team(self):
        assert client.get("/data/livsow/transactions?team=High Beta").json()["total"] == 1
        assert client.get("/data/livsow/transactions?team=Nonexistent").json()["total"] == 0

    def test_soft_delete_requires_admin_and_hides_row(self):
        txn_id = client.get("/data/livsow/transactions").json()["transactions"][0]["id"]
        # no admin header → 403
        assert client.delete(f"/data/livsow/transactions/{txn_id}").status_code == 403
        resp = client.delete(
            f"/data/livsow/transactions/{txn_id}",
            headers={"X-Admin-Email": "stuagano@gmail.com"},
        )
        assert resp.status_code == 200
        assert client.get("/data/livsow/transactions").json()["total"] == 0


class TestTeamDetailEndpoint:
    def setup_method(self):
        _clear_livsow_tables()

    def test_team_detail_by_slug(self):
        with patch(PATCH_TARGET, return_value=_leaderboard()):
            resp = client.get("/data/livsow/teams/high-beta")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "High Beta"
        assert body["rank"] == 1
        assert [p["name"] for p in body["players"]] == ["Gregg Colburn", "Allen Avery"]
        assert body["weeks"] == ["6/1"]

    def test_unknown_slug_404(self):
        with patch(PATCH_TARGET, return_value=_leaderboard()):
            resp = client.get("/data/livsow/teams/no-such-team")
        assert resp.status_code == 404

    def test_team_transactions_filtered(self):
        with patch(PATCH_TARGET, return_value=_leaderboard()):
            client.post("/data/livsow/snapshot")
        with patch(PATCH_TARGET, return_value=_leaderboard(avery_team="Vice Grips")):
            client.post("/data/livsow/snapshot?force=true")
            both = client.get("/data/livsow/teams/vice-grips").json()
        assert len(both["transactions"]) == 1
        assert both["transactions"][0]["player"] == "Allen Avery"


def test_debounce_window_constant_reasonable():
    # Guard against accidental edits making the debounce trivially short/long
    assert 10 * 60 <= livsow_transactions.MIN_CONFIRM_SECONDS <= 24 * 3600


class TestProfileMatching:
    def test_exact_and_fuzzy_profile_linking(self):
        from app.routers.unified_data import _match_profile_id

        profiles = {"tyson theilman": 7, "gregg colburn": 3, "ty cobb": 9}
        # exact (case-insensitive)
        assert _match_profile_id("Gregg Colburn", profiles) == 3
        # fuzzy: sheet typo variant of the profile spelling (Thielman vs Theilman)
        assert _match_profile_id("Tyson Thielman", profiles) == 7
        # different person, same-ish name shape: no match
        assert _match_profile_id("Tyson Brand", profiles) is None
        # no profile at all
        assert _match_profile_id("Zeke Nobody", profiles) is None

    def test_fuzzy_requires_unique_match(self):
        from app.routers.unified_data import _match_profile_id

        # Two close candidates with the same first name -> refuse to guess
        profiles = {"dan anders": 1, "dan andersen": 2}
        assert _match_profile_id("Dan Anderson", profiles) is None


class TestTeamContentEditing:
    def _clear(self):
        from app import models
        from app.database import SessionLocal

        db = SessionLocal()
        db.query(models.LivSowTeamContent).delete()
        db.query(models.PlayerProfile).filter(models.PlayerProfile.name.in_(["Gregg Colburn", "Some Rando"])).delete()
        db.commit()
        db.close()

    def _make_profile(self, name, email):
        from app import models
        from app.database import SessionLocal
        from app.utils.time import utc_now

        db = SessionLocal()
        p = models.PlayerProfile(name=name, email=email, created_at=utc_now().isoformat())
        db.add(p)
        db.commit()
        pid = p.id
        db.close()
        return pid

    def _override_user(self, pid):
        from app import models
        from app.database import SessionLocal
        from app.services.auth_service import get_current_user

        def _dep():
            db = SessionLocal()
            u = db.query(models.PlayerProfile).get(pid)
            db.close()
            return u

        app.dependency_overrides[get_current_user] = _dep

    def setup_method(self):
        _clear_livsow_tables()
        self._clear()

    def teardown_method(self):
        from app.services.auth_service import get_current_user

        app.dependency_overrides.pop(get_current_user, None)

    def test_captain_can_edit_their_team(self):
        # High Beta captain is "Gregg Colburn" per the live sheet; create a
        # matching profile and act as them.
        pid = self._make_profile("Gregg Colburn", "gregg@example.com")
        with patch(PATCH_TARGET, return_value=_leaderboard()):
            # _leaderboard()'s High Beta captain is "Gregg Colburn"? No — it's
            # the test fixture. Patch leaderboard to put Gregg as captain.
            lb = _leaderboard()
            lb["teams"][0]["players"][0] = {
                "name": "Gregg Colburn",
                "role": "Captain",
                "total": 5,
                "count": 2,
                "weeks": {"6/1": 2},
                "best_scores": [3, 2],
                "team_contribution": 5,
            }
            with patch(PATCH_TARGET, return_value=lb):
                self._override_user(pid)
                can = client.get("/data/livsow/teams/high-beta/can-edit")
                assert can.json() == {"can_edit": True}
                resp = client.put(
                    "/data/livsow/teams/high-beta/content",
                    json={"motto": "Fear the Beta", "about": "Best team."},
                )
                assert resp.status_code == 200
                assert resp.json()["motto"] == "Fear the Beta"
                assert resp.json()["updated_by"] == "Gregg Colburn"

    def test_non_captain_cannot_edit(self):
        pid = self._make_profile("Some Rando", "rando@example.com")
        lb = _leaderboard()
        lb["teams"][0]["players"][0] = {
            "name": "Gregg Colburn",
            "role": "Captain",
            "total": 5,
            "count": 2,
            "weeks": {},
            "best_scores": [],
            "team_contribution": 0,
        }
        with patch(PATCH_TARGET, return_value=lb):
            self._override_user(pid)
            assert client.get("/data/livsow/teams/high-beta/can-edit").json() == {"can_edit": False}
            resp = client.put(
                "/data/livsow/teams/high-beta/content",
                json={"motto": "hacked"},
            )
            assert resp.status_code == 403

    def test_admin_can_edit_any_team(self):
        pid = self._make_profile("Some Rando", "stuagano@gmail.com")  # admin email
        lb = _leaderboard()
        with patch(PATCH_TARGET, return_value=lb):
            self._override_user(pid)
            assert client.get("/data/livsow/teams/high-beta/can-edit").json() == {"can_edit": True}

    def test_content_surfaces_on_team_detail(self):
        pid = self._make_profile("Gregg Colburn", "gregg@example.com")
        lb = _leaderboard()
        lb["teams"][0]["players"][0] = {
            "name": "Gregg Colburn",
            "role": "Captain",
            "total": 5,
            "count": 2,
            "weeks": {},
            "best_scores": [],
            "team_contribution": 0,
        }
        with patch(PATCH_TARGET, return_value=lb):
            self._override_user(pid)
            client.put("/data/livsow/teams/high-beta/content", json={"announcement": "Tee at 8"})
            # team detail is unauthenticated-readable; content comes through
            detail = client.get("/data/livsow/teams/high-beta").json()
            assert detail["content"]["announcement"] == "Tee at 8"
            assert detail["captain_name"] == "Gregg Colburn"


class TestStarterSeeding:
    def setup_method(self):
        from app import models
        from app.database import SessionLocal

        db = SessionLocal()
        db.query(models.LivSowTeamContent).delete()
        db.commit()
        db.close()

    def test_seed_requires_admin(self):
        resp = client.post("/data/livsow/teams/seed-starters")
        assert resp.status_code == 403

    def test_seed_inserts_and_is_idempotent(self):
        lb = _leaderboard()  # High Beta + Vice Grips fixtures
        with patch(PATCH_TARGET, return_value=lb):
            r1 = client.post(
                "/data/livsow/teams/seed-starters",
                headers={"X-Admin-Email": "stuagano@gmail.com"},
            )
            assert r1.status_code == 200
            assert "high-beta" in r1.json()["seeded"]
            # second run seeds nothing
            r2 = client.post(
                "/data/livsow/teams/seed-starters",
                headers={"X-Admin-Email": "stuagano@gmail.com"},
            )
            assert r2.json()["count"] == 0
        # starter content shows on the team detail
        with patch(PATCH_TARGET, return_value=lb):
            detail = client.get("/data/livsow/teams/high-beta").json()
            assert detail["content"]["motto"]
            assert detail["content"]["updated_by"] == "(starter — edit me)"
