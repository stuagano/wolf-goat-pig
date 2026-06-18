"""League media archive — harvest videos/images from the GroupMe group.

Chat scrolls on; clips shouldn't get lost. The harvester walks the group's
message history (head page + before_id pagination) and upserts every video
and image into livsow_media, keyed by GroupMe message id (idempotent — safe
to run repeatedly from cron or on demand).

Bytes stay on GroupMe's CDN. `archived_url` is reserved for a future
object-storage copy step.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from .. import models
from ..utils.time import utc_now
from .groupme_service import get_messages

logger = logging.getLogger(__name__)

MAX_HARVEST_PAGES = 50  # 50 pages x 100 msgs — bounded full-history sweep
PAGE_LIMIT = 100


def _media_rows_from_message(m: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for i, v in enumerate(m.get("videos", [])):
        rows.append(
            {
                # One message can carry several media items — suffix keeps ids unique
                "groupme_message_id": f"{m['id']}:v{i}",
                "kind": "video",
                "url": v["url"],
                "preview_url": v.get("preview_url"),
            }
        )
    for i, url in enumerate(m.get("images", [])):
        rows.append(
            {
                "groupme_message_id": f"{m['id']}:i{i}",
                "kind": "image",
                "url": url,
                "preview_url": url,
            }
        )
    return rows


def harvest_media(db: Session, max_pages: int = MAX_HARVEST_PAGES) -> dict[str, Any]:
    """Walk chat history and upsert all media. Returns counts.

    Stops early when a full page contains nothing new AND we've already
    harvested before (incremental mode); a first run sweeps to history start
    or the page cap.
    """
    have_any = db.query(models.LivSowMedia.id).first() is not None
    now = utc_now().isoformat()
    seen_pages = 0
    inserted = 0
    updated = 0
    before_id: str | None = None

    while seen_pages < max_pages:
        data = get_messages(limit=PAGE_LIMIT, before_id=before_id, force_refresh=before_id is None)
        if data.get("configured") is False:
            return {"status": "skipped", "reason": "not_configured"}
        messages = data.get("messages", [])
        if not messages:
            break  # reached history start
        seen_pages += 1
        page_new = 0

        for m in messages:
            for row in _media_rows_from_message(m):
                existing = (
                    db.query(models.LivSowMedia)
                    .filter(models.LivSowMedia.groupme_message_id == row["groupme_message_id"])
                    .first()
                )
                if existing:
                    # refresh like counts/caption (they change over time)
                    existing.likes = m.get("likes", 0)
                    existing.caption = m.get("text")
                    updated += 1
                    continue
                db.add(
                    models.LivSowMedia(
                        groupme_message_id=row["groupme_message_id"],
                        kind=row["kind"],
                        url=row["url"],
                        preview_url=row["preview_url"],
                        author=m.get("name"),
                        caption=m.get("text"),
                        posted_at=m.get("created_at"),
                        harvested_at=now,
                        likes=m.get("likes", 0),
                        featured=False,
                        deleted=False,
                    )
                )
                inserted += 1
                page_new += 1

        db.commit()
        # messages are oldest-first; the OLDEST id on this page pages backwards
        before_id = messages[0]["id"]
        if have_any and page_new == 0 and seen_pages > 1:
            break  # incremental run hit already-harvested territory

    return {"status": "ok", "pages": seen_pages, "inserted": inserted, "updated": updated}


def list_media(db: Session, kind: str | None = "video", limit: int = 100, offset: int = 0) -> dict[str, Any]:
    q = db.query(models.LivSowMedia).filter(models.LivSowMedia.deleted.is_(False))
    if kind:
        q = q.filter(models.LivSowMedia.kind == kind)
    total = q.count()
    rows = q.order_by(models.LivSowMedia.posted_at.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "media": [
            {
                "id": r.id,
                "kind": r.kind,
                "url": r.archived_url or r.url,
                "preview_url": r.preview_url,
                "author": r.author,
                "caption": r.caption,
                "posted_at": r.posted_at,
                "likes": r.likes,
                "featured": r.featured,
            }
            for r in rows
        ],
    }
