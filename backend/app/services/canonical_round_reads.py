"""Accepted-result query boundary for UnifiedDataService, not a second round store.

A configured season is the calendar year supplied to the source date parser.
Unknown dates stay in history, never in date-dependent statistics. Paused mode
keeps serving the last accepted canonical projection; it cannot revive caches.
"""

from collections import defaultdict
from types import SimpleNamespace

from sqlalchemy.orm import Session

from app import models
from app.schemas.round_identity import read_round_identity_config


def canonical_mode(db: Session) -> bool:
    config = read_round_identity_config(db)
    row = db.get(models.AppConfig, "round_identity")
    # A first pause fences writers, not readers. Subsequent recovery pauses keep
    # canonical authority; they must never resurrect legacy counting.
    return config.mode == "canonical" or bool(row and row.value.get("reader_mode") == "canonical")


def accepted_rows(db: Session, *, eligible_only=False, season_only=False):
    config = read_round_identity_config(db)
    query = (
        db.query(models.GameRecord, models.GamePlayerResult)
        .join(models.GamePlayerResult, models.GamePlayerResult.game_record_id == models.GameRecord.id)
        .join(models.GameStateModel, models.GameStateModel.game_id == models.GameRecord.game_id)
        .filter(
            models.GameRecord.is_retracted.is_(False),
            models.GamePlayerResult.is_retracted.is_(False),
            models.GameRecord.accepted_revision > 0,
            models.GamePlayerResult.participant_id.isnot(None),
        )
    )
    rows = query.all()
    # Whole-game eligibility is persisted by the sole writer. Defend against
    # incomplete staged projections too; no result can opt into counting alone.
    groups = defaultdict(list)
    for record, result in rows:
        groups[record.id].append(result)
    valid = {
        record.id
        for record, _ in rows
        if record.score_eligible
        and record.roster_complete
        and len(groups[record.id]) == record.player_count
        and all(r.total_earnings is not None for r in groups[record.id])
    }
    if eligible_only:
        rows = [(record, result) for record, result in rows if record.id in valid and record.played_on is not None]
    if season_only:
        rows = [
            (record, result)
            for record, result in rows
            if config.season is not None and record.played_on is not None and record.played_on.year == config.season
        ]
    return rows, valid


def accepted_ranks(rows):
    """Competition ranks from accepted totals; all tied maxima are winners."""
    totals = defaultdict(list)
    for record, result in rows:
        totals[record.id].append(result.total_earnings)
    return {r.id: 1 + sum(t > r.total_earnings for t in totals[rec.id]) for rec, r in rows}


def profile_statistics(db: Session, player_id: int | None = None):
    """Compute canonical read DTOs without attaching or mutating ORM statistics.

    Unknown detailed observations stay NULL across an incomplete detail sample.
    No flush, write lock, transaction boundary or stored aggregate is required.
    """
    appearances, eligible = accepted_rows(db, season_only=True)
    rows = [(rec, r) for rec, r in appearances if rec.id in eligible]
    ranks = accepted_ranks(rows)
    by_profile = defaultdict(list)
    for record, result in rows:
        if result.player_profile_id is not None:
            by_profile[result.player_profile_id].append((record, result))
    profiles = db.query(models.PlayerProfile)
    if player_id is not None:
        profiles = profiles.filter_by(id=player_id)
    output = {}
    direct = {
        "holes_won": "holes_won",
        "successful_bets": "successful_bets",
        "total_bets": "total_bets",
        "partnerships_formed": "partnerships_formed",
        "partnerships_won": "partnerships_won",
        "solo_attempts": "solo_attempts",
        "solo_wins": "solo_wins",
        "ping_pong_count": "ping_pongs",
        "ping_pong_wins": "ping_pongs_won",
        "invisible_aardvark_appearances": "invisible_aardvark_holes",
        "invisible_aardvark_wins": "invisible_aardvark_holes_won",
        **{
            key: key
            for key in (
                "duncan_attempts",
                "duncan_wins",
                "tunkarri_attempts",
                "tunkarri_wins",
                "big_dick_attempts",
                "big_dick_wins",
            )
        },
    }
    for profile in profiles:
        stored = db.query(models.PlayerStatistics).filter_by(player_id=profile.id).first()
        stats = SimpleNamespace(
            id=stored.id if stored else 0,
            player_id=profile.id,
            favorite_game_mode=stored.favorite_game_mode if stored else "wolf_goat_pig",
            preferred_player_count=stored.preferred_player_count if stored else 4,
            known_participation_count=sum(r.player_profile_id == profile.id for _, r in appearances),
            incomplete_round_count=sum(
                r.player_profile_id == profile.id and rec.id not in eligible for rec, r in appearances
            ),
        )
        sample = sorted(by_profile[profile.id], key=lambda pair: (pair[0].played_on, pair[0].game_id))
        results = [r for _, r in sample]
        stats.games_played = stats.scored_round_count = len(results)
        stats.total_earnings = sum(r.total_earnings for r in results)
        # Winners are maximal accepted quarter totals, not fabricated positions.
        wins = [ranks[result.id] == 1 for _, result in sample]
        stats.games_won = sum(wins)
        for target, source in direct.items():
            values = [getattr(r, source) for r in results]
            setattr(stats, target, sum(values) if values and all(v is not None for v in values) else None)
        holes = [rec.total_holes_played if rec.detail_coverage == "per_hole_complete" else None for rec, _ in sample]
        stats.holes_played = sum(holes) if holes and all(v is not None for v in holes) else None
        stats.avg_earnings_per_hole = stats.total_earnings / stats.holes_played if stats.holes_played else None
        for target, numerator, denominator in (
            ("betting_success_rate", "successful_bets", "total_bets"),
            ("partnership_success_rate", "partnerships_won", "partnerships_formed"),
        ):
            n, d = getattr(stats, numerator), getattr(stats, denominator)
            setattr(stats, target, n / d if n is not None and d else None)
        for target in (
            "eagles",
            "birdies",
            "pars",
            "bogeys",
            "double_bogeys",
            "worse_than_double",
            "times_as_wolf",
            "times_as_goat",
            "times_as_pig",
            "times_as_aardvark",
        ):
            # No canonical evidence contract for these metrics yet.
            setattr(stats, target, None)
        win_streak = loss_streak = best = worst = 0
        for won in wins:
            win_streak = win_streak + 1 if won else 0
            loss_streak = 0 if won else loss_streak + 1
            best, worst = max(best, win_streak), max(worst, loss_streak)
        stats.current_win_streak, stats.current_loss_streak = win_streak, loss_streak
        stats.best_win_streak, stats.worst_loss_streak = best, worst
        stats.performance_trends = [
            {
                "game_id": rec.game_id,
                "participant_id": r.participant_id,
                "game_date": rec.played_on.isoformat(),
                "earnings": r.total_earnings,
                "position": ranks[r.id],
            }
            for rec, r in sample
        ]
        stats.head_to_head_records = {}
        stats.best_hole_performance = []
        stats.worst_hole_performance = []
        stats.last_updated = str(max((rec.accepted_revision for rec, _ in sample), default=0))
        output[profile.id] = stats
    return output


def rebuild_player_statistics(db: Session, player_id: int | None = None):
    """Explicit persisted rebuild for fenced writers only; never used by GETs."""
    from .round_writes import writer_mode

    if writer_mode(db) != "canonical":
        raise ValueError("Canonical statistics rebuild requires canonical writer mode")
    projections = profile_statistics(db, player_id)
    output = {}
    for pid in sorted(projections):
        stats = db.query(models.PlayerStatistics).filter_by(player_id=pid).first()
        if stats is None:
            stats = models.PlayerStatistics(player_id=pid)
            db.add(stats)
        for key, value in vars(projections[pid]).items():
            if key not in {"id", "known_participation_count", "incomplete_round_count", "scored_round_count"}:
                setattr(stats, key, value)
        output[pid] = stats
    db.flush()
    return output


def profile_statistics_pairs(db: Session, *, active_only=True):
    """Existing consumer pair shape, backed by the shared nonmutating projection."""
    stats = profile_statistics(db)
    profiles = db.query(models.PlayerProfile).order_by(models.PlayerProfile.id).all()
    return [(p, stats[p.id]) for p in profiles if not active_only or (p.is_active == 1 and p.is_ai == 0)]
