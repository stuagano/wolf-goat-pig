"""GroupMe bridge — the league chats in GroupMe; the app is a window into it.

Read side uses the GroupMe v3 REST API with a personal access token
(GROUPME_ACCESS_TOKEN). Write side posts through a GroupMe bot
(GROUPME_BOT_ID) so web messages appear in everyone's GroupMe app.

Setup (one-time):
1. dev.groupme.com → log in → copy Access Token → Render env GROUPME_ACCESS_TOKEN
2. GET /groupme/groups (admin) to find the group → Render env GROUPME_GROUP_ID
3. dev.groupme.com/bots → create bot in that group → Render env GROUPME_BOT_ID

All functions degrade gracefully when unconfigured.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

GROUPME_API = "https://api.groupme.com/v3"

# Cache: messages refresh at most every 20 seconds
_cache: dict[str, Any] = {}
_cache_ts: float = 0.0
_CACHE_TTL = 20


def _token() -> str | None:
    return os.environ.get("GROUPME_ACCESS_TOKEN") or None


def _group_id() -> str | None:
    return os.environ.get("GROUPME_GROUP_ID") or None


def _bot_id() -> str | None:
    return os.environ.get("GROUPME_BOT_ID") or None


def is_configured() -> dict[str, bool]:
    read = bool(_token() and _group_id())
    return {
        "read": read,
        # Posting works via bot (preferred) OR as the token owner's account
        # (fallback when the league group's admin hasn't created a bot).
        "post": bool(_bot_id()) or read,
    }


def _api_get(path: str, params: dict[str, Any] | None = None) -> Any:
    token = _token()
    if not token:
        raise RuntimeError("GROUPME_ACCESS_TOKEN not configured")
    qs = dict(params or {})
    qs["token"] = token
    url = f"{GROUPME_API}{path}?{urllib.parse.urlencode(qs)}"
    req = urllib.request.Request(url, headers={"User-Agent": "wolf-goat-pig/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8")).get("response")


def list_groups() -> list[dict[str, Any]]:
    """List the token owner's groups (admin/setup helper)."""
    groups = _api_get("/groups", {"per_page": 50}) or []
    return [{"id": g.get("id"), "name": g.get("name"), "members": len(g.get("members", []))} for g in groups]


_VIDEO_URL_RE = re.compile(r"https://\S*groupme\.com/\S+\.mp4\S*", re.IGNORECASE)


def _normalize_message(m: dict[str, Any]) -> dict[str, Any]:
    """GroupMe message -> compact app shape (only the fields the UI needs)."""
    attachments = m.get("attachments", [])
    images = [a.get("url") for a in attachments if a.get("type") == "image" and a.get("url")]
    videos = [
        {"url": a.get("url"), "preview_url": a.get("preview_url")}
        for a in attachments
        if a.get("type") == "video" and a.get("url")
    ]

    # GroupMe often puts video uploads as a bare .mp4 link in the text
    text = m.get("text")
    if text:
        for url in _VIDEO_URL_RE.findall(text):
            if not any(v["url"] == url for v in videos):
                videos.append({"url": url, "preview_url": None})
        # If the text is ONLY the video link(s), don't show it as text too
        stripped = _VIDEO_URL_RE.sub("", text).strip()
        if videos and not stripped:
            text = None

    created = m.get("created_at")
    created_iso = datetime.fromtimestamp(created, tz=UTC).isoformat() if created else None
    return {
        "id": m.get("id"),
        "name": m.get("name"),
        "text": text,
        "avatar_url": m.get("avatar_url"),
        "created_at": created_iso,
        "likes": len(m.get("favorited_by", [])),
        "images": images,
        "videos": videos,
        "is_system": m.get("system", False) or m.get("sender_type") == "system",
        "is_bot": m.get("sender_type") == "bot",
    }


def get_messages(limit: int = 50, force_refresh: bool = False, before_id: str | None = None) -> dict[str, Any]:
    """Group messages, oldest-first (ready for chat rendering).

    Head page (no before_id) is cached for 20 seconds — the page polls, and
    many viewers shouldn't multiply upstream calls. History pages
    (before_id set) walk backwards through the full archive and bypass the
    cache: each page is requested at most once per scroll-back.
    """
    global _cache, _cache_ts
    if not force_refresh and not before_id and _cache and (time.time() - _cache_ts) < _CACHE_TTL:
        return _cache

    group_id = _group_id()
    if not (_token() and group_id):
        return {"configured": False, "messages": []}

    params: dict[str, Any] = {"limit": min(limit, 100)}
    if before_id:
        params["before_id"] = before_id
    try:
        resp = _api_get(f"/groups/{group_id}/messages", params)
    except urllib.error.HTTPError as e:
        # 304 = no messages; anything else is a real error
        if e.code == 304:
            resp = {"messages": []}
        else:
            logger.error("GroupMe fetch failed: HTTP %s", e.code)
            # Serve stale cache rather than nothing
            return _cache or {"configured": True, "messages": [], "error": f"HTTP {e.code}"}
    except Exception as e:
        logger.error("GroupMe fetch failed: %s", e)
        return _cache or {"configured": True, "messages": [], "error": str(e)}

    raw = (resp or {}).get("messages", [])
    messages = [_normalize_message(m) for m in raw]
    messages.reverse()  # API returns newest-first; chat renders oldest-first

    result = {"configured": True, "messages": messages}
    if messages and not before_id:  # cache the head page only; never empties
        _cache = result
        _cache_ts = time.time()
    return result


def _prepare_body(text: str, author: str | None) -> str | None:
    body = text.strip()
    if not body:
        return None
    if author:
        body = f"{author}: {body}"
    if len(body) > 990:  # GroupMe hard limit is 1000 chars
        body = body[:987] + "..."
    return body


def _post_json(url: str, payload: dict[str, Any]) -> int:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "wolf-goat-pig/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status


def post_message(text: str, author: str | None = None) -> dict[str, Any]:
    """Post into the group. Returns {posted: bool, via: "bot"|"user"}.

    Preferred path is the bot (GROUPME_BOT_ID) — posts under the bot's
    name. Fallback: post as the token owner's own account via the group
    messages API (works without group-admin rights). Either way the web
    author's name is prefixed into the text ("Stuart: nice round sunday").
    """
    global _cache_ts

    body = _prepare_body(text, author)
    if body is None:
        return {"posted": False, "error": "Empty message"}

    bot_id = _bot_id()
    if bot_id:
        try:
            status = _post_json(f"{GROUPME_API}/bots/post", {"bot_id": bot_id, "text": body})
            if status in (200, 201, 202):
                _cache_ts = 0.0  # bust read cache so the message shows promptly
                return {"posted": True, "via": "bot"}
            logger.error("GroupMe bot post returned HTTP %s — trying user post", status)
        except Exception as e:
            logger.error("GroupMe bot post failed (%s) — trying user post", e)

    # Fallback: post as the access-token owner's account
    token, group_id = _token(), _group_id()
    if not (token and group_id):
        return {"posted": False, "error": "No bot configured and no token/group for user posting"}
    try:
        import uuid as _uuid

        url = f"{GROUPME_API}/groups/{group_id}/messages?{urllib.parse.urlencode({'token': token})}"
        status = _post_json(url, {"message": {"source_guid": str(_uuid.uuid4()), "text": body}})
    except Exception as e:
        logger.error("GroupMe user post failed: %s", e)
        return {"posted": False, "error": str(e)}
    if status not in (200, 201, 202):
        return {"posted": False, "error": f"HTTP {status}"}
    _cache_ts = 0.0
    return {"posted": True, "via": "user"}
