"""Admin routes for Google Sheets synchronization.

These endpoints allow admins to:
- View current spreadsheet data (served from legacy_rounds DB — synced every 2h)
- Sync completed games to the spreadsheet
- View leaderboard from spreadsheet
"""

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import LegacyRound, PendingSheetSync
from ..utils.admin_auth import require_admin
from ..services.spreadsheet_sync_service import (
    PRIMARY_SHEET_ID,
    WRITABLE_SHEET_ID,
    _get_access_token,
    get_reconciliation_service,
    get_spreadsheet_sync_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/spreadsheet",
    tags=["admin", "spreadsheet"],
    dependencies=[Depends(require_admin)],
)


class PlayerScoreInput(BaseModel):
    """Input for a single player's score."""

    name: str = Field(..., description="Player name (must match spreadsheet names)")
    score: int = Field(..., description="Quarters won (positive) or lost (negative)")


class SyncRoundRequest(BaseModel):
    """Request to sync a completed round to the spreadsheet."""

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    group: str = Field("A", description="Group letter (A, B, C, D)")
    location: str = Field("Wing Point", description="Course name")
    duration: str | None = Field(None, description="Duration in HH:MM:SS format")
    player_scores: list[PlayerScoreInput] = Field(..., description="List of player scores")


class LeaderboardEntry(BaseModel):
    """A single entry in the leaderboard."""

    rank: int
    member: str
    quarters: int
    average: int
    rounds: int
    qb: int


class RoundResultResponse(BaseModel):
    """Response model for a round result."""

    date: str
    group: str
    member: str
    score: int
    location: str
    duration: str | None = None


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
def get_spreadsheet_leaderboard(db: Session = Depends(get_db)):
    """Get the current leaderboard computed from the legacy_rounds DB (synced every 2h)."""
    rows = (
        db.query(
            LegacyRound.member,
            func.sum(LegacyRound.score).label("quarters"),
            func.count(LegacyRound.id).label("rounds"),
        )
        .group_by(LegacyRound.member)
        .all()
    )

    if not rows:
        return []

    entries = [
        {"member": r.member, "quarters": r.quarters, "rounds": r.rounds}
        for r in rows
    ]
    entries.sort(key=lambda e: e["quarters"], reverse=True)

    leader_quarters = entries[0]["quarters"] if entries else 0
    result = []
    for i, e in enumerate(entries):
        avg = e["quarters"] // e["rounds"] if e["rounds"] else 0
        result.append(
            LeaderboardEntry(
                rank=i + 1,
                member=e["member"],
                quarters=e["quarters"],
                average=avg,
                rounds=e["rounds"],
                qb=leader_quarters - e["quarters"],
            )
        )
    return result


@router.get("/rounds", response_model=list[RoundResultResponse])
def get_all_rounds(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    db: Session = Depends(get_db),
) -> Any:
    """Get all round results from legacy_rounds DB (synced every 2h)."""
    rows = (
        db.query(LegacyRound)
        .order_by(LegacyRound.date.desc(), LegacyRound.member)
        .limit(limit)
        .all()
    )
    return [
        RoundResultResponse(
            date=r.date,
            group=r.group,
            member=r.member,
            score=r.score,
            location=r.location,
            duration=r.duration,
        )
        for r in rows
    ]


@router.get("/rounds/by-date/{date}", response_model=list[dict[str, Any]])
def get_rounds_by_date(date: str, db: Session = Depends(get_db)) -> Any:
    """Get all rounds for a specific date.

    Date format: YYYY-MM-DD (e.g., "2026-07-21").
    """
    rows = (
        db.query(LegacyRound)
        .filter(LegacyRound.date == date)
        .order_by(LegacyRound.group, LegacyRound.member)
        .all()
    )

    # Group into round summaries by (date, group, location, duration)
    summaries: dict[tuple, dict] = {}
    for r in rows:
        key = (r.date, r.group, r.location, r.duration)
        if key not in summaries:
            summaries[key] = {
                "date": r.date,
                "group": r.group,
                "location": r.location,
                "duration": r.duration,
                "player_count": 0,
                "total_score": 0,
                "players": [],
            }
        summaries[key]["player_count"] += 1
        summaries[key]["total_score"] += r.score
        summaries[key]["players"].append({"member": r.member, "score": r.score})

    return list(summaries.values())


@router.get("/player/{member_name}", response_model=list[RoundResultResponse])
def get_player_history(member_name: str, db: Session = Depends(get_db)) -> Any:
    """Get all rounds for a specific player from legacy_rounds DB (synced every 2h)."""
    rows = (
        db.query(LegacyRound)
        .filter(LegacyRound.member == member_name)
        .order_by(LegacyRound.date.desc())
        .all()
    )
    return [
        RoundResultResponse(
            date=r.date,
            group=r.group,
            member=r.member,
            score=r.score,
            location=r.location,
            duration=r.duration,
        )
        for r in rows
    ]


@router.post("/sync-round", status_code=202)
def sync_round_to_spreadsheet(
    request: SyncRoundRequest, db: Session = Depends(get_db)
) -> Any:
    """Enqueue a completed round for background sync to Google Sheets.

    Returns 202 immediately. The background processor runs every 5 minutes,
    deduplicates against existing legacy_rounds, and writes new/updated rounds
    to the sheet.

    Dedup logic:
      - Same date + group + same player set + same scores → skipped as duplicate
      - Same date + group + same player set but different scores → written as update
      - New player set for that date/group → written as new round

    NOTE: player_scores should be summed totals (not per-hole). The app tracks
    per-hole detail internally; the legacy sheet only stores round totals.
    """
    try:
        datetime.strptime(request.date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    total = sum(p.score for p in request.player_scores)
    if total != 0:
        logger.warning(f"Scores for {request.date} group={request.group} sum to {total}, not 0")

    job = PendingSheetSync(
        date=request.date,
        group=request.group,
        location=request.location,
        duration=request.duration,
        player_scores={p.name: p.score for p in request.player_scores},
        status="pending",
        created_at=datetime.now(UTC).isoformat(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "status": "queued",
        "job_id": job.id,
        "message": "Round queued for background sync. Check /admin/spreadsheet/sync-status for progress.",
        "date": request.date,
        "group": request.group,
        "players": [p.name for p in request.player_scores],
    }


@router.get("/sync-status")
def get_sync_queue_status(
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> Any:
    """Get recent sheet sync queue entries and their processing status."""
    jobs = (
        db.query(PendingSheetSync)
        .order_by(PendingSheetSync.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": j.id,
            "date": j.date,
            "group": j.group,
            "players": list(j.player_scores.keys()) if j.player_scores else [],
            "status": j.status,
            "dedup_action": j.dedup_action,
            "created_at": j.created_at,
            "processed_at": j.processed_at,
            "error": j.error,
        }
        for j in jobs
    ]


@router.get("/config")
def get_spreadsheet_config():
    """Get the current spreadsheet configuration."""
    import os

    # Check OAuth status
    oauth_creds = os.environ.get("GOOGLE_OAUTH_CREDENTIALS")
    oauth_status = "not_configured"
    if oauth_creds:
        try:
            import json

            creds = json.loads(oauth_creds)
            has_refresh = bool(creds.get("refresh_token"))
            has_client_id = bool(creds.get("client_id"))
            has_client_secret = bool(creds.get("client_secret"))
            if has_refresh and has_client_id and has_client_secret:
                oauth_status = "configured"
            else:
                oauth_status = (
                    f"incomplete (refresh={has_refresh}, client_id={has_client_id}, secret={has_client_secret})"
                )
        except Exception as e:
            oauth_status = f"invalid_json: {e}"

    # Test token retrieval
    token = _get_access_token()
    token_status = "success" if token else "failed"

    return {
        "primary_sheet_id": PRIMARY_SHEET_ID,
        "writable_sheet_id": WRITABLE_SHEET_ID,
        "primary_url": f"https://docs.google.com/spreadsheets/d/{PRIMARY_SHEET_ID}",
        "writable_url": f"https://docs.google.com/spreadsheets/d/{WRITABLE_SHEET_ID}",
        "sheets": ["Dashboard", "Details"],
        "details_columns": {
            "A": "Date (DD-Mon)",
            "B": "Group (A-D)",
            "C": "Member",
            "D": "Score (quarters)",
            "E": "Location",
            "F": "Duration",
        },
        "oauth_status": oauth_status,
        "token_status": token_status,
    }


# ============================================================================
# Reconciliation Endpoints (still hit Sheets live — admin-only comparison tool)
# ============================================================================


@router.get("/reconcile/status")
def get_reconciliation_status():
    """Get sync status between primary and writable spreadsheets."""
    try:
        service = get_reconciliation_service()
        return service.get_sync_status()
    except Exception as e:
        logger.error(f"Failed to get reconciliation status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {e!s}")


@router.post("/reconcile/primary-to-writable")
def sync_primary_to_writable(dry_run: bool = Query(True, description="Preview changes without applying")) -> Any:
    """Copy missing rounds from primary sheet to writable sheet."""
    try:
        service = get_reconciliation_service()
        return service.sync_primary_to_writable(dry_run=dry_run)
    except Exception as e:
        logger.error(f"Failed to sync primary to writable: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {e!s}")


@router.post("/reconcile/writable-to-primary")
def sync_writable_to_primary(dry_run: bool = Query(True, description="Preview changes without applying")) -> Any:
    """Copy missing rounds from writable sheet to primary sheet."""
    try:
        service = get_reconciliation_service()
        return service.sync_writable_to_primary(dry_run=dry_run)
    except Exception as e:
        logger.error(f"Failed to sync writable to primary: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {e!s}")


@router.get("/reconcile/diff")
def get_reconciliation_diff():
    """Get detailed diff between primary and writable sheets."""
    try:
        service = get_reconciliation_service()
        result = service.compare_sheets()

        return {
            "summary": {
                "is_synced": result.is_synced,
                "primary_total": result.primary_total,
                "writable_total": result.writable_total,
                "matched": result.matched,
                "primary_only_count": len(result.primary_only),
                "writable_only_count": len(result.writable_only),
            },
            "primary_only": [
                {
                    "date": r.date,
                    "group": r.group,
                    "member": r.member,
                    "score": r.score,
                    "location": r.location,
                }
                for r in result.primary_only
            ],
            "writable_only": [
                {
                    "date": r.date,
                    "group": r.group,
                    "member": r.member,
                    "score": r.score,
                    "location": r.location,
                }
                for r in result.writable_only
            ],
        }
    except Exception as e:
        logger.error(f"Failed to get reconciliation diff: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get diff: {e!s}")
