"""UUID social HTTP operations preserve existing records; local databases only."""

from app import models
from app.routers import round_stories
from tests.unit.routers.test_round_reconciliation_api import login, round_api, seed


def prepare(round_api):
    client, app, sessions = round_api
    app.include_router(round_stories.router)
    game_id, *_ = seed(sessions)
    login(app, sessions)
    with sessions() as db:
        db.add(models.RoundAlias(date_key="06-Oct", group="A", location="Old", game_id=game_id))
        db.add(
            models.RoundComment(
                id=51,
                round_date="06-Oct",
                round_group="A",
                location="Old",
                author_profile_id=8,
                body="Original",
                created_at="2026-10-06T10:00:00",
            )
        )
        db.commit()
    return client, app, sessions, game_id


def test_uuid_and_alias_share_comment_ids_and_reactions(round_api):
    client, app, sessions, game_id = prepare(round_api)
    url = f"/data/rounds/uuid/{game_id}/discussion"
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()["comments"][0]["id"] == 51
    for path in (f"/data/rounds/uuid/{game_id}/reactions", "/data/rounds/06-Oct/A/reactions?location=Old"):
        response = client.post(path, json={"emoji": "🔥"})
        assert response.status_code == 200
    with sessions() as db:
        assert db.query(models.RoundReaction).count() == 0
        assert db.get(models.RoundComment, 51).created_at == "2026-10-06T10:00:00"
        assert db.get(models.RoundComment, 51).game_id is None  # GET never migrates
    created = client.post(f"/data/rounds/uuid/{game_id}/comments", json={"body": "New"})
    assert created.status_code == 200
    new_id = created.json()["id"]
    alias_read = client.get("/data/rounds/06-Oct/A?location=Old")
    assert alias_read.status_code == 200, alias_read.text
    assert [c["id"] for c in alias_read.json()["comments"]] == [51, new_id]
    with sessions() as db:
        assert db.get(models.RoundComment, new_id).game_id == game_id
        notes = db.query(models.Notification).filter_by(notification_type="round_comment").all()
        assert notes and all(n.data["path"] == f"/game/{game_id}" for n in notes)
    assert client.post("/data/rounds/06-Oct/A/comments?location=Old", json={"body": "Alias reply"}).status_code == 200
    assert len(client.get(url).json()["comments"]) == 3
    login(app, sessions, 7)
    assert client.delete(f"/data/rounds/comments/{new_id}").status_code == 403
    login(app, sessions, 8)
    assert client.delete(f"/data/rounds/comments/{new_id}").status_code == 200


def test_ambiguous_alias_never_attaches_or_accepts_writes(round_api):
    client, app, sessions, game_id = prepare(round_api)
    with sessions() as db:
        db.add(models.RoundAlias(date_key="06-Oct", group="A", location="Old", game_id="other"))
        db.commit()
    assert client.post("/data/rounds/06-Oct/A/comments?location=Old", json={"body": "No guess"}).status_code == 409
    assert client.post("/data/rounds/06-Oct/A/reactions?location=Old", json={"emoji": "🔥"}).status_code == 409
    assert client.get(f"/data/rounds/uuid/{game_id}/discussion").json()["comments"] == []
    assert client.post("/data/rounds/comments/51/reactions", json={"emoji": "🔥"}).status_code == 409
    assert client.delete("/data/rounds/comments/51").status_code == 409
    with sessions() as db:
        assert db.query(models.RoundComment).count() == 1
        assert db.query(models.RoundReaction).count() == 0
