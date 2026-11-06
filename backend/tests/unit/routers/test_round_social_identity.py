"""UUID social HTTP operations preserve existing records; local databases only."""

import pytest

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


@pytest.mark.parametrize("comment_id", [None, 51])
def test_converged_alias_reactions_are_one_logical_vote_and_toggle_off_completely(round_api, comment_id):
    client, _, sessions, game_id = prepare(round_api)
    with sessions() as db:
        db.add(models.RoundAlias(date_key="2026-10-06", group="B", location="New", game_id=game_id))
        for index, (date, group, location, owner) in enumerate(
            [
                ("06-Oct", "A", "Old", None),
                ("2026-10-06", "B", "New", None),
                (f"uuid:{game_id}", "", "", game_id),
            ]
        ):
            db.add(
                models.RoundReaction(
                    id=100 + index,
                    game_id=owner,
                    round_date=date,
                    round_group=group,
                    location=location,
                    profile_id=8,
                    comment_id=comment_id,
                    emoji="🔥",
                    created_at="2026-10-06",
                )
            )
        db.add_all(
            [
                models.RoundReaction(
                    id=110,
                    game_id=game_id,
                    round_date=f"uuid:{game_id}",
                    round_group="",
                    location="",
                    profile_id=7,
                    comment_id=comment_id,
                    emoji="🔥",
                    created_at="2026-10-06",
                ),
                models.RoundReaction(
                    id=111,
                    game_id=game_id,
                    round_date=f"uuid:{game_id}",
                    round_group="",
                    location="",
                    profile_id=8,
                    comment_id=comment_id,
                    emoji="👏",
                    created_at="2026-10-06",
                ),
                models.RoundReaction(
                    id=112,
                    game_id="unrelated",
                    round_date="other",
                    round_group="",
                    location="",
                    profile_id=8,
                    comment_id=comment_id,
                    emoji="🔥",
                    created_at="2026-10-06",
                ),
            ]
        )
        db.commit()
    url = f"/data/rounds/uuid/{game_id}/discussion"
    data = client.get(url).json()
    reactions = data["reactions"] if comment_id is None else data["comments"][0]["reactions"]
    assert next(r for r in reactions if r["emoji"] == "🔥")["count"] == 2
    with sessions() as db:
        assert db.query(models.RoundReaction).count() == 6  # Projection never migrates/deletes history.
    path = f"/data/rounds/uuid/{game_id}/reactions" if comment_id is None else "/data/rounds/comments/51/reactions"
    off = client.post(path, json={"emoji": "🔥"})
    assert off.status_code == 200, off.text
    assert next(r for r in off.json() if r["emoji"] == "🔥")["count"] == 1
    with sessions() as db:
        assert {r.id for r in db.query(models.RoundReaction)} == {110, 111, 112}
        assert db.get(models.RoundComment, 51).created_at == "2026-10-06T10:00:00"
    on = client.post(path, json={"emoji": "🔥"})
    assert on.status_code == 200
    assert next(r for r in on.json() if r["emoji"] == "🔥")["count"] == 2
    with sessions() as db:
        assert (
            db.query(models.RoundReaction)
            .filter_by(game_id=game_id, profile_id=8, emoji="🔥", comment_id=comment_id)
            .count()
            == 1
        )


@pytest.mark.parametrize("comment_id", [None, 51])
def test_uuid_and_resolved_alias_toggles_serialize_on_postgres(round_api, comment_id):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    client, _, sessions, game_id = prepare(round_api)
    if sessions.kw["bind"].dialect.name != "postgresql":
        # SQLite fixture has one shared connection, not a concurrency substitute.
        return
    gate = Barrier(2)
    alias_path = (
        "/data/rounds/06-Oct/A/reactions?location=Old" if comment_id is None else "/data/rounds/comments/51/reactions"
    )
    uuid_path = f"/data/rounds/uuid/{game_id}/reactions" if comment_id is None else alias_path

    def toggle(path):
        gate.wait(timeout=5)
        return client.post(path, json={"emoji": "🔥"})

    # Start absent: two serialized toggles are ON then OFF, not two ON rows.
    for _ in range(4):
        with ThreadPoolExecutor(max_workers=2) as pool:
            calls = [pool.submit(toggle, path) for path in (uuid_path, alias_path)]
            assert all(call.result(timeout=10).status_code == 200 for call in calls)
        with sessions() as db:
            assert db.query(models.RoundReaction).count() == 0


def test_social_writes_wait_for_ownership_convergence_lock_on_postgres(round_api):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from app.services.round_identity import acquire_reconciliation_lock

    client, _, sessions, game_id = prepare(round_api)
    if sessions.kw["bind"].dialect.name != "postgresql":
        return
    started = Event()
    with sessions() as binding, ThreadPoolExecutor(max_workers=1) as pool:
        acquire_reconciliation_lock(binding)
        binding.add(models.RoundAlias(date_key="new-alias", group="B", location="", game_id=game_id))
        binding.flush()

        def toggle():
            started.set()
            return client.post("/data/rounds/new-alias/B/reactions", json={"emoji": "🔥"})

        call = pool.submit(toggle)
        assert started.wait(5)
        # Verify the actual DB advisory wait, not elapsed-time assumptions.
        import time

        from sqlalchemy import text

        for _ in range(100):
            binding.execute(text("SELECT pg_stat_clear_snapshot()"))
            waiting = binding.execute(
                text(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND wait_event='advisory' AND pid <> pg_backend_pid()"
                )
            ).scalar()
            if waiting:
                break
            time.sleep(0.01)
        assert waiting and not call.done()
        binding.commit()
        response = call.result(timeout=10)
        assert response.status_code == 200, response.text
    with sessions() as db:
        reaction = db.query(models.RoundReaction).one()
        assert reaction.game_id == game_id


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
