"""Feature flags — public read, admin write."""

import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AppConfig
from ..utils.admin_auth import require_admin

logger = logging.getLogger("app.routers.features")

router = APIRouter(prefix="/config", tags=["config"])

DEFAULTS: dict[str, bool] = {
    "foretees": False,
    "scorecard_scan": True,
    "livsow": True,
    "commissioner_chat": True,
}


def _get_flags(db: Session) -> dict[str, bool]:
    row = db.query(AppConfig).filter(AppConfig.name == "features").first()
    stored = row.value if row else {}
    return {**DEFAULTS, **stored}


@router.get("/features")
def get_features(db: Session = Depends(get_db)) -> dict[str, Any]:
    return {"features": _get_flags(db)}


@router.post("/features", dependencies=[Depends(require_admin)])
def set_features(
    body: dict[str, bool],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    row = db.query(AppConfig).filter(AppConfig.name == "features").first()
    current = dict(row.value) if row else {}
    # Only update known keys
    updated = {**current, **{k: v for k, v in body.items() if k in DEFAULTS}}
    if row:
        row.value = updated
    else:
        db.add(AppConfig(name="features", value=updated))
    db.commit()
    logger.info(f"Feature flags updated: {updated}")
    return {"features": {**DEFAULTS, **updated}}
