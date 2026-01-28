"""Admin routes for Google Sheets synchronization.

These endpoints allow admins to:
- View current spreadsheet data
- Sync completed games to the spreadsheet
- View leaderboard from spreadsheet
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.spreadsheet_sync_service import (
    PRIMARY_SHEET_ID,
    WRITABLE_SHEET_ID,
    RoundResult,
    get_spreadsheet_sync_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/spreadsheet",
    tags=["admin", "spreadsheet"],
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
    duration: Optional[str] = Field(None, description="Duration in HH:MM:SS format")
    player_scores: List[PlayerScoreInput] = Field(..., description="List of player scores")


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
    duration: Optional[str] = None


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_spreadsheet_leaderboard():
    """Get the current leaderboard from the Google Sheet."""
    try:
        service = get_spreadsheet_sync_service()
        leaderboard = service.get_leaderboard()
        return leaderboard
    except Exception as e:
        logger.error(f"Failed to fetch leaderboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch leaderboard: {str(e)}")


@router.get("/rounds", response_model=List[RoundResultResponse])
def get_all_rounds(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
):
    """Get all round results from the spreadsheet."""
    try:
        service = get_spreadsheet_sync_service()
        results = service.get_all_rounds()

        # Return most recent first (reverse chronological)
        return [
            RoundResultResponse(
                date=r.date,
                group=r.group,
                member=r.member,
                score=r.score,
                location=r.location,
                duration=r.duration,
            )
            for r in results[-limit:]
        ]
    except Exception as e:
        logger.error(f"Failed to fetch rounds: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch rounds: {str(e)}")


@router.get("/rounds/by-date/{date}", response_model=List[Dict[str, Any]])
def get_rounds_by_date(date: str):
    """Get all rounds for a specific date.

    Date format: DD-Mon (e.g., "21-Jul") to match spreadsheet format.
    """
    try:
        service = get_spreadsheet_sync_service()
        summaries = service.get_rounds_by_date(date)

        return [
            {
                "date": s.date,
                "group": s.group,
                "location": s.location,
                "duration": s.duration,
                "player_count": s.player_count,
                "total_score": s.total_score,
                "players": [{"member": p.member, "score": p.score} for p in s.players],
            }
            for s in summaries
        ]
    except Exception as e:
        logger.error(f"Failed to fetch rounds for {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch rounds: {str(e)}")


@router.get("/player/{member_name}", response_model=List[RoundResultResponse])
def get_player_history(member_name: str):
    """Get all rounds for a specific player."""
    try:
        service = get_spreadsheet_sync_service()
        results = service.get_player_history(member_name)

        return [
            RoundResultResponse(
                date=r.date,
                group=r.group,
                member=r.member,
                score=r.score,
                location=r.location,
                duration=r.duration,
            )
            for r in results
        ]
    except Exception as e:
        logger.error(f"Failed to fetch player history for {member_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch player history: {str(e)}")


@router.post("/sync-round")
def sync_round_to_spreadsheet(request: SyncRoundRequest):
    """Sync a completed round to the Google Sheet.

    This adds the round results to the Details sheet. The Dashboard
    will automatically recalculate the leaderboard.

    NOTE: Player names must match exactly what's in the spreadsheet.
    Use the /legacy-players endpoint to validate names first.
    """
    try:
        # Parse date
        try:
            game_date = datetime.strptime(request.date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

        # Validate scores sum to 0
        total = sum(p.score for p in request.player_scores)
        if total != 0:
            logger.warning(f"Scores sum to {total}, not 0")

        # Build player scores dict
        player_scores = {p.name: p.score for p in request.player_scores}

        # Sync to spreadsheet
        service = get_spreadsheet_sync_service()
        success = service.sync_completed_game(
            game_date=game_date,
            group=request.group,
            location=request.location,
            player_scores=player_scores,
            duration=request.duration,
        )

        if success:
            return {
                "status": "success",
                "message": f"Synced {len(player_scores)} player results to spreadsheet",
                "date": service.format_date_for_sheet(game_date),
                "group": request.group,
                "players": list(player_scores.keys()),
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to sync to spreadsheet")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync round: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync round: {str(e)}")


@router.get("/config")
def get_spreadsheet_config():
    """Get the current spreadsheet configuration."""
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
    }
