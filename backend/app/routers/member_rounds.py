"""Member round-posting + peer attestation.

Members self-post their Wolf-Goat-Pig round result (quarters won/lost — the same
quantity Jeff hand-enters into the Google Sheet), tied to their profile, one
round per member per calendar day. A posted round is ``status='pending'`` and
becomes authoritative (``status='attested'``) only after another member of the
foursome attests it.

These rows live in ``legacy_rounds`` with ``source='member'`` so they survive
the restart-time sheet sync (which only wipes ``primary_sheet``/``writable_sheet``
rows) and are excluded from leaderboards/standings/history until attested.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import LegacyRound, PlayerProfile
from ..services.auth_service import get_current_user
from ..services.email_service import get_email_service
from ..services.legacy_player_service import get_canonical_name
from ..utils.time import utc_now

logger = logging.getLogger(__name__)

router = APIRouter(tags=["member-rounds"])


class PostRoundRequest(BaseModel):
    """A member-posted round result (quarters won/lost)."""

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    score: int = Field(..., description="Quarters won (positive) or lost (negative)")
    location: str | None = Field(None, description="Course name")
    group: str | None = Field(None, description="Group letter")
    duration: str | None = Field(None, description="Duration, e.g. 02:15:00")
    foursome: list[str] = Field(
        ...,
        description="1-3 OTHER players' canonical roster names eligible to attest (must not include yourself)",
    )


def _serialize(r: LegacyRound) -> dict[str, Any]:
    """Render a round in the pinned response shape."""
    return {
        "id": r.id,
        "date": r.date,
        "score": r.score,
        "member": r.member,
        "status": r.status,
        "foursome": r.foursome or [],
        "attested_by": r.attested_by_profile_id,
        "attested_at": r.attested_at.isoformat() if r.attested_at else None,
    }


def _notify_foursome(db: Session, round_row: LegacyRound, poster: PlayerProfile) -> None:
    """Email each foursome member that has a PlayerProfile+email an attestation
    request. Best-effort: any email failure must NOT fail the request."""
    try:
        email_service = get_email_service()
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("Could not get email service for attestation request: %s", e)
        return

    for name in round_row.foursome or []:
        try:
            profile = db.query(PlayerProfile).filter(func.lower(PlayerProfile.legacy_name) == name.lower()).first()
            if profile and profile.email:
                email_service.send_attestation_request(
                    to_email=profile.email,
                    attester_name=profile.name or name,
                    poster_name=poster.legacy_name or poster.name or "A member",
                    round_date=round_row.date,
                    score=round_row.score,
                )
        except Exception as e:
            logger.warning("Failed to send attestation request to '%s': %s", name, e)


@router.post("/players/me/round", status_code=201)
def post_my_round(
    body: PostRoundRequest,
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Post (or replace a still-pending) round result for the current member."""
    if not current_user.legacy_name:
        raise HTTPException(
            status_code=400,
            detail="Link your roster name first via PUT /players/me/legacy-name",
        )

    try:
        datetime.strptime(body.date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    if not 1 <= len(body.foursome) <= 3:
        raise HTTPException(
            status_code=400,
            detail="foursome must list 1-3 other players' canonical roster names",
        )

    # Validate + canonicalize each foursome name; reject the poster.
    canonical_foursome: list[str] = []
    for name in body.foursome:
        canonical = get_canonical_name(name, db)
        if not canonical:
            raise HTTPException(
                status_code=400,
                detail=f"'{name}' is not a valid roster name. Use /players/legacy-players to see valid names.",
            )
        if canonical.lower() == current_user.legacy_name.lower():
            raise HTTPException(status_code=400, detail="foursome must not include yourself")
        if canonical not in canonical_foursome:
            canonical_foursome.append(canonical)

    now = utc_now()
    existing = (
        db.query(LegacyRound)
        .filter(
            LegacyRound.source == "member",
            LegacyRound.member == current_user.legacy_name,
            LegacyRound.date == body.date,
        )
        .first()
    )

    if existing is not None:
        if existing.status == "attested":
            raise HTTPException(
                status_code=409,
                detail="You already posted an attested round for that date",
            )
        # Still pending — allow replace before attestation.
        existing.score = body.score
        existing.location = body.location
        existing.group = body.group
        existing.duration = body.duration
        existing.foursome = canonical_foursome
        existing.player_profile_id = current_user.id
        existing.status = "pending"
        existing.synced_at = now.isoformat()
        row = existing
    else:
        row = LegacyRound(
            date=body.date,
            group=body.group,
            member=current_user.legacy_name,
            score=body.score,
            location=body.location,
            duration=body.duration,
            source="member",
            status="pending",
            synced_at=now.isoformat(),
            created_at=now.isoformat(),
            player_profile_id=current_user.id,
            foursome=canonical_foursome,
        )
        db.add(row)

    db.commit()
    db.refresh(row)

    _notify_foursome(db, row, current_user)

    return _serialize(row)


@router.get("/players/me/rounds")
def get_my_rounds(
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List the current member's own posted rounds (pending and attested)."""
    rows = (
        db.query(LegacyRound)
        .filter(
            LegacyRound.source == "member",
            LegacyRound.player_profile_id == current_user.id,
        )
        .order_by(LegacyRound.date.desc())
        .all()
    )
    return [_serialize(r) for r in rows]


@router.get("/rounds/pending-attestation")
def get_pending_attestation(
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List pending rounds the current member is eligible to attest."""
    if not current_user.legacy_name:
        return []

    rows = (
        db.query(LegacyRound)
        .filter(
            LegacyRound.source == "member",
            LegacyRound.status == "pending",
            LegacyRound.member != current_user.legacy_name,
        )
        .order_by(LegacyRound.date.desc())
        .all()
    )

    legacy = current_user.legacy_name.lower()
    eligible = [r for r in rows if any(n.lower() == legacy for n in (r.foursome or []))]
    return [_serialize(r) for r in eligible]


@router.post("/rounds/{round_id}/attest")
def attest_round(
    round_id: int,
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Attest a pending round posted by another foursome member."""
    row = db.query(LegacyRound).filter(LegacyRound.id == round_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Round not found")

    legacy = current_user.legacy_name
    foursome = row.foursome or []
    eligible = bool(legacy) and legacy != row.member and any(n.lower() == legacy.lower() for n in foursome)
    if not eligible:
        raise HTTPException(status_code=403, detail="You are not eligible to attest this round")

    if row.status != "pending":
        raise HTTPException(status_code=409, detail="Round is not pending attestation")

    row.status = "attested"
    row.attested_by_profile_id = current_user.id
    row.attested_at = utc_now()
    db.commit()
    db.refresh(row)

    return _serialize(row)
