"""Scanned-scorecard routes — record a round from a scorecard, backfill per-hole quarters, photo."""

import base64
import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, Field, field_validator
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
    quarters: float | None = Field(default=None, allow_inf_nan=False)


class ScorecardRoundHoleQuarter(BaseModel):
    player_index: int
    hole: int
    quarters: float


class ScorecardRoundRequest(BaseModel):
    players: list[ScorecardRoundPlayer]
    per_hole_quarters: list[ScorecardRoundHoleQuarter] = Field(default_factory=list)
    detail_coverage: str = "per_hole_complete"
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
    response: Response,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    profile: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """Record a completed round straight from a scanned scorecard.

    Builds a completed game (players + per-hole quarters) and persists the
    same GameRecord/GamePlayerResult rows a live-scored game would, so a
    scanned round shows up in standings/history identically.
    """
    import uuid

    from ..schemas.round_identity import RoundDraft
    from ..services.completed_game_service import build_hole_history, persist_completed_game
    from ..services.round_writes import create_observation, writer_mode

    mode = writer_mode(db)
    if body.detail_coverage not in {"totals_only", "per_hole_complete"}:
        raise HTTPException(400, "Declare totals_only or per_hole_complete coverage")
    if body.detail_coverage == "totals_only":
        if body.per_hole_quarters:
            raise HTTPException(400, "Totals-only input cannot contain holes")
        if any(player.quarters is None for player in body.players):
            raise HTTPException(400, "Totals-only input requires an explicit total for every player")
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
            }
        )
    validate_round_players(players)

    per_hole = [q.model_dump() for q in body.per_hole_quarters]
    hole_history, standings = build_hole_history(players, per_hole)

    if not is_admin_profile(profile) and not any(p["player_profile_id"] == profile.id for p in players):
        raise HTTPException(status_code=403, detail="Only a participant or admin can post a round")
    if body.detail_coverage == "per_hole_complete":
        validate_round_scores(players, hole_history)
    if body.detail_coverage == "totals_only" and mode != "canonical":
        raise HTTPException(409, "Totals-only scans require the coordinated canonical cutover")
    if mode == "canonical":
        draft = RoundDraft(
            played_on=date.fromisoformat(body.played_at) if body.played_at else None,
            course_name=body.course_name,
            roster_complete=True,
            detail_coverage=body.detail_coverage,
            players=[
                {
                    "participant_id": p["id"],
                    "name": p["name"],
                    "profile_id": p["player_profile_id"],
                    "quarters": body.players[i].quarters
                    if body.detail_coverage == "totals_only"
                    else standings[p["id"]],
                }
                for i, p in enumerate(players)
            ],
            hole_history=hole_history,
            actor_profile_id=profile.id,
        )
        receipt, result = create_observation(
            db, profile.id, idempotency_key, body.model_dump(mode="json"), draft, "scan"
        )
        if result["game_id"] is None:
            response.status_code = 202
        elif body.image_base64 and len(body.image_base64) <= 2_000_000:
            db.query(models.GameStateModel).filter_by(
                game_id=result["game_id"]
            ).one().scorecard_image = body.image_base64
        saved = dict(result)
        db.commit()
        return saved

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
                "course_name": body.course_name,
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
        db.commit()
        return {"game_id": game_id, "status": "completed", "warnings": warnings}
    except Exception as e:
        db.rollback()
        logger.error(f"from-scorecard failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record round: {e!s}")


class ScorecardBackfillRequest(BaseModel):
    per_hole_quarters: list[ScorecardRoundHoleQuarter]
    expected_revision: int | None = None


@router.patch("/{game_id}/scorecard")
async def backfill_scorecard(
    game_id: str,
    body: ScorecardBackfillRequest,
    editor: models.PlayerProfile = Depends(require_round_member_or_admin),
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """Backfill the per-hole quarters of a scanned round and recompute standings.
    Standings come out as the sum of the submitted per-hole (settle-up identity)."""
    from ..services.completed_game_service import build_hole_history, merge_hole_history, persist_completed_game
    from ..services.round_writes import check_revision, propose_completed, writer_mode

    mode = writer_mode(db)
    game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).populate_existing().first()
    if not game:
        raise HTTPException(status_code=404, detail="Round not found")
    check_revision(db, game, body.expected_revision, required=mode == "canonical")
    state = dict(game.state or {})
    players = state.get("players", [])
    n = len(players)
    for q in body.per_hole_quarters:
        if not (0 <= q.player_index < n) or not (1 <= q.hole <= 18):
            raise HTTPException(status_code=400, detail="Invalid per_hole_quarters entry")

    per_hole = [q.model_dump() for q in body.per_hole_quarters]
    hole_history, standings = build_hole_history(players, per_hole)
    if mode == "canonical" and game.game_status == "completed":
        from ..services.round_writes import completed_detail_players

        detail_players = completed_detail_players(db, game)
    else:
        detail_players = players
    validate_round_scores(detail_players, hole_history, complete=False)
    history = merge_hole_history(state.get("hole_history", []), hole_history)
    if mode == "canonical" and game.game_status == "completed":
        detail = propose_completed(db, game, history, editor.id)
        db.commit()
        if detail["issue_ids"]:
            raise HTTPException(409, detail)
        return {"game_id": game_id, "revision": detail["revision"], "status": "unchanged", "issue_ids": []}
    state["hole_history"] = history
    state["hole_quarters"] = {str(e["hole"]): e["points_delta"] for e in hole_history}
    state["standings"] = standings
    mark_card_edited(state, editor)
    game.state = state  # reassign top-level so MutableDict marks dirty
    game.updated_at = utc_now().isoformat()

    persist_completed_game(db, game)
    standings = dict(game.state["standings"])
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
