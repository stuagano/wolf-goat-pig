"""Task 8 review regressions through existing callers and physical database reads."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from threading import Barrier
from unittest.mock import Mock

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from app import models
from app.schemas.round_identity import RoundDraft
from app.services.completed_game_service import persist_final_results
from app.services.player_service import PlayerService
from app.services.statistics_service import StatisticsService
from tests.unit.services.test_canonical_round_statistics import canonical_history, save


def test_partial_enrichment_does_not_invent_hole_rate(canonical_history):
    db = canonical_history
    game = save(db, "enriched", [18, -18])
    persist_final_results(
        db,
        game,
        RoundDraft(
            played_on=date(2026, 10, 19),
            roster_complete=True,
            detail_coverage="partial",
            players=[
                {"participant_id": "0", "name": "Avery", "profile_id": 1, "quarters": 18},
                {"participant_id": "1", "name": "Guest", "quarters": -18},
            ],
            hole_history=[{"hole": 1, "points_delta": {"0": 1, "1": -1}}],
        ),
    )
    db.commit()
    stats = PlayerService(db).get_player_statistics(1)
    assert stats.total_earnings == 18
    assert stats.holes_played is stats.avg_earnings_per_hole is None


def test_gets_do_not_write_even_with_poisoned_stored_statistics(canonical_history):
    db = canonical_history
    save(db, "complete", [8, -8])
    db.add(models.PlayerStatistics(player_id=1, games_played=999, total_earnings=999))
    db.commit()
    writes = []

    def record(conn, cursor, statement, parameters, context, many):
        if statement.lstrip().split()[0].upper() in {"UPDATE", "INSERT", "DELETE"}:
            writes.append(statement)

    event.listen(db.get_bind(), "before_cursor_execute", record)
    try:
        assert PlayerService(db).get_player_performance_analytics(1).performance_summary["total_earnings"] == 8
        assert StatisticsService(db).get_advanced_player_metrics(1)["earnings_efficiency"].value == 8
        assert not writes
        assert not db.dirty and not db.new
    finally:
        event.remove(db.get_bind(), "before_cursor_execute", record)


def test_two_session_postgres_analytics_are_read_only(canonical_history):
    db = canonical_history
    if db.bind.dialect.name != "postgresql":
        return  # SQLite read-only behavior is covered above; no skipped cases.
    db.add(models.PlayerProfile(id=2, name="Blair", created_at="2026-01-01"))
    save(db, "complete", [8, -8])
    db.add_all([models.PlayerStatistics(player_id=i, games_played=999, total_earnings=999) for i in (1, 2)])
    db.commit()
    barrier = Barrier(2)
    writes = []

    def record(conn, cursor, statement, parameters, context, many):
        if statement.lstrip().split()[0].upper() in {"UPDATE", "INSERT", "DELETE"}:
            writes.append(statement)

    def read(pid):
        with Session(db.bind) as session:
            barrier.wait(timeout=5)
            result = PlayerService(session).get_player_performance_analytics(pid)
            StatisticsService(session).get_advanced_player_metrics(pid)
            return result.performance_summary["games_played"]

    event.listen(db.bind, "before_cursor_execute", record)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(read, i) for i in (1, 2)]
            assert [f.result(timeout=15) for f in futures] == [1, 0]
        assert not writes
    finally:
        event.remove(db.bind, "before_cursor_execute", record)


def test_tied_winners_share_rank_in_every_analytics_caller(canonical_history):
    db = canonical_history
    db.add(models.PlayerProfile(id=2, name="Blair", created_at="2026-01-01"))
    for i in range(5):
        save(db, f"tie-{i}", [8, 8])
        record = db.query(models.GameRecord).filter_by(game_id=f"tie-{i}").one()
        db.query(models.GamePlayerResult).filter_by(
            game_record_id=record.id, participant_id="1"
        ).one().player_profile_id = 2
    db.commit()
    from app.services.leaderboard_service import LeaderboardService

    service = StatisticsService(db)
    for pid in (1, 2):
        assert PlayerService(db).get_player_statistics(pid).games_won == 5
        assert [t.value for t in service.get_performance_trends(pid, days=10000)["position"]] == [4] * 5
        mode = service.get_game_mode_analytics(pid)["wolf_goat_pig_2p"]
        assert mode["avg_position"] == 1
        assert service._calculate_consistency_score(pid) == 100
    timed = LeaderboardService(db)._generate_time_filtered_leaderboard(
        "average_score", db, datetime(2026, 10, 1), datetime(2026, 10, 31), 10
    )
    assert [r["value"] for r in timed] == [1, 1]


@pytest.mark.parametrize("mixed", [False, True])
def test_incomplete_week_renders_coverage_without_fabricated_awards(canonical_history, mixed, monkeypatch):
    from app.services.email_service import EmailService
    from app.services.weekly_highlights import compute_highlights, run

    db = canonical_history
    save(db, "partial", [100, None])
    if mixed:
        save(db, "complete", [8, -8])
    summary = compute_highlights(db, "2026-10-19", "2026-10-26")
    assert summary is not None
    assert summary["known_participation_count"] == (4 if mixed else 2)
    assert summary["scored_participation_count"] == (2 if mixed else 0)
    assert summary["incomplete_rounds"] == 1
    if not mixed:
        assert summary["top_earner"] is summary["biggest_round"] is None
    email = EmailService()
    email._send_email = Mock(return_value=True)
    assert email.send_weekly_highlights("synthetic@example.test", "Avery", summary)
    body = email._send_email.call_args.kwargs
    for fmt in ("html_body", "text_body"):
        assert "known appearances" in body[fmt]
        assert "scored appearances" in body[fmt]
        assert "incomplete round" in body[fmt]
    monkeypatch.setattr("app.services.weekly_highlights.email_voice.commissioner_intro", lambda *a: None)
    db.get(models.PlayerProfile, 1).email = "synthetic@example.test"
    db.commit()
    email.is_configured = lambda: True
    result = run(db, now=datetime(2026, 10, 26, 20), email_service=email)
    assert result["sent"] == 1
