"""The club's posted tee times for one day, shown on the signup page.

Free text per date (e.g. "12:48 (1-4)"). Anyone can read; any signed-in member
can edit. Not related to ForeTees booking (/api/foretees/tee-times).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import DailyTeeTimes, PlayerProfile
from ..services.auth_service import get_current_user
from ..utils.time import utc_now

router = APIRouter(prefix="/signups/tee-times", tags=["signups"])

MAX_TEE_TIMES_LENGTH = 2000


class TeeTimesUpdate(BaseModel):
    tee_times: str = Field(..., max_length=MAX_TEE_TIMES_LENGTH)


def _validate_date(date: str) -> str:
    try:
        if datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d") != date:
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    return date


def _serialize(date: str, row: DailyTeeTimes | None) -> dict[str, Any]:
    return {
        "date": date,
        "tee_times": row.tee_times if row else "",
        "updated_at": row.updated_at if row else None,
    }


@router.get("/{date}")
def get_day_tee_times(date: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Tee times posted for one day; empty text when none have been entered."""
    _validate_date(date)
    return _serialize(date, db.get(DailyTeeTimes, date))


@router.put("/{date}")
def put_day_tee_times(
    date: str,
    body: TeeTimesUpdate,
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Replace one day's tee times. Only that date's row changes."""
    _validate_date(date)
    row = db.get(DailyTeeTimes, date)
    if row is None:
        row = DailyTeeTimes(date=date)
        db.add(row)
    row.tee_times = body.tee_times
    row.updated_by_profile_id = current_user.id
    row.updated_at = utc_now().isoformat()
    db.commit()
    return _serialize(date, row)
