"""One-shot: move avatar blobs into GCS.

Migrates both:
  - ``avatar_image`` (base64 JPEG in Postgres)
  - ``avatar_url`` values that are ``data:image/...;base64,...`` (legacy inline blobs)

Leaves real external URLs (Auth0 Google pictures, static site paths) alone.

Usage:

    cd backend && source venv/bin/activate
    export MEDIA_BUCKET=wgp-media-seventh-country-232522
    export DATABASE_URL=...   # Cloud SQL proxy URL or Render URL
    python scripts/migrate_avatars_to_gcs.py

Idempotent: skips rows that already have a gcs: avatar_url marker.
"""

from __future__ import annotations

import base64
import logging
import os
import re
import sys

from sqlalchemy import or_
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal  # noqa: E402
from app.models import PlayerProfile  # noqa: E402
from app.services import media_storage_service  # noqa: E402
from app.utils.time import utc_now  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("migrate_avatars")

_DATA_URI_RE = re.compile(r"^data:(image/[\w+.-]+);base64,(.+)$", re.DOTALL | re.IGNORECASE)


def _jpeg_from_player(player: PlayerProfile) -> bytes | None:
    """Extract image bytes from avatar_image or a data: avatar_url."""
    if player.avatar_image:
        return base64.b64decode(player.avatar_image)

    url = player.avatar_url or ""
    match = _DATA_URI_RE.match(url)
    if not match:
        return None
    return base64.b64decode(match.group(2))


def migrate(db: Session) -> tuple[int, int, int]:
    if not media_storage_service.is_enabled():
        raise SystemExit("MEDIA_BUCKET is not set — refuse to migrate")

    rows = (
        db.query(PlayerProfile)
        .filter(
            or_(
                PlayerProfile.avatar_image.isnot(None),
                PlayerProfile.avatar_url.like("data:image/%"),
            )
        )
        .order_by(PlayerProfile.id.asc())
        .all()
    )
    # Filter empty avatar_image strings in Python (SQLAlchemy/SQLite/PG differ)
    rows = [
        p
        for p in rows
        if (p.avatar_image and str(p.avatar_image).strip())
        or (p.avatar_url or "").startswith("data:image/")
    ]

    migrated = skipped = failed = 0
    for player in rows:
        if media_storage_service.is_gcs_avatar_url(player.avatar_url):
            player.avatar_image = None
            player.updated_at = utc_now().isoformat()
            db.commit()
            skipped += 1
            continue

        try:
            jpeg = _jpeg_from_player(player)
            if not jpeg:
                logger.warning("No decodable image for id=%s (%s) — skip", player.id, player.name)
                skipped += 1
                continue

            path = media_storage_service.avatar_object_path(player.id)
            media_storage_service.upload_bytes(path, jpeg, content_type="image/jpeg")
            player.avatar_url = media_storage_service.avatar_gcs_marker(player.id)
            player.avatar_image = None
            player.updated_at = utc_now().isoformat()
            db.commit()
            migrated += 1
            logger.info("Migrated player id=%s (%s) → %s", player.id, player.name, path)
        except Exception:
            logger.exception("Failed player id=%s (%s)", player.id, player.name)
            failed += 1
            db.rollback()

    return migrated, skipped, failed


def main() -> None:
    db = SessionLocal()
    try:
        migrated, skipped, failed = migrate(db)
        logger.info("Done. migrated=%s skipped=%s failed=%s", migrated, skipped, failed)
        if failed:
            raise SystemExit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
