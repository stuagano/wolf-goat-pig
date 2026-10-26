"""Synthetic saved scorecard -> persistence -> every round-navigation API."""

from app import models
from app.routers import member_rounds, players, round_stories, unified_data
from app.services.auth_service import get_current_user
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
