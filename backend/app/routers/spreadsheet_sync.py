"""Admin routes for Google Sheets synchronization.

These endpoints allow admins to:
- View current spreadsheet data (served from legacy_rounds DB — synced every 2h)
- Sync completed games to the spreadsheet
- View leaderboard from spreadsheet
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import LegacyRound, PendingSheetSync
from ..services.spreadsheet_sync_service import (
    PRIMARY_SHEET_ID,
    WRITABLE_SHEET_ID,
    _get_access_token,
    get_reconciliation_service,
)
from ..utils.admin_auth import require_admin

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
    """Queue accepted UUID results, never client date/name guesses."""

    game_id: str
    source_scope: str = Field(min_length=1)
    source_round_token: str = Field(min_length=1)
    operation_key: str = Field(min_length=1)
    expected_revision: int = Field(ge=0, strict=True)
    expected_epoch: int = Field(ge=0, strict=True)
    expected_source_version: str = Field(min_length=1)
    action: str = Field(pattern="^(insert|update)$")


class LeaderboardEntry(BaseModel):
    """A single entry in the leaderboard."""

    rank: int
    member: str
    quarters: float
    average: float | None
    rounds: int
    qb: float
    known_participation_count: int = 0
    incomplete_round_count: int = 0


class RoundResultResponse(BaseModel):
    """Response model for a round result."""

    date: str | None
    # group/location are nullable: member-posted rounds may omit them.
    group: str | None = None
    member: str
    score: float | None
    game_id: str | None = None
    participant_id: str | None = None
    score_eligible: bool = True
    location: str | None = None
    duration: str | None = None


def _canonical(db: Session):
    """The one canonical read authority, or None before cutover."""
    from ..services.canonical_round_reads import canonical_mode
    from ..services.unified_data_service import get_unified_data_service

    return get_unified_data_service(db) if canonical_mode(db) else None


def _round_rows(rounds) -> list[RoundResultResponse]:
    return [
        RoundResultResponse(
            date=r.date_sortable or r.date,
            group=r.group,
            member=r.member,
            score=r.score,
            location=r.location,
            duration=r.duration,
            game_id=r.game_id,
            participant_id=r.participant_id,
            score_eligible=r.score_eligible,
        )
        for r in rounds
    ]


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
def get_spreadsheet_leaderboard(db: Session = Depends(get_db)):
    """Get the current leaderboard computed from the legacy_rounds DB (synced every 2h)."""
    service = _canonical(db)
    if service is not None:
        entries = service.get_unified_leaderboard()
        leader = entries[0].quarters if entries else 0
        return [
            LeaderboardEntry(
                rank=i,
                member=e.member,
                quarters=e.quarters,
                rounds=e.rounds,
                # Old integer floor-division misreported fractional averages.
                average=round(e.average, 2) if e.average is not None else None,
                qb=leader - e.quarters,
                known_participation_count=e.known_participation_count,
                incomplete_round_count=e.incomplete_round_count,
            )
            for i, e in enumerate(entries, 1)
        ]
    rows = (
        db.query(
            LegacyRound.member,
            func.sum(LegacyRound.score).label("quarters"),
            func.count(LegacyRound.id).label("rounds"),
        )
        # Exclude pending member-posted rounds (not yet attested).
        .filter(LegacyRound.status != "pending")
        .group_by(LegacyRound.member)
        .all()
    )

    if not rows:
        return []

    entries = [{"member": r.member, "quarters": r.quarters, "rounds": r.rounds} for r in rows]
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
    """Get accepted canonical history, or the pre-cutover cache."""
    service = _canonical(db)
    if service is not None:
        return _round_rows(service.get_all_rounds()[:limit])
    rows = (
        db.query(LegacyRound)
        .filter(LegacyRound.status != "pending")  # exclude unattested member rounds
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
    service = _canonical(db)
    if service is not None:
        summaries = {}
        for r in service.get_all_rounds():
            if r.date_sortable != date:
                continue
            summary = summaries.setdefault(
                r.game_id,
                {
                    "game_id": r.game_id,
                    "date": r.date_sortable,
                    "group": r.group,
                    "location": r.location,
                    "duration": r.duration,
                    "player_count": 0,
                    "total_score": 0 if r.score_eligible else None,
                    "players": [],
                },
            )
            summary["player_count"] += 1
            if summary["total_score"] is not None:
                summary["total_score"] += r.score
            summary["players"].append({"member": r.member, "score": r.score, "participant_id": r.participant_id})
        return list(summaries.values())
    rows = (
        db.query(LegacyRound)
        .filter(LegacyRound.date == date, LegacyRound.status != "pending")
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
    """Get profile-associated history without assigning guests by display name."""
    service = _canonical(db)
    if service is not None:
        return _round_rows(service.get_player_history(member_name))
    rows = (
        db.query(LegacyRound)
        .filter(LegacyRound.member == member_name, LegacyRound.status != "pending")
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
def sync_round_to_spreadsheet(request: SyncRoundRequest, db: Session = Depends(get_db)) -> Any:
    """Enqueue a revision-bound accepted UUID; Gate B must already be approved."""
    from ..services.round_sheet_delivery import enqueue_sheet_sync

    try:
        job = enqueue_sheet_sync(db, **request.model_dump())
        db.commit()
        return {"status": "queued", "job_id": job.id, "game_id": job.game_id}
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/sync-status")
def get_sync_queue_status(
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> Any:
    """Get recent sheet sync queue entries and their processing status."""
    jobs = db.query(PendingSheetSync).order_by(PendingSheetSync.created_at.desc()).limit(limit).all()
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


@router.post("/sync-legacy-rounds")
def trigger_legacy_rounds_sync(db: Session = Depends(get_db)) -> Any:
    """Manually trigger the shared complete-snapshot ingestion boundary.

    Normally runs every two hours; held evidence never replaces accepted data.
    """
    from ..services.spreadsheet_sync_service import refresh_round_history

    return refresh_round_history(db)


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
