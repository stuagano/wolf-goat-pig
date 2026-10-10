"""Round story pages: the foursome, public comments, and who may delete one."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.usefixtures("mock_admin_identity")

client = TestClient(app)


def _round(member, score, group="A", location="Wing Point", date="2026-10-06"):
    return SimpleNamespace(
        date="6-Oct",
        date_sortable=date,
        group=group,
        member=member,
        score=score,
        location=location,
    )


def _service(*rounds):
    service = MagicMock()
    service.get_season_rounds.return_value = list(rounds)
    return service


class TestRoundStory:
    @patch("app.routers.round_stories.profile_ids_by_member", return_value={"coulburn": 4})
    @patch("app.routers.round_stories.get_unified_data_service")
    def test_oct_6_shows_coulburn_losing_400(self, mock_service, _names):
        mock_service.return_value = _service(
            _round("Coulburn", -400),
            _round("Stuart Gano", 200),
        )
        with patch("app.routers.round_stories._comments", return_value=[]):
            resp = client.get("/data/rounds/2026-10-06/A", params={"location": "Wing Point"})

        assert resp.status_code == 200
        body = resp.json()
        coulburn = next(player for player in body["players"] if player["member"] == "Coulburn")
        assert coulburn["quarters"] == -400
        assert coulburn["player_id"] == 4
        assert body["comments"] == []

    @patch("app.routers.round_stories.profile_ids_by_member", return_value={})
    @patch("app.routers.round_stories.get_unified_data_service")
    def test_sheet_date_in_the_url_still_finds_the_round(self, mock_service, _names):
        mock_service.return_value = _service(_round("Coulburn", -400))
        with patch("app.routers.round_stories._comments", return_value=[]):
            resp = client.get("/data/rounds/6-Oct/A", params={"location": "Wing Point"})

        assert resp.status_code == 200
        body = resp.json()
        assert body["date_sortable"] == "2026-10-06"
        assert body["players"][0]["quarters"] == -400

    @patch("app.routers.round_stories.get_unified_data_service")
    def test_missing_round_is_404(self, mock_service):
        mock_service.return_value = _service()
        resp = client.get("/data/rounds/2026-10-06/A")
        assert resp.status_code == 404

    @patch("app.routers.round_stories.get_unified_data_service")
    def test_signed_in_player_can_comment(self, mock_service):
        mock_service.return_value = _service(_round("Coulburn", -400))
        db = MagicMock()

        def override_db():
            yield db

        from app.database import get_db

        app.dependency_overrides[get_db] = override_db

        def refresh(comment):
            comment.id = 15

        db.refresh.side_effect = refresh
        try:
            resp = client.post(
                "/data/rounds/2026-10-06/A/comments",
                params={"location": "Wing Point"},
                json={"body": "Coulburn never recovered after the turn."},
                headers={"X-Admin-Email": "player@example.com"},
            )
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert resp.status_code == 200, resp.text
        assert resp.json()["body"] == "Coulburn never recovered after the turn."
        assert resp.json()["id"] == 15
        db.commit.assert_called_once()

    @patch("app.routers.round_stories.get_unified_data_service")
    def test_blank_comment_is_rejected(self, mock_service):
        mock_service.return_value = _service(_round("Coulburn", -400))
        resp = client.post(
            "/data/rounds/2026-10-06/A/comments",
            params={"location": "Wing Point"},
            json={"body": "   "},
            headers={"X-Admin-Email": "player@example.com"},
        )
        assert resp.status_code == 422

    def test_comment_requires_a_signed_in_player(self):
        from app.services.auth_service import get_current_user

        app.dependency_overrides.pop(get_current_user, None)
        resp = client.post(
            "/data/rounds/2026-10-06/A/comments",
            json={"body": "hello"},
        )
        assert resp.status_code == 401

    @patch("app.routers.round_stories.admin_role", return_value="normal")
    def test_someone_else_cannot_delete(self, _role):
        comment = SimpleNamespace(id=9, author_profile_id=123)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = comment

        def override_db():
            yield db

        from app.database import get_db

        app.dependency_overrides[get_db] = override_db
        try:
            resp = client.delete("/data/rounds/comments/9", headers={"X-Admin-Email": "player@example.com"})
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert resp.status_code == 403
        db.delete.assert_not_called()

    @patch("app.routers.round_stories.admin_role", return_value="admin")
    def test_admin_can_delete(self, _role):
        comment = SimpleNamespace(id=9, author_profile_id=123)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = comment

        def override_db():
            yield db

        from app.database import get_db

        app.dependency_overrides[get_db] = override_db
        try:
            resp = client.delete("/data/rounds/comments/9", headers={"X-Admin-Email": "stuagano@gmail.com"})
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert resp.status_code == 200
        db.delete.assert_called_once_with(comment)

    @patch("app.routers.round_stories._reactions", return_value=[])
    @patch("app.routers.round_stories.get_unified_data_service")
    def test_round_reaction_toggles_on(self, mock_service, reactions):
        mock_service.return_value = _service(_round("Coulburn", -400))
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        def override_db():
            yield db

        from app.database import get_db

        app.dependency_overrides[get_db] = override_db
        try:
            resp = client.post(
                "/data/rounds/2026-10-06/A/reactions",
                params={"location": "Wing Point"},
                json={"emoji": "😭"},
                headers={"X-Admin-Email": "player@example.com"},
            )
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert resp.status_code == 200, resp.text
        added = db.add.call_args.args[0]
        assert added.emoji == "😭"
        assert added.comment_id is None
        reactions.assert_called_once()

    @patch("app.routers.round_stories._reactions", return_value=[])
    @patch("app.routers.round_stories.get_unified_data_service")
    def test_tapping_your_reaction_again_removes_it(self, mock_service, _reactions):
        mock_service.return_value = _service(_round("Coulburn", -400))
        existing = SimpleNamespace(emoji="😭", comment_id=None, profile_id=999)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing

        def override_db():
            yield db

        from app.database import get_db

        app.dependency_overrides[get_db] = override_db
        try:
            resp = client.post(
                "/data/rounds/2026-10-06/A/reactions",
                params={"location": "Wing Point"},
                json={"emoji": "😭"},
                headers={"X-Admin-Email": "player@example.com"},
            )
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert resp.status_code == 200, resp.text
        db.delete.assert_called_once_with(existing)
        db.add.assert_not_called()

    @patch("app.routers.round_stories.get_unified_data_service")
    def test_unknown_emoji_is_rejected(self, mock_service):
        mock_service.return_value = _service(_round("Coulburn", -400))
        resp = client.post(
            "/data/rounds/2026-10-06/A/reactions",
            params={"location": "Wing Point"},
            json={"emoji": "🚀"},
            headers={"X-Admin-Email": "player@example.com"},
        )
        assert resp.status_code == 422

    @patch("app.routers.round_stories._comment_reactions", return_value=[])
    def test_comment_reaction_is_tied_to_that_comment(self, reactions):
        comment = SimpleNamespace(
            id=9,
            round_date="2026-10-06",
            round_group="A",
            location="Wing Point",
            author_profile_id=4,
        )
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [comment, None]

        def override_db():
            yield db

        from app.database import get_db

        app.dependency_overrides[get_db] = override_db
        try:
            resp = client.post(
                "/data/rounds/comments/9/reactions",
                json={"emoji": "🔥"},
                headers={"X-Admin-Email": "player@example.com"},
            )
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert resp.status_code == 200, resp.text
        added = db.add.call_args.args[0]
        assert added.emoji == "🔥"
        assert added.comment_id == 9
        reactions.assert_called_once()
