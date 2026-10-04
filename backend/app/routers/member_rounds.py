"""Honor-system group results and historical peer-attestation endpoints.

One linked participant posts 2-4 player results in one transaction. New results
use status='posted' and count immediately; historical pending records are left
intact and can still be attested through the legacy API.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import LegacyRound, PlayerProfile
from ..services.auth_service import get_current_user
from ..services.legacy_player_service import get_canonical_name
from ..services.unified_data_service import get_unified_data_service
from ..utils.time import utc_now

logger = logging.getLogger(__name__)

router = APIRouter(tags=["member-rounds"])


class PlayerRoundResult(BaseModel):
    member: str = Field(..., min_length=1, description="Canonical roster name")
    score: int = Field(..., strict=True, ge=-2147483648, le=2147483647, description="Whole quarters won or lost")


class PostRoundRequest(BaseModel):
    """One participant submits the whole group's results on the honor system."""

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    results: list[PlayerRoundResult] = Field(..., min_length=2, max_length=4)
    location: str | None = None
    group: str | None = None
    duration: str | None = None


def _serialize(r: LegacyRound) -> dict[str, Any]:
    """Render a round in the pinned response shape."""
    return {
        "id": r.id,
        "round_code": f"WGP-{r.id}",
        "date": r.date,
        "score": r.score,
        "member": r.member,
        "location": r.location,
        "status": r.status,
        "foursome": r.foursome or [],
        "attested_by": r.attested_by_profile_id,
        "attested_at": r.attested_at.isoformat() if r.attested_at else None,
    }


def _history_from_rounds(member: str, rounds: list[Any], *, recent_limit: int = 5) -> dict[str, Any]:
    """Aggregate club history for the Account personal-stats panel.

    ``score`` on these rounds is quarters won/lost (not stroke play), matching
    the Google Sheet / legacy_rounds convention.
    """
    if not rounds:
        return {
            "found": False,
            "member": member,
            "rounds_played": 0,
            "total_quarters": 0,
            "average_per_round": 0.0,
            "best_round": None,
            "worst_round": None,
            "recent_rounds": [],
        }

    total_quarters = sum(r.score for r in rounds)
    round_count = len(rounds)
    best = max(r.score for r in rounds)
    worst = min(r.score for r in rounds)
    recent = [
        {
            "date": r.date_sortable,
            "date_display": r.date,
            "score": r.score,
            "location": r.location,
            "group": r.group,
            "source": r.source,
        }
        for r in rounds[:recent_limit]
    ]

    return {
        "found": True,
        "member": rounds[0].member,
        "rounds_played": round_count,
        "total_quarters": total_quarters,
        "average_per_round": round(total_quarters / round_count, 1) if round_count else 0.0,
        "best_round": best,
        "worst_round": worst,
        "recent_rounds": recent,
    }


@router.post("/players/me/round", status_code=201)
def post_my_round(
    body: PostRoundRequest,
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Post every participant's result atomically, without peer attestation."""
    if not current_user.legacy_name:
        raise HTTPException(status_code=400, detail="Link your roster name before posting results")
    try:
        parsed_date = datetime.strptime(body.date, "%Y-%m-%d")
        if parsed_date.strftime("%Y-%m-%d") != body.date:
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    results: dict[str, int] = {}
    for result in body.results:
        canonical = get_canonical_name(result.member.strip(), db)
        if not canonical:
            raise HTTPException(status_code=400, detail=f"'{result.member}' is not a valid roster name")
        if canonical in results:
            raise HTTPException(status_code=400, detail="Each player must appear exactly once")
        results[canonical] = result.score
    if current_user.legacy_name.lower() not in {name.lower() for name in results}:
        raise HTTPException(status_code=400, detail="Include your own result when posting for the group")

    existing = (
        db.query(LegacyRound)
        .filter(
            LegacyRound.source == "member",
            func.lower(LegacyRound.member).in_([name.lower() for name in results]),
            LegacyRound.date == body.date,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"{existing.member} already has a posted result for that date")

    profiles = (
        db.query(PlayerProfile)
        .filter(func.lower(PlayerProfile.legacy_name).in_([name.lower() for name in results]))
        .all()
    )
    profile_ids = {p.legacy_name.lower(): p.id for p in profiles}
    now = utc_now().isoformat()
    rows = [
        LegacyRound(
            date=body.date,
            group=body.group,
            member=name,
            score=score,
            location=body.location,
            duration=body.duration,
            source="member",
            status="posted",
            synced_at=now,
            created_at=now,
            player_profile_id=profile_ids.get(name.lower()),
            submitted_by_profile_id=current_user.id,
            foursome=[partner for partner in results if partner != name],
        )
        for name, score in results.items()
    ]
    db.add_all(rows)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        # A concurrent group submission may win after the preflight check.
        if "ux_member_round_per_day" in str(
            exc.orig
        ) or "UNIQUE constraint failed: legacy_rounds.member, legacy_rounds.date" in str(exc.orig):
            raise HTTPException(
                status_code=409, detail="A result for this group was already posted for that date"
            ) from exc
        raise
    return {"rounds": [_serialize(row) for row in rows]}


@router.get("/players/me/rounds")
def get_my_rounds(
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List results credited to the linked roster player, whoever submitted them."""
    rows = (
        db.query(LegacyRound)
        .filter(
            LegacyRound.source == "member",
            func.lower(LegacyRound.member) == (current_user.legacy_name or "").lower(),
        )
        .order_by(LegacyRound.date.desc())
        .all()
    )
    return [_serialize(r) for r in rows]


@router.get("/players/me/history")
def get_my_history(
    recent_limit: int = 5,
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Club history for the signed-in member (sheet + attested + in-app rounds).

    Powers the Account personal-stats panel. Prefer ``legacy_name`` when linked
    so sheet rows match; fall back to display name for accounts that have only
    played in-app games.
    """
    if recent_limit < 1 or recent_limit > 50:
        raise HTTPException(status_code=400, detail="recent_limit must be between 1 and 50")

    lookup_name = (current_user.legacy_name or current_user.name or "").strip()
    if not lookup_name:
        return _history_from_rounds("", [], recent_limit=recent_limit)

    service = get_unified_data_service(db=db)
    rounds = service.get_player_history(lookup_name)
    return _history_from_rounds(lookup_name, rounds, recent_limit=recent_limit)


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
