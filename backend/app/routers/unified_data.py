"""API routes for unified data access.

These endpoints provide a unified view of all game data from:
- Primary spreadsheet (legacy data)
- Writable spreadsheet (transition data)
- Render database (app-recorded games)

Data is automatically deduplicated based on date/group/member/score.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..services.livsow_service import get_livsow_leaderboard, get_livsow_team_map
from ..services.livsow_transactions import check_and_record_snapshot, describe_transaction
from ..services.spreadsheet_sync_service import PRIMARY_SHEET_ID, PRIMARY_SHEET_TAB_GID
from ..services.unified_data_service import get_unified_data_service
from ..utils.admin_auth import require_admin
from ..utils.time import utc_now

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/data",
    tags=["data"],
)


class UnifiedRoundResponse(BaseModel):
    """A round result from any source."""

    date: str
    date_sortable: str
    group: str
    member: str
    score: int
    location: str
    duration: str | None = None
    source: str


class UnifiedLeaderboardEntryResponse(BaseModel):
    """A player's aggregated stats."""

    rank: int
    member: str
    quarters: int
    rounds: int
    average: float
    best_round: int
    worst_round: int
    sources: list[str]


class DataSourceStatus(BaseModel):
    """Status of a data source."""

    available: bool
    record_count: int
    id: str | None = None
    error: str | None = None


class DataStatusResponse(BaseModel):
    """Status of all data sources."""

    primary_sheet: DataSourceStatus
    writable_sheet: DataSourceStatus
    database: DataSourceStatus
    unified_total: int
    deduplicated_total: int


@router.get("/leaderboard", response_model=list[UnifiedLeaderboardEntryResponse])
def get_unified_leaderboard(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of players"),
    db: Session = Depends(get_db),
) -> Any:
    """Get the unified leaderboard from all data sources.

    This merges and deduplicates data from:
    - Primary spreadsheet (read-only legacy data)
    - Writable spreadsheet (app-entered transition data)
    - Database (games recorded in the app)

    Returns players sorted by total quarters (highest first).
    """
    service = get_unified_data_service(db=db)
    leaderboard = service.get_unified_leaderboard()

    return [
        UnifiedLeaderboardEntryResponse(
            rank=i + 1,
            member=entry.member,
            quarters=entry.quarters,
            rounds=entry.rounds,
            average=round(entry.average, 1),
            best_round=entry.best_round,
            worst_round=entry.worst_round,
            sources=list(entry.sources),
        )
        for i, entry in enumerate(leaderboard[:limit])
    ]


@router.get("/leaderboard-config")
def get_leaderboard_config() -> Any:
    """Return the configured leaderboard spreadsheet URL.

    This is a public endpoint used by the frontend to build the 'View Spreadsheet' link.
    The sheet ID can be changed via the LEADERBOARD_SHEET_ID env var on Render.
    """
    sheet_url = (
        f"https://docs.google.com/spreadsheets/d/{PRIMARY_SHEET_ID}"
        f"/edit?gid={PRIMARY_SHEET_TAB_GID}#gid={PRIMARY_SHEET_TAB_GID}"
    )
    return {
        "sheet_id": PRIMARY_SHEET_ID,
        "tab_gid": PRIMARY_SHEET_TAB_GID,
        "sheet_url": sheet_url,
    }


@router.get("/livsow/team-map")
def get_livsow_team_map_endpoint() -> Any:
    """Return {player_name: {team, role}} for use in other pages."""
    return get_livsow_team_map()


@router.get("/livsow/leaderboard")
def get_livsow_leaderboard_endpoint(refresh: bool = Query(False), db: Session = Depends(get_db)) -> Any:
    """Return LivSow stableford league standings from the Google Sheet.

    Cached for 15 minutes. Pass ?refresh=true to force a re-fetch.
    Opportunistically checks for roster changes (cheap hash compare) so
    transactions get detected from normal page traffic.
    """
    data = get_livsow_leaderboard(force_refresh=refresh)
    try:
        check_and_record_snapshot(db, data)
    except Exception:
        logger.exception("LivSow snapshot check failed (non-fatal)")
    return data


def _txn_row(t: models.LivSowTransaction) -> dict[str, Any]:
    d = {
        "id": t.id,
        "detected_at": t.detected_at,
        "season": t.season,
        "week": t.week_label,
        "snapshot_id": t.snapshot_id,
        "type": t.type,
        "player": t.player_name,
        "from_team": t.from_team,
        "to_team": t.to_team,
        "from_role": t.from_role,
        "to_role": t.to_role,
        "details": t.details,
    }
    d["description"] = describe_transaction(
        {
            "type": t.type,
            "player_name": t.player_name,
            "from_team": t.from_team,
            "to_team": t.to_team,
            "from_role": t.from_role,
            "to_role": t.to_role,
            "details": t.details,
        }
    )
    return d


def _livsow_slugify(name: str) -> str:
    import re as _re

    return _re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@router.get("/livsow/transactions")
def get_livsow_transactions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    player: str | None = Query(None),
    team: str | None = Query(None),
    type: str | None = Query(None),
    db: Session = Depends(get_db),
) -> Any:
    """LivSow transaction log — newest first, baseball-reference style."""
    q = db.query(models.LivSowTransaction).filter(models.LivSowTransaction.deleted.is_(False))
    if player:
        q = q.filter(models.LivSowTransaction.player_name.ilike(f"%{player}%"))
    if team:
        q = q.filter((models.LivSowTransaction.from_team == team) | (models.LivSowTransaction.to_team == team))
    if type:
        q = q.filter(models.LivSowTransaction.type == type)
    total = q.count()
    rows = (
        q.order_by(models.LivSowTransaction.detected_at.desc(), models.LivSowTransaction.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {"total": total, "transactions": [_txn_row(t) for t in rows]}


@router.get("/livsow/teams/{slug}")
def get_livsow_team_detail(slug: str, db: Session = Depends(get_db)) -> Any:
    """Team profile: roster with full stats, rank/total, and team transactions."""
    data = get_livsow_leaderboard()
    team = next((t for t in data.get("teams", []) if _livsow_slugify(t["name"]) == slug), None)
    if team is None:
        raise HTTPException(status_code=404, detail=f"LivSow team not found: {slug}")

    rows = (
        db.query(models.LivSowTransaction)
        .filter(models.LivSowTransaction.deleted.is_(False))
        .order_by(models.LivSowTransaction.detected_at.desc(), models.LivSowTransaction.id.desc())
        .limit(200)
        .all()
    )
    team_txns = [_txn_row(t) for t in rows if t.from_team == team["name"] or t.to_team == team["name"]]

    # Attach app profile ids so the UI can link players to their profile pages.
    # Sheet names don't always match profile names exactly — case-insensitive
    # exact match only; unmatched players simply render unlinked.
    players = [dict(p) for p in team.get("players", [])]
    names = [p["name"] for p in players]
    if names:
        from sqlalchemy import func as _func

        profile_rows = (
            db.query(models.PlayerProfile.id, models.PlayerProfile.name)
            .filter(_func.lower(models.PlayerProfile.name).in_([n.lower() for n in names]))
            .all()
        )
        by_lower = {name.lower(): pid for pid, name in profile_rows}
        for p in players:
            p["profile_id"] = by_lower.get(p["name"].lower())

    return {
        "slug": slug,
        "name": team["name"],
        "rank": team.get("rank"),
        "total": team.get("total"),
        "players": players,
        "weeks": data.get("weeks", []),
        "transactions": team_txns,
        "sheet_url": data.get("sheet_url"),
    }


@router.post("/livsow/snapshot")
def post_livsow_snapshot(force: bool = Query(False), db: Session = Depends(get_db)) -> Any:
    """Run the roster snapshot/diff check now. Called by the daily cron and
    available for manual triggering. Idempotent and guarded — safe to call
    repeatedly. ?force=true bypasses the debounce and circuit breaker."""
    data = get_livsow_leaderboard(force_refresh=True)
    return check_and_record_snapshot(db, data, force=force)


@router.delete("/livsow/transactions/{transaction_id}", dependencies=[Depends(require_admin)])
def delete_livsow_transaction(transaction_id: int, db: Session = Depends(get_db)) -> Any:
    """Soft-delete a transaction (admin escape hatch for sheet-edit noise)."""
    t = db.query(models.LivSowTransaction).filter(models.LivSowTransaction.id == transaction_id).first()
    if t is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    t.deleted = True
    db.commit()
    return {"success": True, "id": transaction_id}


@router.get("/rounds", response_model=list[UnifiedRoundResponse])
def get_unified_rounds(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of rounds"),
    offset: int = Query(0, ge=0, description="Number of rounds to skip"),
    db: Session = Depends(get_db),
) -> Any:
    """Get all rounds from all data sources.

    Returns rounds sorted by date (most recent first).
    Data is deduplicated - if the same round appears in multiple sources,
    only one copy is returned.
    """
    service = get_unified_data_service(db=db)
    rounds = service.get_all_rounds()

    return [
        UnifiedRoundResponse(
            date=r.date,
            date_sortable=r.date_sortable,
            group=r.group,
            member=r.member,
            score=r.score,
            location=r.location,
            duration=r.duration,
            source=r.source,
        )
        for r in rounds[offset : offset + limit]
    ]


@router.get("/rounds/by-date/{date}", response_model=list[UnifiedRoundResponse])
def get_rounds_by_date(
    date: str,
    db: Session = Depends(get_db),
) -> Any:
    """Get all rounds for a specific date.

    Args:
        date: Date in DD-Mon format (e.g., "27-Jan")
    """
    service = get_unified_data_service(db=db)
    rounds = service.get_rounds_by_date(date)

    return [
        UnifiedRoundResponse(
            date=r.date,
            date_sortable=r.date_sortable,
            group=r.group,
            member=r.member,
            score=r.score,
            location=r.location,
            duration=r.duration,
            source=r.source,
        )
        for r in rounds
    ]


@router.get("/player/{member_name}", response_model=list[UnifiedRoundResponse])
def get_player_history(
    member_name: str,
    db: Session = Depends(get_db),
) -> Any:
    """Get all rounds for a specific player.

    Args:
        member_name: Player name (case-insensitive match)
    """
    service = get_unified_data_service(db=db)
    rounds = service.get_player_history(member_name)

    return [
        UnifiedRoundResponse(
            date=r.date,
            date_sortable=r.date_sortable,
            group=r.group,
            member=r.member,
            score=r.score,
            location=r.location,
            duration=r.duration,
            source=r.source,
        )
        for r in rounds
    ]


@router.get("/player/{member_name}/stats")
def get_player_stats(
    member_name: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Get aggregated stats for a specific player.

    Args:
        member_name: Player name (case-insensitive match)
    """
    service = get_unified_data_service(db=db)
    rounds = service.get_player_history(member_name)

    if not rounds:
        return {
            "member": member_name,
            "found": False,
            "message": "Player not found in any data source",
        }

    total_quarters = sum(r.score for r in rounds)
    round_count = len(rounds)
    best = max(r.score for r in rounds)
    worst = min(r.score for r in rounds)
    sources = list(set(r.source for r in rounds))

    # Recent form (last 5 rounds)
    recent = rounds[:5]
    recent_total = sum(r.score for r in recent)

    return {
        "member": rounds[0].member,  # Use actual casing from data
        "found": True,
        "total_quarters": total_quarters,
        "rounds_played": round_count,
        "average_per_round": (round(total_quarters / round_count, 1) if round_count else 0),
        "best_round": best,
        "worst_round": worst,
        "sources": sources,
        "recent_form": {
            "rounds": len(recent),
            "total": recent_total,
            "average": round(recent_total / len(recent), 1) if recent else 0,
        },
        "first_round_date": rounds[-1].date if rounds else None,
        "last_round_date": rounds[0].date if rounds else None,
    }


@router.get("/status", response_model=DataStatusResponse)
def get_data_status(db: Session = Depends(get_db)) -> Any:
    """Get status of all data sources.

    Returns availability and record counts for each source,
    plus totals before and after deduplication.
    """
    service = get_unified_data_service(db=db)
    status = service.get_data_sources_status()

    return DataStatusResponse(
        primary_sheet=DataSourceStatus(
            available=status["primary_sheet"]["available"],
            record_count=status["primary_sheet"]["record_count"],
            id=status["primary_sheet"].get("id"),
            error=status["primary_sheet"].get("error"),
        ),
        writable_sheet=DataSourceStatus(
            available=status["writable_sheet"]["available"],
            record_count=status["writable_sheet"]["record_count"],
            id=status["writable_sheet"].get("id"),
            error=status["writable_sheet"].get("error"),
        ),
        database=DataSourceStatus(
            available=status["database"]["available"],
            record_count=status["database"]["record_count"],
            error=status["database"].get("error"),
        ),
        unified_total=status["unified_total"],
        deduplicated_total=status["deduplicated_total"],
    )


@router.post("/sync-sheets", dependencies=[Depends(require_admin)])
def sync_sheets_to_db(db: Session = Depends(get_db)) -> Any:
    """Pull all rounds from Google Sheets and upsert into legacy_rounds table.

    Safe to run repeatedly — clears and repopulates the table each time.
    """
    service = get_unified_data_service(db=db)

    try:
        all_rounds = service.get_all_rounds(include_database=False, use_sheet_cache=False)
    except Exception as exc:
        return {"success": False, "error": str(exc), "synced": 0}

    if not all_rounds:
        return {"success": False, "error": "No rounds returned from sheets", "synced": 0}

    synced_at = utc_now().isoformat()

    # Clear existing sheet-sourced rows and repopulate
    db.query(models.LegacyRound).filter(models.LegacyRound.source.in_(["primary_sheet", "writable_sheet"])).delete(
        synchronize_session=False
    )

    for r in all_rounds:
        db.add(
            models.LegacyRound(
                date=r.date_sortable,
                group=r.group,
                member=r.member,
                score=r.score,
                location=r.location or "",
                source=r.source,
                synced_at=synced_at,
            )
        )

    db.commit()
    return {"success": True, "synced": len(all_rounds), "synced_at": synced_at}
