"""A finished round's paper card: attach the photo, and report who may edit it."""

import base64
import logging
from io import BytesIO
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, ImageOps
from sqlalchemy.orm import Session

from .. import database, models
from ..services.auth_service import get_current_user
from ..utils.round_card import can_edit_round, mark_card_edited, require_round_member_or_admin
from ..utils.time import utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])

CARD_MAX_UPLOAD_BYTES = 20 * 1024 * 1024
CARD_MAX_DIM = 2000  # big enough to read handwriting, small enough to keep rows modest
CARD_MAX_PIXELS = 60_000_000  # ~3x a 20MP phone photo; bounds decode memory


def _downscale_card(image_bytes: bytes) -> str:
    img = Image.open(BytesIO(image_bytes))
    # Header-only so far: refuse pixel bombs before decoding allocates memory.
    if img.width * img.height > CARD_MAX_PIXELS:
        raise ValueError(f"image too large: {img.width}x{img.height}")
    img.draft("RGB", (CARD_MAX_DIM, CARD_MAX_DIM))  # JPEG: decode at reduced scale
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((CARD_MAX_DIM, CARD_MAX_DIM), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


@router.put("/{game_id}/scorecard-photo")
def put_scorecard_photo(
    game_id: str,
    file: UploadFile = File(...),
    editor: models.PlayerProfile = Depends(require_round_member_or_admin),
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """Attach or replace the round's card photo. Numbers are untouched."""
    image_bytes = file.file.read()
    if len(image_bytes) > CARD_MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Photo too large. Maximum size is 20MB.")
    try:
        image = _downscale_card(image_bytes)
    except Exception as e:
        logger.warning("Unreadable card photo for %s", game_id, exc_info=True)
        raise HTTPException(status_code=400, detail="Could not read that file as a photo") from e

    game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Round not found")
    state = dict(game.state or {})
    mark_card_edited(state, editor)
    game.scorecard_image = image
    game.state = state  # reassign top-level so MutableDict marks dirty
    game.updated_at = utc_now().isoformat()
    db.commit()
    return {"game_id": game_id, "card_edited_by": state["card_edited_by"], "card_edited_at": state["card_edited_at"]}


@router.get("/{game_id}/card")
def get_card(
    game_id: str,
    profile: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """What the signed-in viewer may do with this round's card, and its last edit."""
    game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Round not found")
    state = game.state or {}
    return {
        "has_photo": bool(game.scorecard_image),
        "can_edit": can_edit_round(db, game, profile),
        "edited_by": state.get("card_edited_by"),
        "edited_at": state.get("card_edited_at"),
    }
