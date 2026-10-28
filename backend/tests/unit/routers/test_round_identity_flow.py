"""Synthetic saved scorecard -> persistence -> every round-navigation API."""

from app import models
from app.routers import member_rounds, players, round_stories, unified_data
from app.services.auth_service import get_current_user
from tests.unit.round_identity_postgres_support import identity_pg
from tests.unit.routers.test_round_posting_p1 import round_api


def test_six_player_card_identity_survives_sheet_reconciliation_and_all_entrypoints(round_api):
    client, app, sessions = round_api
    for router in (member_rounds.router, players.router, round_stories.router, unified_data.router):
        app.include_router(router)
    names = ["Avery", "Blair", "Casey", "Devon", "Emery", "Frankie"]
    totals = [147, 82, -8, -16, -66, -139]
    with sessions() as db:
        db.add_all([models.PlayerProfile(id=i, name=name, legacy_name=name) for i, name in enumerate(names, 1)])
        db.commit()
    app.dependency_overrides[get_current_user] = lambda: models.PlayerProfile(id=1, name="Avery", legacy_name="Avery")
    response = client.post(
        "/games/from-scorecard",
        json={
            "players": [{"name": name, "player_profile_id": i} for i, name in enumerate(names, 1)],
            "course_name": "Example Golf & Country Club",
            "played_at": "2026-10-25",
            "per_hole_quarters": [
                {"hole": hole, "player_index": i, "quarters": total if hole == 1 else 0}
                for hole in range(1, 19)
                for i, total in enumerate(totals)
            ],
        },
    )
    assert response.status_code == 200, response.text
    game_id = response.json()["game_id"]
    # Separate transaction simulates the authoritative sheet arriving later.
    with sessions() as db:
        db.add_all(
            [
                models.LegacyRound(
                    date="2026-10-25",
                    group="B",
                    member=name,
                    score=total,
                    location="Example Golf & Country Club",
                    source="primary_sheet",
                )
                for name, total in zip(names, totals)
            ]
        )
        db.commit()
    params = {"location": "Example Golf & Country Club"}
    for path, kwargs in [
        ("/data/rounds/2026-10-25/B", {"params": params}),
        ("/data/leaderboard/rounds", {}),
        ("/data/leaderboard/scores", {"params": {"kind": "best"}}),
        ("/data/rounds", {}),
    ]:
        result = client.get(path, **kwargs)
        assert result.status_code == 200, result.text
        payload = result.json()
        rows = payload if isinstance(payload, list) else [payload]
        assert rows and {row["game_id"] for row in rows} == {game_id}
    story = client.get("/data/rounds/2026-10-25/B", params=params).json()
    assert len(story["players"]) == 6
    assert sorted(p["quarters"] for p in story["players"]) == sorted(totals)
    assert story["comments"] == []
    public = client.get("/players/1/public-profile")
    assert public.status_code == 200, public.text
    history = public.json()["game_history"]
    assert len(history) == 1 and history[0]["game_id"] == game_id
    assert len(history[0]["holes"]) == 18
    own = client.get("/players/me/history")
    assert own.status_code == 200, own.text
    assert own.json()["rounds_played"] == 1
    assert own.json()["recent_rounds"][0]["game_id"] == game_id
    completed = client.get("/games", params={"status": "completed"}).json()["games"]
    assert len(completed) == 1
    assert completed[0]["game_id"] == game_id
    assert completed[0]["played_at"] == "2026-10-25"
    # Follow the exact same UUID all entry points expose to a real card endpoint.
    card = client.get(f"/games/{game_id}/state")
    assert card.status_code == 200, card.text
    assert len(card.json()["hole_history"]) == 18
    assert len(card.json()["players"]) == 6


def test_tokens_to_uuid_social_photo_detail_conflict_channels_and_resolution(identity_pg, monkeypatch):
    """Single actual HTTP/service/SQL story; providers and claims stay synthetic."""
    from io import BytesIO
    from unittest.mock import Mock

    from PIL import Image
    from sqlalchemy import text

    from app.routers import game_card
    from app.schemas.round_identity import RoundDraft, SourceRef
    from app.services import round_delivery as delivery
    from app.services.round_reconciliation import observe_round
    from tests.unit.routers.test_round_backfill_attribution import review
    from tests.unit.routers.test_round_reconciliation_api import login
    from tests.unit.services.test_round_delivery import configure_recipient

    h = identity_pg
    h.app.include_router(game_card.router)
    with h.sessions() as db:
        configure_recipient(db, 7)
        db.commit()
    source = SourceRef(kind="sheet", scope="synthetic-approved:42:2026", round_token="opaque-round-token")
    value = RoundDraft(
        played_on="2026-10-06",
        raw_date="6-Oct",
        group="B",
        roster_complete=True,
        players=[
            {"participant_id": "opaque-a", "name": "Avery", "profile_id": 1, "quarters": 2.5},
            {"participant_id": "opaque-b", "name": "Blair", "profile_id": 2, "quarters": -2.5},
        ],
    )
    with h.sessions() as db:
        h.writer_pids.add(db.scalar(text("SELECT pg_backend_pid()")))
        outcome = observe_round(
            db,
            source,
            value,
            observation_key="approved-snapshot-1",
            raw_payload={"approval": "synthetic frozen fixture", "tokens": ["opaque-a", "opaque-b"]},
            continuity_verified=True,
        )
        game_id = outcome.game_id
        db.commit()
    durable = h.snapshot()
    assert durable["game_records"][0]["total_holes_played"] is None
    assert durable["game_records"][0]["course_name"] is None
    assert all(r["holes_won"] is None for r in durable["game_player_results"])
    assert {r["total_earnings"] for r in durable["game_player_results"]} == {2.5, -2.5}
    client = h.client
    login(h.app, h.sessions, 1)
    leaderboard = client.get("/data/leaderboard")
    assert leaderboard.status_code == 200, leaderboard.text
    standings = leaderboard.json()
    assert {row["member"]: (row["quarters"], row["rounds"]) for row in standings} == {
        "Avery": (2.5, 1),
        "Blair": (-2.5, 1),
    }
    history = client.get("/players/me/history")
    assert history.status_code == 200, history.text
    assert history.json()["recent_rounds"][0]["game_id"] == game_id
    rows = client.get("/data/rounds").json()
    assert rows and {r["game_id"] for r in rows} == {game_id}
    summary = client.get(f"/games/{game_id}/round-summary").json()
    assert summary["detail_coverage"] == "totals_only" and summary["hole_history"] == []
    assert summary["course_name"] is None
    comment = client.post(f"/data/rounds/uuid/{game_id}/comments", json={"body": "Original fixture discussion"})
    assert comment.status_code == 200, comment.text
    comment_id = comment.json()["id"]
    assert client.post(f"/data/rounds/uuid/{game_id}/reactions", json={"emoji": "🔥"}).status_code == 200
    photo = BytesIO()
    Image.new("RGB", (2, 2), "white").save(photo, format="PNG")
    uploaded = client.put(
        f"/games/{game_id}/scorecard-photo", files={"file": ("synthetic.png", photo.getvalue(), "image/png")}
    )
    assert uploaded.status_code == 200, uploaded.text
    assert client.get(f"/games/{game_id}/scorecard-photo").status_code == 200
    assert h.snapshot()["game_records"] == durable["game_records"]

    def patch(holes):
        revision = client.get(f"/games/{game_id}/round-summary").json()["revision"]
        return client.patch(
            f"/games/{game_id}/scorecard",
            json={
                "expected_revision": revision,
                "per_hole_quarters": [
                    {"hole": hole, "player_index": index, "quarters": quarters}
                    for hole in holes
                    for index, quarters in [(0, 1), (1, -1)]
                ],
            },
        )

    partial = patch([1])
    assert partial.status_code == 409, partial.text  # New detail requires reviewed acceptance.
    login(h.app, h.sessions)
    with h.sessions() as db:
        partial_id = db.query(models.RoundIssue).filter_by(game_id=game_id, field="detail", status="open").one().id
    accepted_partial = client.post(
        f"/round-reconciliation/issues/{partial_id}/resolve", json=review(client, partial_id)
    )
    assert accepted_partial.status_code in (200, 202), accepted_partial.text
    summary = client.get(f"/games/{game_id}/round-summary").json()
    assert summary["detail_coverage"] == "partial" and len(summary["hole_history"]) == 1
    assert {p["quarters"] for p in summary["players"]} == {2.5, -2.5}
    full = patch(range(1, 19))
    assert full.status_code == 409, full.text
    with h.sessions() as db:
        issue_id = db.query(models.RoundIssue).filter_by(game_id=game_id, field="detail", status="open").one().id
    # Anonymous and participant cannot resolve an imported discrepancy.
    h.app.dependency_overrides.pop(get_current_user)
    assert client.post(
        f"/round-reconciliation/issues/{issue_id}/resolve",
        json={"action": "accept", "reason": "no", "expected_issue_revision": 1, "expected_head_revision": 1},
    ).status_code in (401, 403)
    login(h.app, h.sessions, 1)
    assert (
        client.post(
            f"/round-reconciliation/issues/{issue_id}/resolve",
            json={"action": "accept", "reason": "no", "expected_issue_revision": 1, "expected_head_revision": 1},
        ).status_code
        == 403
    )
    login(h.app, h.sessions)
    detail = client.get(f"/round-reconciliation/issues/{issue_id}").json()
    assert detail["accepted_value"] != detail["proposed_value"]
    transport = Mock()
    transport.is_configured.return_value = True
    transport.send_round_conflict_notification.return_value = True
    monkeypatch.setattr(delivery, "get_email_service", lambda: transport)
    monkeypatch.setattr(delivery, "SessionLocal", h.sessions)
    delivery.dispatch_round_deliveries()
    delivery.dispatch_round_deliveries()
    deliveries = h.snapshot()["round_deliveries"]
    # Already reviewed partial-detail intents are obsolete, not failed sends.
    assert all(d["status"] == "obsolete" for d in deliveries if d["issue_id"] == partial_id)
    receipts = [d for d in deliveries if d["issue_id"] == issue_id]
    assert len(receipts) == 2
    assert {d["channel"] for d in receipts} == {"email", "in_app"}
    assert all(d["status"] == ("accepted" if d["channel"] == "email" else "delivered") for d in receipts), receipts
    assert transport.send_round_conflict_notification.call_count == len(
        [d for d in deliveries if d["status"] == "accepted"]
    )
    decision = review(client, issue_id)
    resolved = client.post(f"/round-reconciliation/issues/{issue_id}/resolve", json=decision)
    assert resolved.status_code in (200, 202), resolved.text
    final = h.snapshot()
    assert len(final["game_state"]) == len(final["game_records"]) == 1
    assert final["game_records"][0]["game_id"] == game_id
    assert len(final["game_player_results"]) == 2
    assert {r["total_earnings"] for r in final["game_player_results"]} == {2.5, -2.5}
    assert final["round_resolutions"][-1]["actor_profile_id"] == 8
    assert client.get(f"/data/rounds/uuid/{game_id}/discussion").json()["comments"][0]["id"] == comment_id
    assert client.get("/data/leaderboard").json() == standings
    assert client.get("/round-reconciliation/aliases", params={"date": "6-Oct", "group": "B"}).json()["game_ids"] == [
        game_id
    ]
