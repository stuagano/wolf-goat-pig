"""Commissioner-voice intro for league emails (weekly highlights, Sunday nudge).

One LLM call per email batch writes a short, dry, trash-talking paragraph from
the real facts; the same intro goes to every recipient. The facts block in the
email is never AI-written. Any failure, timeout, or a number that isn't in the
facts drops the intro, and the email goes out exactly as it would without it.
"""

import asyncio
import json
import logging
import re
from typing import Any

from .commissioner_llm_service import llm_generate

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 20
MAX_CHARS = 600

SYSTEM_INSTRUCTION = (
    "You are the Commissioner of the Wolf Goat Pig golf game at Wing Point Golf & Country Club. "
    "Games are played on different days of the week; only name a day if the facts give it. "
    "Write the opening paragraph of a league email in a dry, wry, affectionate trash-talking voice: "
    "2-3 sentences, plain text, no markdown, no greeting, no sign-off, at most one emoji. "
    "Use ONLY the names and numbers in the facts you are given. Never invent numbers, scores, names, "
    "or events, and never mention anything that is not in the facts."
)

_NUMBER = re.compile(r"\d+(?:\.\d+)?")


def _allowed_numbers(facts: Any) -> set[str]:
    """Every number appearing in the facts, plus its magnitude (so -20 allows "20")."""
    found = set(_NUMBER.findall(json.dumps(facts, default=str)))
    return found | {n.rstrip("0").rstrip(".") for n in found if "." in n}


def commissioner_intro(kind: str, facts: dict[str, Any]) -> str | None:
    """Flavor paragraph for an email of `kind` built from `facts`, or None on any problem."""
    prompt = f"Email: {kind}\nFacts (JSON):\n{json.dumps(facts, default=str, indent=2)}"
    try:
        text = asyncio.run(asyncio.wait_for(llm_generate(prompt, SYSTEM_INSTRUCTION), TIMEOUT_SECONDS))
    except Exception as e:
        logger.warning("Commissioner intro for %s skipped: %s", kind, e)
        return None

    text = (text or "").strip().strip('"').strip()
    if not text or len(text) > MAX_CHARS:
        logger.warning("Commissioner intro for %s dropped: empty or too long (%d chars)", kind, len(text))
        return None
    invented = set(_NUMBER.findall(text)) - _allowed_numbers(facts)
    if invented:
        logger.warning("Commissioner intro for %s dropped: numbers not in facts %s", kind, sorted(invented))
        return None
    return text
