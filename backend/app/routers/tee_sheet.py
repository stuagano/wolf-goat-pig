"""
Tee Sheet Integration Router

Read sign-ups from and post sign-ups to the thousand-cranes.com WGP tee sheet.
CGI endpoints: wgp_tee_sheet.cgi (read), wgp_add_tee_sheet_ajax.cgi (write)
"""

import asyncio
import logging
import re
from datetime import date as date_type
from datetime import timedelta
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger("app.routers.tee_sheet")

router = APIRouter(prefix="/tee-sheet", tags=["tee-sheet"])

TEE_SHEET_BASE = "https://thousand-cranes.com/WolfGoatPig"
TEE_SHEET_READ_URL = f"{TEE_SHEET_BASE}/wgp_tee_sheet.cgi"
TEE_SHEET_SIGNUP_URL = f"{TEE_SHEET_BASE}/wgp_add_tee_sheet_ajax.cgi"


def _parse_slots(html: str) -> list[dict]:
    rows = re.findall(r'<tr><td align="center">(\d+)</td>(.*?)</tr>', html, re.DOTALL)
    slots = []
    for slot_num, content in rows:
        name_match = re.search(r"color:#001bbf[^>]*>([^<]+)", content)
        notes_match = re.search(r"color:#800000[^>]*>([^<]+)", content)
        slots.append(
            {
                "slot": int(slot_num),
                "name": name_match.group(1).strip() if name_match else None,
                "notes": notes_match.group(1).strip() if notes_match else None,
            }
        )
    return slots


@router.get("")
async def get_tee_sheet(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
) -> dict[str, Any]:
    """Fetch current sign-ups from the thousand-cranes.com tee sheet."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                TEE_SHEET_READ_URL,
                params={"date": date},
                headers={"Referer": TEE_SHEET_READ_URL},
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Tee sheet unavailable: HTTP {e.response.status_code}")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Could not reach tee sheet: {e}")

    slots = _parse_slots(resp.text)
    signed_up = [s for s in slots if s["name"]]
    return {
        "date": date,
        "slots": slots,
        "signed_up_count": len(signed_up),
        "signed_up": signed_up,
    }


DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


async def _fetch_count(client: httpx.AsyncClient, d: str) -> dict[str, Any]:
    try:
        resp = await client.get(TEE_SHEET_READ_URL, params={"date": d}, headers={"Referer": TEE_SHEET_READ_URL})
        resp.raise_for_status()
        slots = _parse_slots(resp.text)
        count = sum(1 for s in slots if s["name"])
    except Exception:
        count = -1  # -1 signals fetch failed
    dt = date_type.fromisoformat(d)
    return {
        "date": d,
        "day": DAYS[dt.weekday() % 7 - (dt.weekday() + 1) % 7],
        "weekday": dt.strftime("%a"),
        "signed_up_count": count,
    }


# Map Python weekday (Mon=0) → JS-style Sunday-first
def _weekday_name(d: date_type) -> str:
    return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][d.weekday()]


@router.get("/upcoming")
async def get_upcoming_counts(
    start: str = Query(..., description="Start date YYYY-MM-DD"),
    days: int = Query(7, ge=1, le=14),
) -> list[dict[str, Any]]:
    """Return sign-up counts for each day in the upcoming window, fetched in parallel."""
    start_date = date_type.fromisoformat(start)
    dates = [(start_date + timedelta(days=i)).isoformat() for i in range(days)]

    async with httpx.AsyncClient(timeout=10.0) as client:
        results = await asyncio.gather(*[_fetch_count(client, d) for d in dates])

    out = []
    for r in results:
        d = date_type.fromisoformat(r["date"])
        out.append(
            {
                "date": r["date"],
                "weekday": _weekday_name(d),
                "short": d.strftime("%a"),
                "label": d.strftime("%b %-d"),
                "signed_up_count": r["signed_up_count"],
            }
        )
    return out


class SignupRequest(BaseModel):
    date: str
    name: str


@router.post("/signup")
async def signup_for_tee_sheet(request: SignupRequest) -> dict[str, Any]:
    """Sign up a player for a given date on the thousand-cranes.com tee sheet."""
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                TEE_SHEET_SIGNUP_URL,
                data={"date": request.date, "name": name, "type": "member"},
                headers={"Referer": TEE_SHEET_READ_URL},
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Tee sheet signup failed: HTTP {e.response.status_code}")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Could not reach tee sheet: {e}")

    logger.info("Signed up %s on tee sheet for %s", name, request.date)
    return {"success": True, "name": name, "date": request.date}
