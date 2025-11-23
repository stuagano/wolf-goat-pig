# backend/app/routes/betting_events.py
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

VALID_EVENT_TYPES = {
    "DOUBLE_OFFERED",
    "DOUBLE_ACCEPTED",
    "DOUBLE_DECLINED",
    "PRESS_OFFERED",
    "PRESS_ACCEPTED",
    "PRESS_DECLINED",
    "TEAMS_FORMED",
    "HOLE_COMPLETE"
}

class BettingEvent(BaseModel):
    eventId: str
    eventType: str
    actor: str
    data: Dict[str, Any]
    timestamp: str

class BettingEventsPayload(BaseModel):
    holeNumber: int
    events: List[BettingEvent]
    clientTimestamp: str

class BettingEventsResponse(BaseModel):
    success: bool
    confirmedEvents: List[str]
    corrections: List[Dict[str, Any]] = []

@router.post("/api/games/{game_id}/betting-events", response_model=BettingEventsResponse)
async def create_betting_events(game_id: str, payload: BettingEventsPayload) -> BettingEventsResponse:
    """
    Store betting events for a game.
    Validates event types and returns confirmed event IDs.
    """
    confirmed = []

    for event in payload.events:
        if event.eventType not in VALID_EVENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type: {event.eventType}"
            )
        confirmed.append(event.eventId)

    # TODO: Persist to database
    # For now, just confirm receipt

    return BettingEventsResponse(
        success=True,
        confirmedEvents=confirmed,
        corrections=[]
    )
