"""Cloud Storage helpers for avatars (and future media).

When ``MEDIA_BUCKET`` is unset (local/dev/tests), callers should fall back to
DB-backed ``avatar_image`` storage. The bucket is private; images are served
through ``GET /players/{id}/avatar``, not public object URLs.

``avatar_url`` values of the form ``gcs:avatars/{id}.jpg`` mark a GCS-backed
upload so ``has_avatar_image`` stays true without keeping the blob in Postgres.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)

GCS_AVATAR_PREFIX = "gcs:"
AVATAR_OBJECT_TEMPLATE = "avatars/{player_id}.jpg"


def media_bucket() -> str:
    return (os.getenv("MEDIA_BUCKET") or "").strip()


def is_enabled() -> bool:
    return bool(media_bucket())


def avatar_object_path(player_id: int) -> str:
    return AVATAR_OBJECT_TEMPLATE.format(player_id=player_id)


def avatar_gcs_marker(player_id: int) -> str:
    return f"{GCS_AVATAR_PREFIX}{avatar_object_path(player_id)}"


def is_gcs_avatar_url(url: str | None) -> bool:
    return bool(url and url.startswith(GCS_AVATAR_PREFIX))


def gcs_path_from_marker(url: str) -> str:
    return url[len(GCS_AVATAR_PREFIX) :]


@lru_cache(maxsize=1)
def _client():
    from google.cloud import storage

    return storage.Client()


def upload_bytes(object_path: str, data: bytes, content_type: str = "application/octet-stream") -> None:
    bucket_name = media_bucket()
    if not bucket_name:
        raise RuntimeError("MEDIA_BUCKET is not configured")
    blob = _client().bucket(bucket_name).blob(object_path)
    blob.upload_from_string(data, content_type=content_type)
    logger.info("Uploaded gs://%s/%s (%d bytes)", bucket_name, object_path, len(data))


def download_bytes(object_path: str) -> bytes | None:
    bucket_name = media_bucket()
    if not bucket_name:
        return None
    blob = _client().bucket(bucket_name).blob(object_path)
    if not blob.exists():
        return None
    return blob.download_as_bytes()


def delete_object(object_path: str) -> None:
    bucket_name = media_bucket()
    if not bucket_name:
        return
    blob = _client().bucket(bucket_name).blob(object_path)
    if blob.exists():
        blob.delete()
        logger.info("Deleted gs://%s/%s", bucket_name, object_path)
