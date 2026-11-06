"""Avatar image helpers shared by the /players/me and /players/{player_id} routes."""

import base64
from io import BytesIO

from PIL import Image, ImageOps

from .. import models
from ..services import media_storage_service

AVATAR_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
AVATAR_MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8MB raw upload; we downscale server-side
AVATAR_MAX_DIM = 400


def _downscale_avatar_jpeg(image_bytes: bytes) -> bytes:
    """Resize to fit AVATAR_MAX_DIM, correct EXIF rotation, re-encode as JPEG bytes."""
    img = Image.open(BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    img.thumbnail((AVATAR_MAX_DIM, AVATAR_MAX_DIM), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _downscale_avatar(image_bytes: bytes) -> str:
    """Legacy helper: downscale and return base64 JPEG (DB blob fallback)."""
    return base64.b64encode(_downscale_avatar_jpeg(image_bytes)).decode("ascii")


def _avatar_jpeg_for_player(player: models.PlayerProfile) -> bytes | None:
    """Resolve uploaded avatar bytes from GCS, data: URL, or legacy DB blob."""
    if media_storage_service.is_gcs_avatar_url(player.avatar_url):
        path = media_storage_service.gcs_path_from_marker(player.avatar_url or "")
        return media_storage_service.download_bytes(path)
    url = player.avatar_url or ""
    if url.startswith("data:image/"):
        try:
            _header, b64 = url.split(",", 1)
            return base64.b64decode(b64)
        except Exception:
            return None
    if player.avatar_image:
        return base64.b64decode(player.avatar_image)
    return None
