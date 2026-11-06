"""Current golfer sets their own name when Auth0 only gave us their email."""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services.auth_service import get_current_user
from ..services.profile_name_service import set_own_name
from ..utils.api_helpers import handle_api_errors

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/me", tags=["players"])


class MyNameUpdate(BaseModel):
    first_name: str
    last_name: str


@router.put("/name", response_model=schemas.PlayerProfileResponse)
@handle_api_errors(operation_name="update my name")
async def update_my_name(
    body: MyNameUpdate,
    current_user: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.PlayerProfileResponse:
    """Replace an email-as-name with the golfer's first and last name (once)."""
    player = set_own_name(db, current_user, body.first_name, body.last_name)
    logger.info("Player profile id=%s set their name", player.id)
    return schemas.PlayerProfileResponse.model_validate(player)
