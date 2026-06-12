"""GroupMe bridge endpoints — read the league group, post via bot."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from .. import models
from ..services.auth_service import get_current_user
from ..services.groupme_service import get_messages, is_configured, list_groups, post_message
from ..utils.admin_auth import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/groupme", tags=["groupme"])


class PostMessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=900)


@router.get("/status")
def groupme_status() -> Any:
    """Whether the bridge is configured (read side / post side)."""
    return is_configured()


@router.get("/messages")
def groupme_messages(
    limit: int = Query(50, ge=1, le=100),
    refresh: bool = Query(False),
    before_id: str | None = Query(None, description="Page backwards: messages older than this id"),
) -> Any:
    """Group messages, oldest-first. Head page cached ~20s; before_id pages history."""
    return get_messages(limit=limit, force_refresh=refresh, before_id=before_id)


@router.post("/messages")
def groupme_post(
    body: PostMessageRequest,
    current_user: models.PlayerProfile = Depends(get_current_user),
) -> Any:
    """Post to the GroupMe group as the logged-in player (via the bot).

    Auth required — anonymous web visitors must not be able to spam the
    league's chat.
    """
    author = current_user.name or "Web user"
    result = post_message(body.text, author=author)
    if not result.get("posted"):
        raise HTTPException(status_code=502, detail=result.get("error", "Post failed"))
    return result


@router.get("/groups", dependencies=[Depends(require_admin)])
def groupme_groups() -> Any:
    """Admin setup helper: list the token owner's groups to find the group ID."""
    try:
        return {"groups": list_groups()}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("GroupMe group list failed: %s", e)
        raise HTTPException(status_code=502, detail="GroupMe API error")
