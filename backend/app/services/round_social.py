"""Persisted UUID ownership of the existing social rows, without read-time migration."""

import logging
from datetime import datetime
from urllib.parse import quote

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app import models
from app.services.round_identity import resolve_round_alias
from app.utils.time import utc_now

logger = logging.getLogger(__name__)


def alias_game(db, date, group, location):
    ids = resolve_round_alias(db, date, group, location)
    if len(ids) > 1:
        raise HTTPException(409, "Ambiguous round alias; choose a UUID before writing")
    return ids[0] if ids else None


def owned_rows(db, model, game_id):
    aliases = db.query(models.RoundAlias).filter_by(game_id=game_id).all()
    keys = []
    for alias in aliases:
        if resolve_round_alias(db, alias.date_key, alias.group, alias.location) == [game_id]:
            keys.append(
                and_(
                    model.round_date == alias.date_key,
                    model.round_group == alias.group,
                    model.location == alias.location,
                    model.game_id.is_(None),
                )
            )
    return db.query(model).filter(or_(model.game_id == game_id, *keys))


def require_game(db, game_id):
    game = db.query(models.GameStateModel).filter_by(game_id=game_id).one_or_none()
    if not game:
        raise HTTPException(404, "Round unavailable")
    return game


def comment_game(db, comment):
    return getattr(comment, "game_id", None) or alias_game(
        db, comment.round_date, comment.round_group, comment.location
    )


def _notify_site_of_comment(
    comment: models.RoundComment,
    shown_date: str,
    author: models.PlayerProfile,
    db: Session,
) -> None:
    """Ping every other signed-in player. The social feed is the whole site, not the foursome.

    In-app only. AI and inactive profiles have nobody watching the bell.
    A failed fan-out must not reject a comment that already landed.
    """
    nested = db.begin_nested()
    try:
        watchers = (
            db.query(models.PlayerProfile.id)
            .filter(
                models.PlayerProfile.is_active == 1,
                models.PlayerProfile.is_ai == 0,
                models.PlayerProfile.id != author.id,
            )
            .all()
        )
        where = shown_date or comment.round_date
        if comment.location:
            where = f"{where} at {comment.location}"
        author_name = author.name or "Someone"
        snippet = comment.body if len(comment.body) <= 80 else f"{comment.body[:77]}..."
        message = f"{author_name} on {where}: {snippet}"
        query = f"?location={quote(comment.location)}" if comment.location else ""
        path = (
            f"/game/{quote(comment.game_id)}"
            if comment.game_id
            else f"/rounds/{quote(comment.round_date)}/{quote(comment.round_group)}{query}"
        )
        created_at = utc_now().isoformat()
        db.add_all(
            [
                models.Notification(
                    player_profile_id=watcher_id,
                    notification_type="round_comment",
                    message=message,
                    data={
                        "path": path,
                        "round_date": comment.round_date,
                        "round_group": comment.round_group,
                        "location": comment.location,
                    },
                    is_read=False,
                    created_at=created_at,
                )
                for (watcher_id,) in watchers
            ]
        )
        nested.commit()
    except Exception:
        # The comment itself still commits. A missed bell is better than a 500.
        nested.rollback()
        logger.exception("Failed to notify players of a round comment")


def _display_dates(dt: datetime) -> set[str]:
    """Sheet dates are "6-Oct" or "06-Oct". Don't use %-d; glibc-only."""
    padded = dt.strftime("%d-%b")
    return {padded, padded.lstrip("0")}


def _date_keys(date: str) -> set[str]:
    """Accept YYYY-MM-DD and the sheet display form (6-Oct or 06-Oct).

    Shared links from the first deploy used the display date. The year isn't
    on the sheet, so a display date matches any season round on that day.
    """
    keys = {date}
    try:
        keys.update(_display_dates(datetime.strptime(date, "%Y-%m-%d")))
        return keys
    except ValueError:
        pass
    # Year is a dummy; only the day and month are added to the key set.
    try:
        keys.update(_display_dates(datetime.strptime(f"{date}-2000", "%d-%b-%Y")))
    except ValueError:
        pass
    return keys
