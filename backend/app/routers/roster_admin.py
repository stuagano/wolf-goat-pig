"""Admin: compare the canonical roster with Jeff's legacy dropdown and remove junk entries."""

import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import roster_drift_service
from ..utils.admin_auth import require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/legacy-players", tags=["legacy-players"], dependencies=[Depends(require_admin)])


@router.get("/drift")
def get_roster_drift(db: Session = Depends(get_db)) -> dict[str, Any]:
    """What's on Jeff's dropdown vs. the app roster (reads the old site live, read-only)."""
    try:
        dropdown = roster_drift_service.fetch_dropdown_names()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Could not read the legacy tee sheet: {exc}") from exc
    return roster_drift_service.compute_drift(db, dropdown)


@router.delete("/{name}")
def delete_roster_name(name: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Remove a roster entry no active profile uses (e.g. an email that was promoted by mistake)."""
    result = roster_drift_service.remove_roster_name(db, name)
    if not result["removed"]:
        raise HTTPException(status_code=result["status"], detail=result["message"])
    logger.info("Removed roster name '%s'", result["name"])
    return result
