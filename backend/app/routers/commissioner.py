"""Commissioner chat endpoint — natural language queries over game history and rules.

Uses Claude (Haiku) with the full WGP ruleset and live DB context as the system
prompt, so players can ask anything: rules clarifications, historical stats,
leaderboard questions, head-to-head records.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..utils.api_helpers import ApiResponse, handle_api_errors

logger = logging.getLogger("app.routers.commissioner")

router = APIRouter(prefix="/api/commissioner", tags=["commissioner"])

_GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


async def _llm_generate(
    prompt: str,
    system_instruction: str,
) -> str:
    """Call Groq API (OpenAI-compatible) for LLM generation."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Commissioner AI is not configured (GROQ_API_KEY missing)")

    payload = {
        "model": _GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            _GROQ_API_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        if resp.status_code == 429:
            raise ValueError("Commissioner is getting too many questions right now. Try again in a minute.")
        if resp.status_code != 200:
            body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            err_msg = body.get("error", {}).get("message", "unknown error")
            logger.error("Groq API %d: %s", resp.status_code, err_msg)
            raise ValueError(f"LLM API error: {err_msg}")

    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise ValueError("LLM returned no choices")
    return choices[0].get("message", {}).get("content", "")


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
    """Build leaderboard and player context from the Render DB only."""
    from .. import models
    from sqlalchemy import func

    lines = []

    # Leaderboard: aggregate legacy_rounds by member
    try:
        rows = (
            db.query(
                models.LegacyRound.member,
                func.sum(models.LegacyRound.score).label("quarters"),
                func.count(models.LegacyRound.id).label("rounds"),
            )
            .group_by(models.LegacyRound.member)
            .order_by(func.sum(models.LegacyRound.score).desc())
            .limit(20)
            .all()
        )
        if rows:
            lines.append("## Current Season Leaderboard")
            for i, row in enumerate(rows, 1):
                avg = row.quarters / row.rounds if row.rounds else 0
                lines.append(
                    f"  {i}. {row.member}: {row.quarters:+d}Q "
                    f"over {row.rounds} rounds (avg {avg:+.1f}Q/round)"
                )
        else:
            lines.append("## Leaderboard\n  (no historical data synced yet — run /data/sync-sheets)")
    except Exception as exc:
        logger.warning("Could not load leaderboard from DB: %s", exc)

    # Registered players with handicaps
    try:
        players = db.query(models.PlayerProfile).order_by(models.PlayerProfile.name).all()
        if players:
            lines.append("\n## Registered Players")
            for p in players:
                lines.append(f"  - {p.name} (handicap: {p.handicap})")
    except Exception as exc:
        logger.warning("Could not load players: %s", exc)

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

    response_text = await _llm_generate(request.message, system)
    return ApiResponse.success(data={"response": response_text})


# ---------------------------------------------------------------------------
# Data Chat — "Ask Commissioner Hover Over"
# ---------------------------------------------------------------------------

DATA_SCHEMA = """
## Queryable Tables

### legacy_rounds
Columns: id, date, "group", member, score, location, duration, source, synced_at
IMPORTANT: `group` is a PostgreSQL reserved word — always quote it as "group" in queries.
Note: Uses `member` (string name) not a foreign key. Player matching requires
`player_profiles.name` or `player_profiles.legacy_name`.

### player_profiles
Columns: id, name, legacy_name, email, handicap, ghin_id, ghin_last_updated,
avatar_url, created_at, updated_at, last_played, is_active, is_ai,
playing_style, description
(EXCLUDED columns: foretees_password_encrypted, foretees_username, preferences,
personality_traits, strengths, weaknesses)

### player_statistics
Columns: id, player_id, games_played, games_won, total_earnings, holes_played,
holes_won, avg_earnings_per_hole, betting_success_rate, successful_bets,
total_bets, partnership_success_rate, partnerships_formed, partnerships_won,
solo_attempts, solo_wins, ping_pong_count, ping_pong_wins,
invisible_aardvark_appearances, invisible_aardvark_wins, duncan_attempts,
duncan_wins, tunkarri_attempts, tunkarri_wins, big_dick_attempts,
big_dick_wins, eagles, birdies, pars, bogeys, double_bogeys,
worse_than_double, current_win_streak, current_loss_streak, best_win_streak,
worst_loss_streak, times_as_wolf, times_as_goat, times_as_pig,
times_as_aardvark, last_updated

### game_records
Columns: id, game_id, course_name, game_mode, player_count,
total_holes_played, game_duration_minutes, created_at, completed_at,
final_scores

### game_player_results
Columns: id, game_record_id, player_profile_id, player_name, final_position,
total_earnings, holes_won, successful_bets, total_bets, partnerships_formed,
partnerships_won, solo_attempts, solo_wins, ping_pongs, ping_pongs_won,
duncan_attempts, duncan_wins, tunkarri_attempts, tunkarri_wins,
big_dick_attempts, big_dick_wins, created_at

### ghin_scores
Columns: id, player_profile_id, ghin_id, score_date, course_name, tees,
score, course_rating, slope_rating, differential, posted,
handicap_index_at_time, synced_at

### ghin_handicap_history
Columns: id, player_profile_id, ghin_id, effective_date, handicap_index,
revision_reason, scores_used_count, synced_at

## Relationships
- player_statistics.player_id → player_profiles.id
- game_player_results.game_record_id → game_records.id
- game_player_results.player_profile_id → player_profiles.id
- ghin_scores.player_profile_id → player_profiles.id
- ghin_handicap_history.player_profile_id → player_profiles.id
""".strip()

_ALLOWED_TABLES = {
    "legacy_rounds",
    "player_profiles",
    "player_statistics",
    "game_records",
    "game_player_results",
    "ghin_scores",
    "ghin_handicap_history",
}

_DENIED_COLUMNS = {
    "foretees_password_encrypted",
    "foretees_username",
    "preferences",
    "personality_traits",
    "strengths",
    "weaknesses",
}

_DANGEROUS_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "TRUNCATE", "GRANT", "REVOKE", "EXEC",
}


def _validate_sql(sql: str) -> bool:
    """Return True if *sql* is a safe, read-only SELECT against allowed tables."""
    # Strip single-line comments
    cleaned = re.sub(r"--[^\n]*", " ", sql)
    # Strip block comments
    cleaned = re.sub(r"/\*.*?\*/", " ", cleaned, flags=re.DOTALL)
    # Normalize whitespace
    cleaned = " ".join(cleaned.split()).strip()
    # Strip a single trailing semicolon (Gemini adds these routinely)
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()

    # Must start with SELECT or WITH (CTEs)
    first_word = cleaned.split()[0].upper() if cleaned.split() else ""
    if first_word not in ("SELECT", "WITH"):
        return False

    # Reject semicolons (multi-statement injection)
    if ";" in cleaned:
        return False

    upper = cleaned.upper()

    # Reject dangerous keywords (word-boundary check)
    for kw in _DANGEROUS_KEYWORDS:
        if re.search(rf"\b{kw}\b", upper):
            return False

    # Check denied columns
    lower = cleaned.lower()
    for col in _DENIED_COLUMNS:
        if col in lower:
            return False

    # Extract CTE names (WITH name AS ...) so they're treated as valid aliases
    cte_names = {name.lower() for name in re.findall(r"\bWITH\s+(\w+)\s+AS\b", upper)}
    cte_names |= {name.lower() for name in re.findall(r",\s*(\w+)\s+AS\s*\(", upper)}
    allowed = _ALLOWED_TABLES | cte_names

    # Table allowlist — every FROM / JOIN target must be allowed
    table_refs = re.findall(r"\bFROM\s+(\w+)", upper)
    table_refs += re.findall(r"\bJOIN\s+(\w+)", upper)
    for tbl in table_refs:
        if tbl.lower() not in allowed:
            return False

    return True


def _execute_readonly_sql(db: Session, sql: str, row_limit: int = 100) -> dict:
    """Execute a read-only SQL statement and return columnar results."""
    try:
        # Enforce row limit
        upper = sql.upper().strip()
        limit_match = re.search(r"\bLIMIT\s+(\d+)", upper)
        if limit_match:
            existing_limit = int(limit_match.group(1))
            if existing_limit > row_limit:
                sql = re.sub(
                    r"(?i)\bLIMIT\s+\d+",
                    f"LIMIT {row_limit}",
                    sql,
                )
        else:
            sql = f"{sql.rstrip().rstrip(';')} LIMIT {row_limit}"

        result = db.execute(text(sql))
        columns = list(result.keys())
        rows = [list(row) for row in result.fetchall()]
        truncated = len(rows) >= row_limit

        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "truncated": truncated,
        }
    except Exception as exc:
        return {"error": str(exc)}


class DataChatRequest(BaseModel):
    question: str


@router.post("/data-chat")
@handle_api_errors(operation_name="commissioner data chat")
async def commissioner_data_chat(
    request: DataChatRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Ask Commissioner Hover Over a data question about the WGP database."""
    # Step 1: Ask Gemini to produce a SQL query (or a direct answer for rules)
    system = f"""{WGP_RULES}

{DATA_SCHEMA}

You are Commissioner Hover Over — the all-knowing statistician and historian of Wolf Goat Pig.
You have access to the full game database. When asked a data question, respond with a SQL query
wrapped in ```sql ... ``` code blocks. Use PostgreSQL syntax.

If the question is purely about rules (not data), respond directly without SQL.
If you're unsure which player is meant, use ILIKE with wildcards for fuzzy matching.

Example queries:
- "Who has the most quarters?" → SELECT member, SUM(score) as total_quarters FROM legacy_rounds GROUP BY member ORDER BY total_quarters DESC LIMIT 10
- "Stuart's handicap history" → SELECT effective_date, handicap_index FROM ghin_handicap_history gh JOIN player_profiles pp ON gh.player_profile_id = pp.id WHERE pp.name ILIKE '%Stuart%' ORDER BY effective_date
- "How many rounds per player?" → SELECT member, COUNT(*) as rounds FROM legacy_rounds GROUP BY member ORDER BY rounds DESC
- "Best single round ever?" → SELECT member, score, date, location FROM legacy_rounds ORDER BY score DESC LIMIT 5
- "Who goes solo the most?" → SELECT pp.name, ps.solo_attempts, ps.solo_wins FROM player_statistics ps JOIN player_profiles pp ON ps.player_id = pp.id WHERE ps.solo_attempts > 0 ORDER BY ps.solo_attempts DESC"""

    step1_text = await _llm_generate(request.question, system)

    # Step 2: Extract SQL from ```sql ... ``` blocks
    sql_match = re.search(r"```sql\s*(.*?)\s*```", step1_text, re.DOTALL)

    if not sql_match:
        # No SQL — this is a rules-only answer
        return ApiResponse.success(data={
            "response": step1_text,
            "table_data": None,
            "sql_used": None,
        })

    sql = sql_match.group(1).strip().rstrip(";")

    # Validate the SQL
    if not _validate_sql(sql):
        return ApiResponse.success(data={
            "response": (
                "The Commissioner attempted a query that didn't pass safety "
                "validation. Please rephrase your question."
            ),
            "table_data": None,
            "sql_used": sql,
        })

    # Execute the SQL
    results = _execute_readonly_sql(db, sql)

    if "error" in results:
        return ApiResponse.success(data={
            "response": (
                f"The Commissioner's query hit a snag: {results['error']}. "
                "Try rephrasing your question."
            ),
            "table_data": None,
            "sql_used": sql,
        })

    # Step 3: Ask Gemini to narrate the results
    narration_system = (
        "You are Commissioner Hover Over — the all-knowing statistician and "
        "historian of Wolf Goat Pig. Narrate the following query results in "
        "your voice: authoritative, colorful golf commentary, using specific "
        "numbers from the data. Keep it concise but entertaining."
    )

    narration_prompt = (
        f"The user asked: {request.question}\n\n"
        f"SQL executed: {sql}\n\n"
        f"Results (columns: {results['columns']}):\n"
    )
    for row in results["rows"]:
        narration_prompt += f"  {row}\n"
    if results["truncated"]:
        narration_prompt += "\n(Results were truncated to 100 rows.)"

    narration_text = await _llm_generate(narration_prompt, narration_system)

    return ApiResponse.success(data={
        "response": narration_text,
        "table_data": results,
        "sql_used": sql,
    })
