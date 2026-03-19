"""ForeTees integration service for Wing Point Golf & Country Club.

Reverse-engineered from the ForeTees v5 web app at ftapp.wingpointgolf.com.
Provides tee time browsing and booking via HTML scraping of the Member_sheet
endpoint, which embeds structured JSON in data-ftjson attributes.

Authentication flow:
1. POST login to wingpointgolf.com → session cookies
2. GET tee time page → extract ftSSOKey/ftSSOIV from inline JS
3. GET ForeTees Member_select with SSO params → JSESSIONID cookie
4. Use JSESSIONID for all ForeTees API requests

All configuration via environment variables. Best-effort, non-blocking.
"""

from __future__ import annotations

import html
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

# ForeTees base URL and endpoints
FORETEES_APP_BASE = "https://ftapp.wingpointgolf.com/v5/wingpointgcc_flxrez0_m30"
WINGPOINT_BASE = "https://www.wingpointgolf.com"
TEE_TIME_PAGE = "/members/golf/make-a-tee-time-703.html"
LOGIN_PAGE = "/public/member-login-465.html"

# Session expiry (re-auth after 15 minutes)
SESSION_TTL_SECONDS = 900


@dataclass(frozen=True)
class ForeteesConfig:
    enabled: bool = False
    username: str = ""
    password: str = ""
    base_url: str = FORETEES_APP_BASE
    timeout_seconds: float = 15.0

    @classmethod
    def from_env(cls) -> ForeteesConfig:
        return cls(
            enabled=os.getenv("FORETEES_ENABLED", "false").strip().lower() in {"1", "true", "yes"},
            username=os.getenv("FORETEES_USERNAME", ""),
            password=os.getenv("FORETEES_PASSWORD", ""),
            base_url=os.getenv("FORETEES_BASE_URL", FORETEES_APP_BASE),
            timeout_seconds=float(os.getenv("FORETEES_TIMEOUT_SECONDS", "15")),
        )


class ForeteesService:
    """Client for the ForeTees tee time system at Wing Point Golf."""

    def __init__(self, config: ForeteesConfig) -> None:
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._last_auth_time: float = 0

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            # Use a fresh CookieJar that tolerates duplicate cookie names
            # (wingpointgolf.com can set multiple UID cookies for different paths)
            jar = httpx.Cookies()
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout_seconds,
                follow_redirects=True,
                cookies=jar,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/146.0.0.0 Safari/537.36"
                    ),
                },
            )
        return self._client

    def _session_valid(self) -> bool:
        if self._last_auth_time == 0:
            return False
        return (time.time() - self._last_auth_time) < SESSION_TTL_SECONDS

    async def _ensure_session(self) -> bool:
        """Authenticate and establish a ForeTees session. Returns True on success."""
        if self._session_valid():
            return True

        if not self.config.enabled:
            logger.debug("ForeTees integration disabled")
            return False

        if not self.config.username or not self.config.password:
            logger.warning("ForeTees credentials not configured")
            return False

        client = await self._get_client()

        try:
            # Step 1: Login to wingpointgolf.com
            login_url = f"{WINGPOINT_BASE}{LOGIN_PAGE}"
            login_resp = await client.get(login_url)
            login_resp.raise_for_status()

            # The login form POSTs back to the login page itself
            login_data = {
                "UserLOGIN": self.config.username,
                "UserPWD": self.config.password,
                "btnLogon": "Log On",
                "Action": "Authenticate",
                "DocID": "465",
                "LogonRequest": "",
                "R": "0",
            }
            login_post_resp = await client.post(
                login_url,
                data=login_data,
                headers={"Referer": login_url},
            )
            login_post_resp.raise_for_status()

            # Step 2: Get the tee time page and extract SSO parameters
            # The iframe src is empty; JS constructs the URL from inline variables.
            tee_page_resp = await client.get(f"{WINGPOINT_BASE}{TEE_TIME_PAGE}")
            tee_page_resp.raise_for_status()

            sso_key_match = re.search(r"ftSSOKey\s*=\s*'([^']+)'", tee_page_resp.text)
            sso_iv_match = re.search(r"ftSSOIV\s*=\s*'([^']+)'", tee_page_resp.text)

            if not sso_key_match or not sso_iv_match:
                logger.error("Could not find ftSSOKey/ftSSOIV in tee time page")
                return False

            sso_key = sso_key_match.group(1)
            sso_iv = sso_iv_match.group(1)

            # Step 3: Hit ForeTees SSO endpoint to establish JSESSIONID
            sso_url = (
                f"{self.config.base_url}/Member_select"
                f"?sso_uid={quote(sso_key)}&sso_iv={quote(sso_iv)}"
            )
            sso_resp = await client.get(sso_url)
            sso_resp.raise_for_status()

            # Verify we got a JSESSIONID cookie
            try:
                has_session = any(
                    "JSESSIONID" in str(cookie.name)
                    for cookie in client.cookies.jar
                )
                if not has_session:
                    logger.warning("No JSESSIONID cookie received from ForeTees SSO")
                    # Continue anyway - the session might still work
            except httpx.CookieConflict:
                # Multiple cookies with same name on different paths - session likely fine
                logger.debug("CookieConflict checking JSESSIONID, continuing")

            self._last_auth_time = time.time()
            logger.info("ForeTees session established successfully")
            return True

        except httpx.HTTPStatusError as exc:
            logger.warning(
                "ForeTees auth failed with HTTP %s: %s",
                exc.response.status_code,
                exc.response.text[:200],
            )
        except httpx.RequestError as exc:
            logger.warning("ForeTees auth request failed: %s", exc)
        except Exception as exc:
            logger.error("Unexpected error during ForeTees auth: %s", exc)

        return False

    async def get_tee_times(self, date: str) -> List[Dict[str, Any]]:
        """Get tee times for a given date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            List of tee time slot dicts with time, players, open_slots, etc.
        """
        if not await self._ensure_session():
            return []

        client = await self._get_client()

        try:
            # Convert YYYY-MM-DD to MM/DD/YYYY for ForeTees
            dt = datetime.strptime(date, "%Y-%m-%d")
            ft_date = dt.strftime("%m/%d/%Y")

            sheet_url = f"{self.config.base_url}/Member_sheet"
            resp = await client.get(
                sheet_url,
                params={
                    "calDate": ft_date,
                    "course": "",
                    "displayOpt": "0",
                },
            )
            resp.raise_for_status()

            return self._parse_tee_sheet(resp.text, date)

        except httpx.HTTPStatusError as exc:
            logger.warning(
                "ForeTees tee sheet request failed HTTP %s",
                exc.response.status_code,
            )
            # Session may have expired - force re-auth next time
            self._last_auth_time = 0
        except httpx.RequestError as exc:
            logger.warning("ForeTees tee sheet request failed: %s", exc)
        except Exception as exc:
            logger.error("Error fetching ForeTees tee times: %s", exc)

        return []

    async def get_my_tee_times(self) -> List[Dict[str, Any]]:
        """Get the current member's upcoming tee times."""
        if not await self._ensure_session():
            return []

        client = await self._get_client()

        try:
            resp = await client.get(f"{self.config.base_url}/Member_teelist_list")
            resp.raise_for_status()
            return self._parse_my_tee_times(resp.text)
        except Exception as exc:
            logger.warning("Error fetching my ForeTees tee times: %s", exc)
            self._last_auth_time = 0
            return []

    async def book_tee_time(
        self, ttdata: str, transport_mode: str = "WLK"
    ) -> Dict[str, Any]:
        """Book the logged-in member into a tee time slot.

        Two-step flow:
        1. GET Member_slot?ttdata=... to load the booking form with hidden tokens
        2. POST Member_slot with form data to submit the booking

        Args:
            ttdata: Encrypted slot identifier from the tee sheet data-ftjson.
            transport_mode: One of WLK, CRT, PC.

        Returns:
            Dict with success, title, and messages keys.
        """
        if not await self._ensure_session():
            return {"success": False, "message": "Could not establish ForeTees session"}

        client = await self._get_client()

        try:
            # Step 1: Load the slot booking form
            slot_url = f"{self.config.base_url}/Member_slot"
            form_resp = await client.get(slot_url, params={"ttdata": ttdata})
            form_resp.raise_for_status()

            fields = self._parse_slot_form(form_resp.text)

            teecurr_id = fields.get("teecurr_id1", "")
            id_hash = fields.get("id_hash", "")
            if not teecurr_id or not id_hash:
                logger.warning("Missing required booking form fields: teecurr_id1=%s, id_hash=%s", bool(teecurr_id), bool(id_hash))
                return {"success": False, "message": "Could not load booking form"}

            # Build form data preserving all pre-populated players
            form_data: Dict[str, str] = {
                "teecurr_id1": teecurr_id,
                "id_hash": id_hash,
                "hide": "0",
                "notes": "",
                "submitForm": "submit",
                "slot_submit_action": "update",
                "json_mode": "true",
                "looking_for_players": "0",
                "show_remove_orig": "true",
                "remove_originator": "0",
            }

            for i in range(1, 6):
                form_data[f"player{i}"] = fields.get(f"player{i}", "")
                form_data[f"member_id{i}"] = fields.get(f"member_id{i}", "0")
                form_data[f"user{i}"] = fields.get(f"user{i}", "")
                form_data[f"player_type_a{i}"] = fields.get(f"player_type_a{i}", "")
                form_data[f"guest_id{i}"] = fields.get(f"guest_id{i}", "0")
                form_data[f"p9{i}"] = fields.get(f"p9{i}", "0")

                # Set transport mode for populated players, preserve existing
                existing_transport = fields.get(f"p{i}cw", "")
                if form_data[f"player{i}"] and not existing_transport:
                    form_data[f"p{i}cw"] = transport_mode
                else:
                    form_data[f"p{i}cw"] = existing_transport

            # Step 2: Submit the booking
            submit_resp = await client.post(
                slot_url,
                data=form_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                },
            )
            submit_resp.raise_for_status()

            result = submit_resp.json()
            success = result.get("successful", False)

            # ForeTees spreads messages across three lists
            messages = (
                result.get("message_list", [])
                + result.get("notice_list", [])
                + result.get("warning_list", [])
            )
            title = result.get("title", "")

            if success:
                logger.info("ForeTees booking successful: %s", title)
            else:
                logger.warning("ForeTees booking rejected: %s %s", title, messages)

            return {"success": success, "title": title, "messages": messages}

        except httpx.HTTPStatusError as exc:
            logger.warning("ForeTees booking failed HTTP %s", exc.response.status_code)
            self._last_auth_time = 0
        except httpx.RequestError as exc:
            logger.warning("ForeTees booking request failed: %s", exc)
            self._last_auth_time = 0
        except Exception as exc:
            logger.error("Error booking ForeTees tee time: %s", exc)

        return {"success": False, "message": "Booking request failed"}

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # HTML Parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_slot_form(html_content: str) -> Dict[str, str]:
        """Parse Member_slot HTML to extract hidden and visible form field values."""
        fields: Dict[str, str] = {}
        pattern = re.compile(
            r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"',
            re.IGNORECASE,
        )
        for name, value in pattern.findall(html_content):
            fields[name] = html.unescape(value)

        # Also extract select/combobox values (transport modes)
        select_pattern = re.compile(
            r'name="(p\dcw)"[^>]*>.*?<option[^>]*selected[^>]*value="([^"]*)"',
            re.IGNORECASE | re.DOTALL,
        )
        for name, value in select_pattern.findall(html_content):
            fields[name] = html.unescape(value)

        return fields

    @staticmethod
    def _parse_tee_sheet(html_content: str, date: str) -> List[Dict[str, Any]]:
        """Parse the Member_sheet HTML to extract tee time data.

        The key data lives in data-ftjson attributes on time slot links:
        <a class="teetime_button" data-ftjson="{...}">11:00 AM</a>

        Player transport modes are in sibling divs:
        <div><span>Player Name</span><span>PC</span></div>
        """
        slots: List[Dict[str, Any]] = []

        # Extract all data-ftjson attributes
        pattern = re.compile(r'data-ftjson="([^"]+)"')
        matches = pattern.findall(html_content)

        # Also extract player transport modes from the row HTML
        # Each row: <div class="rwdTr">...<div class="pgCol"><div><span>Name</span><span>Mode</span></div></div>...
        row_pattern = re.compile(
            r'<div\s+class="rwdTr[^"]*">(.*?)</div>\s*(?=<div\s+class="rwdTr|$)',
            re.DOTALL,
        )
        rows = row_pattern.findall(html_content)

        # Build a map of jump index → transport modes
        transport_map: Dict[int, List[str]] = {}
        player_transport_pattern = re.compile(
            r'class="rwdTd pgCol">\s*<div>\s*<span>([^<]+)</span>\s*<span>([^<]*)</span>',
        )

        for row_html in rows:
            # Find the data-ftjson in this row to get the jump index
            ftjson_match = pattern.search(row_html)
            if not ftjson_match:
                continue
            try:
                row_data = json.loads(html.unescape(ftjson_match.group(1)))
                jump = row_data.get("jump", 0)
            except (json.JSONDecodeError, ValueError):
                continue

            # Find all player transport modes in this row
            transports = []
            for _name, mode in player_transport_pattern.findall(row_html):
                transports.append(mode.strip())
            transport_map[jump] = transports

        # Also extract open slot counts
        open_slots_pattern = re.compile(
            r'class="slotCount[^"]*openSlots(\d+)\s+maxPlayers(\d+)"',
        )
        open_slots_map: Dict[int, Dict[str, int]] = {}
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

            # Skip non-tee-time entries (events, headers, etc.)
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

            slots.append({
                "date": date,
                "time": data.get("time:0", ""),
                "front_back": "F",  # Default; could parse from sF div
                "players": players,
                "open_slots": open_count,
                "max_players": max_players,
                "ttdata": data.get("ttdata", ""),
                "jump": data.get("jump", 0),
                "p5_allowed": data.get("p5", "No") == "Yes",
            })

        logger.info("Parsed %d tee time slots for %s", len(slots), date)
        return slots

    @staticmethod
    def _parse_my_tee_times(html_content: str) -> List[Dict[str, Any]]:
        """Parse the Member_teelist_list HTML for the user's bookings."""
        bookings: List[Dict[str, Any]] = []

        # The tee time list uses data-ftjson attributes similar to the sheet
        pattern = re.compile(r'data-ftjson="([^"]+)"')
        matches = pattern.findall(html_content)

        for raw_json in matches:
            try:
                data = json.loads(html.unescape(raw_json))
            except (json.JSONDecodeError, ValueError):
                continue

            # Extract date and time from the data
            ft_date = data.get("date", 0)
            if ft_date:
                date_str = str(ft_date)
                if len(date_str) == 8:
                    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
                else:
                    formatted_date = date_str
            else:
                formatted_date = ""

            bookings.append({
                "date": formatted_date,
                "time": data.get("stime", data.get("time:0", "")),
                "course": data.get("course", ""),
                "type": data.get("type", ""),
                "raw": data,
            })

        return bookings


# ------------------------------------------------------------------
# Singleton
# ------------------------------------------------------------------

_foretees_service: Optional[ForeteesService] = None


def get_foretees_service() -> ForeteesService:
    """Return a process-wide singleton instance of the ForeTees service."""
    global _foretees_service
    if _foretees_service is None:
        _foretees_service = ForeteesService(ForeteesConfig.from_env())
    return _foretees_service


def reset_foretees_service() -> None:
    """Reset the cached service instance (for tests)."""
    global _foretees_service
    _foretees_service = None


def create_user_foretees_service(username: str, password: str) -> ForeteesService:
    """Create a request-scoped ForeteesService with per-user credentials."""
    config = ForeteesConfig(enabled=True, username=username, password=password)
    return ForeteesService(config)
