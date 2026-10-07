"""Turn authenticated app feedback into issues in the fixed project repository."""

import logging
import os
from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from ..middleware.rate_limiting import rate_limiter
from ..models import PlayerProfile
from ..services.auth_service import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feedback", tags=["feedback"])
REPOSITORY = "stuagano/wolf-goat-pig"
TYPE_NAMES = {"bug": "Bug", "feature": "Feature request", "general": "General feedback"}


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    type: Literal["bug", "feature", "general"]
    title: str = Field(min_length=1, max_length=120, pattern=r"^[^\r\n]+$")
    description: str = Field(min_length=1, max_length=5000)
    steps: str = Field(default="", max_length=3000)


class FeedbackResponse(BaseModel):
    number: int = Field(gt=0)
    url: str


@router.post("", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    body: FeedbackRequest,
    current_user: PlayerProfile = Depends(get_current_user),
) -> FeedbackResponse:
    token = os.getenv("WGP_FEEDBACK_GITHUB_TOKEN", "").strip()
    if not token:
        raise HTTPException(503, "Feedback submission is not configured yet. Please contact the club administrator.")

    # ponytail: cooldown is per worker; use shared storage if cross-instance limits become necessary.
    try:
        rate_limiter.check_limit("feedback", min_interval_seconds=60, client_id=str(current_user.id))
    except HTTPException as exc:
        raise HTTPException(429, "Please wait one minute between feedback submissions.", headers=exc.headers) from exc

    kind = TYPE_NAMES[body.type]
    issue_body = f"## {kind}\n\n{body.description}"
    if body.type == "bug" and body.steps:
        issue_body += f"\n\n## Steps to reproduce\n\n{body.steps}"
    issue_body += "\n\n---\nSubmitted through the Wolf Goat Pig feedback form."

    # No account details or browser context are copied into this public issue.
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"https://api.github.com/repos/{REPOSITORY}/issues",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2026-03-10",
                },
                json={"title": f"[Feedback: {kind}] {body.title}", "body": issue_body},
            )
    except httpx.RequestError:
        # A lost response can follow a successful write. Never retry this POST automatically.
        raise HTTPException(
            504, "Could not confirm delivery. Check the GitHub issues before submitting again."
        ) from None

    if response.status_code != 201:
        logger.warning("GitHub feedback submission returned HTTP %s", response.status_code)
        raise HTTPException(
            502, "GitHub could not accept your feedback. Please try later or contact the club administrator."
        )
    try:
        number = response.json()["number"]
        if type(number) is not int or number < 1:
            raise ValueError("Invalid issue number")
    except (ValueError, KeyError, TypeError):
        raise HTTPException(
            502, "Could not confirm delivery. Check the GitHub issues before submitting again."
        ) from None

    return FeedbackResponse(number=number, url=f"https://github.com/{REPOSITORY}/issues/{number}")
