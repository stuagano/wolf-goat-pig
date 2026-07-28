"""ForeTees Member_sheet HTML parser."""

from __future__ import annotations

import html
import json
import logging
import re
from datetime import datetime
from typing import Any
from urllib.parse import quote

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class ForeteesAuthError(Exception):
    """Raised when Wing Point or ForeTees authentication fails."""


class ForeteesSheetError(Exception):
    """Raised when the ForeTees Member_sheet request fails."""


def _build_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _validate_sheet_date(date: str) -> str:
    dt = datetime.strptime(date, "%Y-%m-%d")
    return dt.strftime("%m/%d/%Y")


async def fetch_tee_times(
    username: str,
    password: str,
    date: str,
    *,
    settings: Settings | None = None,
) -> list[dict[str, Any]]:
    """Fetch and parse a member tee sheet through the Wing Point ForeTees SSO flow."""
    ft_date = _validate_sheet_date(date)
    resolved_settings = settings or get_settings()

    login_url = _build_url(resolved_settings.wingpoint_base, resolved_settings.login_page)
    tee_time_url = _build_url(resolved_settings.wingpoint_base, resolved_settings.tee_time_page)
    foretees_base = resolved_settings.foretees_base.rstrip("/")

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        try:
            login_resp = await client.get(login_url)
            login_resp.raise_for_status()

            login_post_resp = await client.post(
                login_url,
                data={
                    "UserLOGIN": username,
                    "UserPWD": password,
                    "btnLogon": "Log On",
                    "Action": "Authenticate",
                    "DocID": "465",
                    "LogonRequest": "",
                    "R": "0",
                },
                headers={"Referer": login_url},
            )
            login_post_resp.raise_for_status()

            tee_page_resp = await client.get(tee_time_url)
            tee_page_resp.raise_for_status()
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            raise ForeteesAuthError("ForeTees authentication request failed") from exc

        sso_key_match = re.search(r"ftSSOKey\s*=\s*'([^']+)'", tee_page_resp.text)
        sso_iv_match = re.search(r"ftSSOIV\s*=\s*'([^']+)'", tee_page_resp.text)
        if not sso_key_match or not sso_iv_match:
            raise ForeteesAuthError("ForeTees SSO parameters were not found")

        sso_key = sso_key_match.group(1)
        sso_iv = sso_iv_match.group(1)
        try:
            sso_url = f"{foretees_base}/Member_select?sso_uid={quote(sso_key)}&sso_iv={quote(sso_iv)}"
            sso_resp = await client.get(sso_url)
            sso_resp.raise_for_status()
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            raise ForeteesAuthError("ForeTees SSO request failed") from exc

        try:
            sheet_resp = await client.get(
                f"{foretees_base}/Member_sheet",
                params={"calDate": ft_date, "course": "", "displayOpt": "0"},
            )
            sheet_resp.raise_for_status()
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            raise ForeteesSheetError("ForeTees sheet request failed") from exc

    return parse_tee_sheet(sheet_resp.text, date)


def parse_tee_sheet(html_content: str, date: str) -> list[dict[str, Any]]:
    """Parse the Member_sheet HTML to extract tee time data.

    The key data lives in data-ftjson attributes on time slot links:
    <a class="teetime_button" data-ftjson="{...}">11:00 AM</a>

    Player transport modes are in sibling divs:
    <div><span>Player Name</span><span>PC</span></div>
    """
    slots: list[dict[str, Any]] = []

    pattern = re.compile(r'data-ftjson="([^"]+)"')
    matches = pattern.findall(html_content)

    row_pattern = re.compile(
        r'<div\s+class="rwdTr[^"]*">(.*?)</div>\s*(?=<div\s+class="rwdTr|$)',
        re.DOTALL,
    )
    rows = row_pattern.findall(html_content)

    transport_map: dict[int, list[str]] = {}
    player_transport_pattern = re.compile(
        r'class="rwdTd pgCol">\s*<div>\s*<span>([^<]+)</span>\s*<span>([^<]*)</span>',
    )

    for row_html in rows:
        ftjson_match = pattern.search(row_html)
        if not ftjson_match:
            continue
        try:
            row_data = json.loads(html.unescape(ftjson_match.group(1)))
            jump = row_data.get("jump", 0)
        except (json.JSONDecodeError, ValueError):
            continue

        transports = []
        for _name, mode in player_transport_pattern.findall(row_html):
            transports.append(mode.strip())
        transport_map[jump] = transports

    open_slots_pattern = re.compile(
        r'class="slotCount[^"]*openSlots(\d+)\s+maxPlayers(\d+)"',
    )
    open_slots_map: dict[int, dict[str, int]] = {}
    for row_html in rows:
        ftjson_match = pattern.search(row_html)
        if not ftjson_match:
            continue
        try:
            row_data = json.loads(html.unescape(ftjson_match.group(1)))
            jump = row_data.get("jump", 0)
        except (json.JSONDecodeError, ValueError):
            continue

        slots_match = open_slots_pattern.search(row_html)
        if slots_match:
            open_slots_map[jump] = {
                "open_slots": int(slots_match.group(1)),
                "max_players": int(slots_match.group(2)),
            }

    for raw_json in matches:
        try:
            data = json.loads(html.unescape(raw_json))
        except (json.JSONDecodeError, ValueError):
            continue

        if data.get("type") != "Member_slot":
            continue

        players = []
        for i in range(1, 6):
            name = data.get(f"wasP{i}", "")
            if name:
                transport = ""
                jump = data.get("jump", 0)
                transports = transport_map.get(jump, [])
                if i - 1 < len(transports):
                    transport = transports[i - 1]
                players.append({"name": name, "transport": transport})

        slot_info = open_slots_map.get(data.get("jump", 0), {})
        max_players = slot_info.get("max_players", 4)
        open_count = max_players - len(players)

        slots.append(
            {
                "date": date,
                "time": data.get("time:0", ""),
                "front_back": "F",
                "players": players,
                "open_slots": open_count,
                "max_players": max_players,
                "ttdata": data.get("ttdata", ""),
                "jump": data.get("jump", 0),
                "p5_allowed": data.get("p5", "No") == "Yes",
            }
        )

    logger.info("Parsed %d tee time slots for %s", len(slots), date)
    return slots
