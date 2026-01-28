"""API routes for unified data access.

These endpoints provide a unified view of all game data from:
- Primary spreadsheet (legacy data)
- Writable spreadsheet (transition data)
- Render database (app-recorded games)

Data is automatically deduplicated based on date/group/member/score.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.unified_data_service import get_unified_data_service

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
    duration: Optional[str] = None
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
    sources: List[str]


class DataSourceStatus(BaseModel):
    """Status of a data source."""

    available: bool
    record_count: int
    id: Optional[str] = None
    error: Optional[str] = None


class DataStatusResponse(BaseModel):
    """Status of all data sources."""

    primary_sheet: DataSourceStatus
    writable_sheet: DataSourceStatus
    database: DataSourceStatus
    unified_total: int
    deduplicated_total: int


@router.get("/leaderboard", response_model=List[UnifiedLeaderboardEntryResponse])
def get_unified_leaderboard(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of players"),
    db: Session = Depends(get_db),
):
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


@router.get("/rounds", response_model=List[UnifiedRoundResponse])
def get_unified_rounds(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of rounds"),
    offset: int = Query(0, ge=0, description="Number of rounds to skip"),
    db: Session = Depends(get_db),
):
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


@router.get("/rounds/by-date/{date}", response_model=List[UnifiedRoundResponse])
def get_rounds_by_date(
    date: str,
    db: Session = Depends(get_db),
):
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


@router.get("/player/{member_name}", response_model=List[UnifiedRoundResponse])
def get_player_history(
    member_name: str,
    db: Session = Depends(get_db),
):
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
) -> Dict[str, Any]:
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
        "average_per_round": round(total_quarters / round_count, 1) if round_count else 0,
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
def get_data_status(db: Session = Depends(get_db)):
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
