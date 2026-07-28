"""ForeTees Member_sheet HTML parser."""

from __future__ import annotations

import html
import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


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
