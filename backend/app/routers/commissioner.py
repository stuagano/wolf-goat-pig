"""Commissioner chat endpoint — natural language queries over game history and rules.

Uses Claude (Haiku) with the full WGP ruleset and live DB context as the system
prompt, so players can ask anything: rules clarifications, historical stats,
leaderboard questions, head-to-head records.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..utils.api_helpers import ApiResponse, handle_api_errors

logger = logging.getLogger("app.routers.commissioner")

router = APIRouter(prefix="/api/commissioner", tags=["commissioner"])

WGP_RULES = """
You are the Wolf Goat Pig Commissioner — an authoritative, friendly rules expert and
statistician for this private golf betting game played at Wing Point Golf & Country Club.

## The Game: Wolf Goat Pig (WGP)

### Core Structure
4-player game (5-man and 6-man variants exist). Players rotate as Captain each hole.
Captain tees off first, then chooses a partner or goes solo before all others have hit.

### Betting Phases (4-player)
- Holes 1–12: Regular play, 1Q base wager
- Holes 13–16: Vinnie's Variation — base wager doubles to 2Q
- Holes 17–18: Hoepfinger — the Goat (player furthest down) picks tee position and
  can invoke Joe's Special to set the wager at 2, 4, or 8 quarters

### Captain Rules
- Captain tees first, then picks a partner from players who haven't hit yet
- If declined, the declining player goes solo AND the bet doubles
- Captain can go solo voluntarily (becomes "the Pig") — bet doubles
- The Duncan: Captain declares solo BEFORE hitting → wins 3Q for every 2Q wagered

### Carry-Over
- If a hole is tied (halved), the wager carries over to the next hole (doubles)
- Consecutive carry-overs are blocked — second straight push resets, doesn't stack

### Special Rules
- **Karl Marx Rule**: When quarters can't divide evenly, the player furthest down pays/wins less
- **The Float**: Each Captain gets one Float per round — invoke before anyone hits to double the base wager
- **The Option**: If the Captain is the Goat, the bet automatically doubles unless turned off
- **Creecher Feature**: Handicap strokes — easiest 6 holes get half-stroke; net handicaps relative to lowest
- **Line of Scrimmage**: Can't offer a double after passing the furthest ball from the hole
- **Big Dick**: On 18th tee, biggest winner can go solo vs everyone — all or nothing
- **Aardvark** (5-man): 5th player can ask to join a team after it forms; rejection doubles the bet
- **Joe's Special**: At Hoepfinger start, the Goat sets the starting value: 2, 4, or 8Q

### Scoring
- Quarters (Q) are the betting unit
- Team with best ball wins; ties carry over
- Zero-sum: total quarters won = total quarters lost across all players
""".strip()


class ChatRequest(BaseModel):
    message: str
    game_state: dict[str, Any] | None = None


def _build_data_context(db: Session) -> str:
    """Pull current leaderboard and player list from the DB."""
    lines = []

    try:
        from ..services.unified_data_service import get_unified_data_service
        svc = get_unified_data_service(db)
        leaderboard = svc.get_unified_leaderboard()
        if leaderboard:
            lines.append("## Current Season Leaderboard")
            for entry in leaderboard[:20]:
                lines.append(
                    f"  {entry.rank}. {entry.member}: {entry.quarters:+d}Q "
                    f"over {entry.rounds} rounds (avg {entry.average:+.1f}Q/round)"
                )
    except Exception as exc:
        logger.debug("Could not load leaderboard: %s", exc)

    try:
        from .. import models
        players = db.query(models.PlayerProfile).order_by(models.PlayerProfile.name).all()
        if players:
            lines.append("\n## Registered Players")
            for p in players:
                lines.append(f"  - {p.name} (handicap: {p.handicap})")
    except Exception as exc:
        logger.debug("Could not load players: %s", exc)

    return "\n".join(lines)


def _build_game_context(game_state: dict[str, Any] | None) -> str:
    if not game_state:
        return ""
    lines = ["## Current Game State"]
    if game_state.get("current_hole"):
        lines.append(f"  Current hole: {game_state['current_hole']}")
    if game_state.get("players"):
        lines.append("  Players:")
        for p in game_state["players"]:
            name = p.get("name", "?")
            score = p.get("score", 0)
            lines.append(f"    - {name}: {score:+d}Q")
    return "\n".join(lines)


@router.post("/chat")
@handle_api_errors(operation_name="commissioner chat")
async def commissioner_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Ask the Commissioner a question about rules or game history."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Commissioner AI is not configured (GEMINI_API_KEY missing)")

    import google.generativeai as genai

    data_context = _build_data_context(db)
    game_context = _build_game_context(request.game_state)

    system = WGP_RULES
    if data_context:
        system += f"\n\n{data_context}"
    if game_context:
        system += f"\n\n{game_context}"
    system += (
        "\n\nAnswer concisely and conversationally. "
        "For rules questions, be authoritative. "
        "For stats questions, cite specific numbers from the data above. "
        "If you don't have data to answer a stats question, say so honestly."
    )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=system,
    )
    response = model.generate_content(request.message)
    return ApiResponse.success(data={"response": response.text})
