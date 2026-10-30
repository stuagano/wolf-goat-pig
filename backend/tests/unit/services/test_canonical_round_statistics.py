"""Canonical counting uses committed accepted UUID/slots, never source-cache echoes."""

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import models
from app.schemas.round_identity import RoundDraft
from app.services.completed_game_service import persist_final_results
from app.services.unified_data_service import UnifiedDataService


@pytest.fixture(params=["sqlite", "postgresql"])
def canonical_history(request):
    import os
    from uuid import uuid4

    from sqlalchemy import text
    from sqlalchemy.engine import make_url
    from sqlalchemy.pool import NullPool

    admin = None
    if request.param == "postgresql":
        raw = os.environ.get("ROUND_IDENTITY_TEST_DATABASE_URL")
        if not raw:
            pytest.fail("Canonical statistics readback requires local ROUND_IDENTITY_TEST_DATABASE_URL")
        url = make_url(raw)
        assert url.host in {"127.0.0.1", "localhost", "::1"} and url.database.endswith("_test") and not url.query
        schema = "statistics_" + uuid4().hex
        admin = create_engine(url.set(drivername="postgresql+psycopg2"), poolclass=NullPool)
        with admin.begin() as tx:
            tx.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(
            url.set(drivername="postgresql+psycopg2"),
            poolclass=NullPool,
            connect_args={"options": f"-csearch_path={schema} -cstatement_timeout=10000"},
        )
    else:
        from sqlalchemy.pool import StaticPool

        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    models.Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(models.AppConfig(name="round_identity", value={"mode": "canonical", "season": 2026}))
        db.add(models.PlayerProfile(id=1, name="Avery", created_at="2026-01-01T00:00:00"))
        db.commit()
        yield db
    engine.dispose()
    if admin is not None:
        with admin.begin() as tx:
            tx.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


def save(db, key, scores, *, played=date(2026, 10, 19), names=None):
    game = models.GameStateModel(game_id=key, state={}, game_status="setup")
    db.add(game)
    db.flush()
    persist_final_results(
        db,
        game,
        RoundDraft(
            played_on=played,
            raw_date="19-Oct",
            roster_complete=True,
            players=[
                {
                    "participant_id": str(i),
                    "name": (names or ["Avery", "Guest"])[i],
                    "profile_id": 1 if i == 0 else None,
                    "quarters": score,
                }
                for i, score in enumerate(scores)
            ],
        ),
    )
    db.commit()
    db.expire_all()
    return game


def test_partial_round_never_enlarges_score_average(canonical_history):
    db = canonical_history
    save(db, "complete", [8, -8])
    save(db, "partial", [4, None])
    entry = UnifiedDataService(db).get_unified_leaderboard()[0]
    assert (entry.member, entry.rounds, entry.quarters, entry.average) == ("Avery", 1, 8, 8)
    assert entry.known_participation_count == 2
    history = UnifiedDataService(db).get_all_rounds()
    assert len(history) == 4
    assert next(r for r in history if r.game_id == "partial" and r.member == "Guest").score is None


def test_empty_scored_sample_keeps_unknown_average(canonical_history):
    from app.routers import member_rounds, spreadsheet_sync, unified_data

    db = canonical_history
    save(db, "partial", [4, None])
    entry = UnifiedDataService(db).get_unified_leaderboard()[0]
    assert (entry.rounds, entry.average, entry.best_round, entry.worst_round) == (0, None, None, None)
    assert entry.known_participation_count == entry.incomplete_round_count == 1
    admin = spreadsheet_sync.get_spreadsheet_leaderboard(db=db)[0]
    assert admin.average is None
    personal = member_rounds.get_my_history(current_user=db.get(models.PlayerProfile, 1), db=db)
    named = unified_data.get_player_stats(member_name="Avery", db=db)
    for summary in (personal, named):
        assert summary["average_per_round"] is None
        assert summary["best_round"] is summary["worst_round"] is None
        assert summary["rounds_played"] == 0
        assert summary["known_participation_count"] == summary["incomplete_round_count"] == 1
    assert named["recent_form"]["average"] is None


def test_echo_same_day_guests_and_unknown_year(canonical_history):
    db = canonical_history
    save(db, "one", [1.25, -1.25], names=["Avery", "Avery"])
    save(db, "two", [1.25, -1.25], names=["Avery", "Avery"])
    save(db, "prior", [99, -99], played=date(2025, 10, 19))
    save(db, "unknown", [100, -100], played=None)
    db.add(models.LegacyRound(date="2026-10-19", member="Avery", score=999, source="primary_sheet"))
    db.commit()
    service = UnifiedDataService(db)
    rows = service.get_all_rounds()
    assert len(rows) == 8
    assert len({r.game_key for r in rows}) == 8
    assert len(set(rows)) == 8  # equality must not collapse same-day games
    unknown = next(r for r in rows if r.game_id == "unknown")
    assert unknown.date_sortable is None
    entries = service.get_unified_leaderboard()
    assert len(entries) == 1  # guests never acquire a profile by display name
    assert (entries[0].quarters, entries[0].rounds) == (2.5, 2)


def test_retracted_records_and_slots_never_count(canonical_history):
    db = canonical_history
    save(db, "retracted", [8, -8])
    record = db.query(models.GameRecord).one()
    record.is_retracted = True
    db.commit()
    assert UnifiedDataService(db).get_all_rounds() == []
    record.is_retracted = False
    db.query(models.GamePlayerResult).filter_by(participant_id="0").one().is_retracted = True
    db.commit()
    assert UnifiedDataService(db).get_unified_leaderboard() == []


def test_actual_profile_admin_and_analytics_reads(canonical_history):
    from app.routers import players, spreadsheet_sync, unified_data
    from app.services.player_service import PlayerService
    from app.services.statistics_service import StatisticsService
    from app.services.weekly_highlights import compute_highlights

    db = canonical_history
    save(db, "one", [1.25, -1.25], names=["Avery", "Avery"])
    save(db, "two", [1.25, -1.25], names=["Avery", "Avery"])
    save(db, "partial", [100, None])
    save(db, "prior", [999, -999], played=date(2025, 10, 19))
    save(db, "unknown", [999, -999], played=None)
    db.add(models.LegacyRound(date="2026-10-19", member="Avery", score=999, source="primary_sheet"))
    db.add(models.PlayerStatistics(player_id=1, games_played=999, total_earnings=999))
    db.commit()
    stats = PlayerService(db).get_player_statistics(1)
    assert (stats.games_played, stats.total_earnings, stats.holes_played, stats.solo_wins) == (2, 2.5, None, None)
    assert PlayerService(db).get_player_statistics(1).model_dump() == stats.model_dump()
    # Season participation is reported separately from the scored denominator.
    assert (stats.known_participation_count, stats.incomplete_round_count) == (3, 1)
    public = players.get_public_player_profile(player_id=1, db=db)
    assert public["stats"]["total_earnings"] == 2.5
    assert public["stats"]["known_participation_count"] == 3
    assert len(public["game_history"]) == 5
    assert all(r["score"] >= 0 for r in public["game_history"])
    from app.routers import member_rounds

    personal = member_rounds.get_my_history(current_user=db.get(models.PlayerProfile, 1), db=db, recent_limit=20)
    named = unified_data.get_player_stats(member_name="Avery", db=db)
    for summary in (personal, named):
        assert (summary["rounds_played"], summary["total_quarters"]) == (2, 2.5)
        assert (summary["known_participation_count"], summary["incomplete_round_count"]) == (3, 1)
    assert len(personal["recent_rounds"]) == 5
    posted = member_rounds.get_my_rounds(current_user=db.get(models.PlayerProfile, 1), db=db)
    assert len(posted) == 5
    assert len({(r["game_id"], r["participant_id"]) for r in posted}) == 5
    assert sum(r["score_eligible"] for r in posted) == 3  # all-time history includes the prior season
    admin = spreadsheet_sync.get_spreadsheet_leaderboard(db=db)
    assert (admin[0].rounds, admin[0].quarters, admin[0].average) == (2, 2.5, 1.25)
    assert len(spreadsheet_sync.get_all_rounds(limit=100, db=db)) == 10
    assert len(spreadsheet_sync.get_rounds_by_date("2026-10-19", db=db)) == 3
    assert len(spreadsheet_sync.get_player_history("Avery", db=db)) == 5
    extremes = unified_data.get_season_extreme_scores(kind="best", limit=50, db=db)
    assert len(extremes) == 4  # complete guest slots remain distinct
    highlights = compute_highlights(db, "2026-10-19", "2026-10-26")
    assert highlights["rounds"] == 2
    assert highlights["top_earner"]["quarters"] == 2.5
    analytics = StatisticsService(db)
    mode = analytics.get_game_mode_analytics(1)["wolf_goat_pig_2p"]
    assert (mode["total_earnings"], mode["wins"], mode["win_rate"]) == (2.5, 2, 100)
    assert highlights["incomplete_rounds"] == 1
    assert highlights["known_participation_count"] == 6
    assert analytics.get_score_performance_analytics(1)["status"] == "unavailable"
    assert analytics.get_special_event_analytics(1)["status"] == "unavailable"
    assert "earnings_efficiency" in analytics.get_advanced_player_metrics(1)
    assert PlayerService(db).get_player_performance_analytics(1).performance_summary["total_earnings"] == 2.5


def test_disputes_held_evidence_and_paused_reads(canonical_history):
    from app.schemas.round_identity import SourceRef
    from app.services.round_reconciliation import observe_round

    db = canonical_history
    draft = RoundDraft(
        played_on=date(2026, 10, 19),
        roster_complete=True,
        players=[
            {"participant_id": "a", "name": "Avery", "profile_id": 1, "quarters": 8},
            {"participant_id": "b", "name": "Guest", "quarters": -8},
        ],
    )
    source = SourceRef(kind="sheet", scope="fixture", round_token="round")
    first = observe_round(db, source, draft, observation_key="first", raw_payload={}, continuity_verified=True)
    db.commit()
    draft.players[0].quarters = 80
    conflict = observe_round(db, source, draft, observation_key="conflict", raw_payload={}, continuity_verified=True)
    db.commit()
    assert conflict.issue_ids and conflict.game_id == first.game_id
    held = observe_round(
        db,
        SourceRef(kind="sheet", scope="other", round_token="ambiguous"),
        draft,
        observation_key="held",
        raw_payload={},
        continuity_verified=False,
    )
    db.commit()
    assert held.status == "held"
    assert UnifiedDataService(db).get_unified_leaderboard()[0].quarters == 8
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.database import get_db
    from app.routers import leaderboard, unified_data

    app = FastAPI()
    app.include_router(leaderboard.router)
    app.include_router(unified_data.router)
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        enhanced = client.get("/leaderboard/ghin-enhanced")
        assert enhanced.status_code == 200
        assert enhanced.json()[0]["total_earnings"] == 8
        response = client.get("/data/leaderboard")
        assert response.status_code == 200
        assert response.json()[0]["quarters"] == 8
        assert len(client.get("/data/leaderboard/rounds").json()) == 1
    # A recovery pause after activation keeps canonical reader authority; it is
    # the real transition, not a hand-written configuration value.
    from app.schemas.round_identity import read_round_identity_config
    from app.services.round_cutover import pause_writers

    pause_writers(db, expected_epoch=read_round_identity_config(db).epoch, reason="Fixture recovery pause")
    db.commit()
    assert db.get(models.AppConfig, "round_identity").value["reader_mode"] == "canonical"
    assert UnifiedDataService(db).get_unified_leaderboard()[0].quarters == 8


def test_legacy_writers_cannot_overwrite_canonical_statistics(canonical_history):
    from app.schemas.games import GamePlayerResultCreate
    from app.services.player_service import PlayerService
    from app.services.sheet_integration_service import SheetIntegrationService

    db = canonical_history
    save(db, "accepted", [1.25, -1.25])
    record = db.query(models.GameRecord).one()
    service = PlayerService(db)
    replay = GamePlayerResultCreate(
        game_record_id=record.id, player_profile_id=1, player_name="Avery", final_position=1, total_earnings=1.25
    )
    assert service.record_game_result(replay)
    assert service.record_game_result(replay)
    assert db.query(models.GamePlayerResult).count() == 2
    assert service.get_player_statistics(1).total_earnings == 1.25
    with pytest.raises(ValueError, match="canonical final-result writer"):
        service.record_game_result(replay.model_copy(update={"total_earnings": 999}))
    with pytest.raises(ValueError, match="disabled in canonical mode"):
        SheetIntegrationService(db).sync_sheet_data_to_database([{"Player Name": "Avery", "Games Played": 999}], [])
    assert service.get_player_statistics(1).games_played == 1
    record.is_retracted = True
    db.commit()
    with pytest.raises(ValueError, match="canonical final-result writer"):
        service.record_game_result(replay)


def test_leaderboard_service_and_actual_endpoint_readbacks(canonical_history):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.database import get_db
    from app.routers import leaderboard, unified_data
    from app.services.leaderboard_service import LeaderboardService

    db = canonical_history
    save(db, "one", [1.25, -1.25], names=["Avery", "Avery"])
    save(db, "two", [1.25, -1.25], names=["Avery", "Avery"])
    save(db, "partial", [100, None])
    save(db, "prior", [999, -999], played=date(2025, 10, 19))
    save(db, "unknown", [999, -999], played=None)
    save(db, "retracted", [999, -999])
    db.query(models.GameRecord).filter_by(game_id="retracted").one().is_retracted = True
    db.add(models.PlayerStatistics(player_id=1, games_played=999, total_earnings=999))
    db.commit()
    service = LeaderboardService(db)
    service.cache.set("leaderboard:total_earnings:10:0", [{"value": 999}])
    expected = [{"rank": 1, "player_id": 1, "player_name": "Avery", "value": 2.5}]
    assert service.get_leaderboard("total_earnings", db) == expected
    assert service.get_leaderboard("total_earnings", db) == expected
    assert service.get_leaderboard("games_played", db)[0]["value"] == 2
    assert service.get_leaderboard("partnerships_won", db) == []
    from datetime import datetime

    period = service._generate_time_filtered_leaderboard(
        "total_earnings", db, datetime(2026, 10, 19), datetime(2026, 10, 20), 10
    )
    assert period == expected  # played date, not upload clock; guest never gains the profile
    app = FastAPI()
    app.include_router(leaderboard.router)
    app.include_router(unified_data.router)
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        response = client.get("/leaderboard/ghin-enhanced")
        assert response.status_code == 200, response.text
        enhanced = response.json()
        assert len(enhanced) == 1
        assert (enhanced[0]["games_played"], enhanced[0]["total_earnings"]) == (2, 2.5)
        assert enhanced[0]["avg_earnings"] is enhanced[0]["partnership_success"] is None
        assert enhanced[0]["handicap"] == db.get(models.PlayerProfile, 1).handicap
        rounds = client.get("/data/leaderboard/rounds").json()
        assert len(rounds) == 3
        assert len([p for game in rounds for p in game["players"]]) == 6
        assert len(client.get("/data/leaderboard/scores?kind=best&limit=50").json()) == 4
        db.query(models.GamePlayerResult).filter_by(
            game_record_id=db.query(models.GameRecord).filter_by(game_id="two").one().id, participant_id="1"
        ).one().is_retracted = True
        db.commit()
        assert service.get_leaderboard("total_earnings", db)[0]["value"] == 1.25
        enhanced = client.get("/leaderboard/ghin-enhanced").json()
        assert (enhanced[0]["games_played"], enhanced[0]["total_earnings"]) == (1, 1.25)


def test_commissioner_sql_view_and_retractions(canonical_history):
    from app.database import ensure_canonical_round_results_view
    from app.routers.commissioner import _build_data_context, _execute_readonly_sql

    db = canonical_history
    save(db, "one", [1.25, -1.25])
    save(db, "partial", [100, None])
    save(db, "prior", [999, -999], played=date(2025, 10, 19))
    save(db, "unknown", [999, -999], played=None)
    ensure_canonical_round_results_view(db.get_bind())
    result = _execute_readonly_sql(db, "SELECT SUM(score), COUNT(*) FROM canonical_round_results")
    assert result["rows"] == [[1.25, 1]]
    assert "1 scored rounds" in _build_data_context(db)
    assert "error" in _execute_readonly_sql(db, "SELECT * FROM game_player_results")
    assert "error" in _execute_readonly_sql(db, "SELECT * FROM player_statistics")
    db.query(models.GamePlayerResult).filter_by(
        game_record_id=db.query(models.GameRecord).filter_by(game_id="one").one().id, participant_id="1"
    ).one().is_retracted = True
    db.commit()
    result = _execute_readonly_sql(db, "SELECT COUNT(*) FROM canonical_round_results")
    assert result["rows"] == [[0]]
