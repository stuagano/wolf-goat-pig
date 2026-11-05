"""Scanned-scorecard routes — record a round from a scorecard, backfill per-hole quarters, photo."""

import base64
import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from .. import database, models
from ..services.auth_service import get_current_user
from ..services.completed_game_service import validate_round_players, validate_round_scores
from ..utils.admin_auth import is_admin_profile
from ..utils.round_card import mark_card_edited, require_round_member_or_admin
from ..utils.time import utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])


class ScorecardRoundPlayer(BaseModel):
    name: str
    player_profile_id: int | None = None
    # When the user explicitly chose "keep as typed (unlinked)", do NOT
    # auto-resolve a profile from the name — otherwise a guest whose typed
    # name happens to match a roster legacy_name would be wrongly linked to
    # that member, corrupting their standings.
    unlinked: bool = False


class ScorecardRoundHoleQuarter(BaseModel):
    player_index: int
    hole: int
    quarters: float


class ScorecardRoundRequest(BaseModel):
    players: list[ScorecardRoundPlayer]
    per_hole_quarters: list[ScorecardRoundHoleQuarter]
    course_name: str | None = None
    played_at: str | None = None
    image_base64: str | None = None

    @field_validator("played_at")
    @classmethod
    def validate_played_at(cls, value: str | None) -> str | None:
        if value is not None and date.fromisoformat(value).isoformat() != value:
            raise ValueError("played_at must be a valid YYYY-MM-DD date")
        return value


@router.post("/from-scorecard")
async def create_round_from_scorecard(
    body: ScorecardRoundRequest,
    profile: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """Record a completed round straight from a scanned scorecard.

    Builds a completed game (players + per-hole quarters) and persists the
    same GameRecord/GamePlayerResult rows a live-scored game would, so a
    scanned round shows up in standings/history identically.
    """
    import uuid

    from ..services.completed_game_service import build_hole_history, persist_completed_game

    if len(body.players) not in (4, 5, 6):
        raise HTTPException(status_code=400, detail="Wolf Goat Pig requires 4, 5, or 6 players")

    # Validate every quarter entry references a real player and a hole in 1-18,
    # so malformed input to this public endpoint is rejected rather than
    # silently dropped (build_hole_history skips out-of-range entries).
    n_players = len(body.players)
    for q in body.per_hole_quarters:
        if not (0 <= q.player_index < n_players):
            raise HTTPException(status_code=400, detail=f"Invalid player_index {q.player_index}")
        if not (1 <= q.hole <= 18):
            raise HTTPException(status_code=400, detail=f"Invalid hole {q.hole} (must be 1-18)")

    # Assign stable ids; resolve profile from canonical legacy_name when absent.
    players: list[dict[str, Any]] = []
    profiles = (
        db.query(models.PlayerProfile).all()
        if any(p.player_profile_id is None and not p.unlinked for p in body.players)
        else []
    )
    for i, p in enumerate(body.players):
        name = " ".join(p.name.split())
        profile_id = p.player_profile_id
        if profile_id is None and not p.unlinked:
            matches = [
                prof
                for prof in profiles
                if any(
                    alias and " ".join(alias.casefold().split()) == name.casefold()
                    for alias in (prof.legacy_name, prof.name)
                )
            ]
            if len(matches) > 1:
                raise HTTPException(status_code=400, detail="Ambiguous player name; select a player profile")
            profile_id = matches[0].id if matches else None
        players.append(
            {
                "id": f"p{i + 1}",
                "name": name,
                "player_profile_id": profile_id,
                "handicap": 18.0,
            }
        )
    validate_round_players(players)

    per_hole = [q.model_dump() for q in body.per_hole_quarters]
    hole_history, standings = build_hole_history(players, per_hole)

    if not is_admin_profile(profile) and not any(p["player_profile_id"] == profile.id for p in players):
        raise HTTPException(status_code=403, detail="Only a participant or admin can post a round")
    validate_round_scores(players, hole_history)

    # Warn (do not reject) on holes whose deltas don't sum to zero.
    warnings: dict[str, float] = {}
    for entry in hole_history:
        s = sum(entry["points_delta"].values())
        if abs(s) > 0.001:
            warnings[str(entry["hole"])] = s

    try:
        now = utc_now().isoformat()
        game_id = str(uuid.uuid4())
        game = models.GameStateModel(
            game_id=game_id,
            game_status="completed",
            state={
                "game_status": "completed",
                "course_name": body.course_name or "Wing Point",
                "player_count": len(players),
                "players": players,
                "hole_history": hole_history,
                "hole_quarters": {str(e["hole"]): e["points_delta"] for e in hole_history},
                "standings": standings,
                "source": "scorecard_scan",
                "played_at": body.played_at or now[:10],
            },
            created_at=now,
            updated_at=now,
        )
        # Attach the photo for later per-hole backfill (best-effort; oversize ignored).
        if body.image_base64 and len(body.image_base64) <= 2_000_000:
            game.scorecard_image = body.image_base64
        db.add(game)
        db.flush()
        persist_completed_game(db, game)
        return {"game_id": game_id, "status": "completed", "warnings": warnings}
    except Exception as e:
        db.rollback()
        logger.error(f"from-scorecard failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record round: {e!s}")


class ScorecardBackfillRequest(BaseModel):
    per_hole_quarters: list[ScorecardRoundHoleQuarter]


@router.patch("/{game_id}/scorecard")
async def backfill_scorecard(
    game_id: str,
    body: ScorecardBackfillRequest,
    editor: models.PlayerProfile = Depends(require_round_member_or_admin),
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """Backfill the per-hole quarters of a scanned round and recompute standings.
    Standings come out as the sum of the submitted per-hole (settle-up identity)."""
    from ..services.completed_game_service import build_hole_history, persist_completed_game

    game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Round not found")
    state = dict(game.state or {})
    players = state.get("players", [])
    n = len(players)
    for q in body.per_hole_quarters:
        if not (0 <= q.player_index < n) or not (1 <= q.hole <= 18):
            raise HTTPException(status_code=400, detail="Invalid per_hole_quarters entry")

    per_hole = [q.model_dump() for q in body.per_hole_quarters]
    hole_history, standings = build_hole_history(players, per_hole)
    validate_round_scores(players, hole_history)
    state["hole_history"] = hole_history
    state["hole_quarters"] = {str(e["hole"]): e["points_delta"] for e in hole_history}
    state["standings"] = standings
    mark_card_edited(state, editor)
    game.state = state  # reassign top-level so MutableDict marks dirty
    game.updated_at = utc_now().isoformat()

    persist_completed_game(db, game)
    db.commit()
    return {"game_id": game_id, "standings": standings}


@router.get("/{game_id}/scorecard-photo")
async def get_scorecard_photo(game_id: str, db: Session = Depends(database.get_db)) -> Response:
    """Return the stored scorecard photo for a scanned round (for later per-hole backfill)."""
    game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()
    if not game or not game.scorecard_image:
        raise HTTPException(status_code=404, detail="No scorecard photo for this round")
    raw = game.scorecard_image
    media_type = "image/jpeg"
    if raw.startswith("data:"):
        header, _, b64 = raw.partition(",")
        media_type = header[5:].split(";", 1)[0] or media_type
    else:
        b64 = raw
    try:
        content = base64.b64decode(b64)
    except Exception:
        raise HTTPException(status_code=404, detail="Stored photo is unreadable")
    return Response(content=content, media_type=media_type)
