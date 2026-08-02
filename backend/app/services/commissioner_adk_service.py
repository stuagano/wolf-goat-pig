"""Commissioner data-chat via Google ADK — agent with read-only SQL tools."""

from __future__ import annotations

import logging
import os
from typing import Any

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_APP_NAME = "wgp_commissioner"


def _ensure_vertex_env() -> None:
    """Map WGP env vars to the names ADK / google-genai expect for Vertex."""
    project = os.getenv("GCP_PROJECT_ID", "").strip()
    if not project:
        raise ValueError("Commissioner AI is not configured (GCP_PROJECT_ID missing)")

    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project)
    location = os.getenv("GCP_LOCATION", "global").strip() or "global"
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", location)


def _model_name() -> str:
    return os.getenv("COMMISSIONER_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"


def _make_tools(db: Session, trace: dict[str, Any]):
    """Build per-request tools bound to the SQLAlchemy session."""
    from app.routers.commissioner import (
        _build_data_context,
        _execute_readonly_sql,
        _validate_sql,
    )

    def get_season_context() -> dict[str, str]:
        """Return the current club season leaderboard and registered players."""
        return {"context": _build_data_context(db)}

    def run_readonly_sql(sql: str) -> dict[str, Any]:
        """Run a read-only PostgreSQL SELECT against allowed WGP tables.

        Use legacy_rounds_official for club season standings. Results are capped
        at 100 rows. Only SELECT / WITH queries pass validation.
        """
        if not _validate_sql(sql):
            return {
                "status": "error",
                "message": "Query failed safety validation. Use only allowed tables and SELECT.",
            }

        results = _execute_readonly_sql(db, sql)
        if "error" in results:
            return {"status": "error", "message": results["error"]}

        trace["sql_used"] = sql
        trace["table_data"] = results
        return {"status": "success", **results}

    return [get_season_context, run_readonly_sql]


def _build_instruction(data_context: str) -> str:
    from app.routers.commissioner import DATA_SCHEMA, WGP_RULES

    return f"""{WGP_RULES}

{DATA_SCHEMA}

{data_context}

You are Commissioner Hover Over — the all-knowing statistician and historian of Wolf Goat Pig.

Use the tools to answer data questions:
- `get_season_context` for a quick leaderboard / player snapshot (already in prompt too).
- `run_readonly_sql` when you need precise numbers from the database.

Default to `legacy_rounds_official` for ANY season / leaderboard / standings /
"who's ahead" / rounds-played / historical-performance question. Only use
`player_statistics` when the question explicitly asks about in-app live games,
solo rates, streaks, or hole-by-hole app scoring.
For club standings, total quarters is the only ranking metric. Do not select,
calculate, or discuss wins or win percentage unless the user explicitly asks.

If the question is purely about rules (not data), answer directly without SQL.
If you're unsure which player is meant, use ILIKE with wildcards for fuzzy matching.

Narrate answers in your voice: authoritative, colorful golf commentary, using
specific numbers from tool results. Keep it concise but entertaining."""


def _extract_text(event) -> str:
    if not event.content or not event.content.parts:
        return ""
    chunks: list[str] = []
    for part in event.content.parts:
        if part.text:
            chunks.append(part.text)
    return "".join(chunks).strip()


async def run_data_chat_adk(db: Session, question: str, data_context: str) -> dict[str, Any]:
    """Run Commissioner Hover Over via ADK with SQL tools."""
    _ensure_vertex_env()
    trace: dict[str, Any] = {}

    agent = Agent(
        name="commissioner_hover_over",
        model=_model_name(),
        instruction=_build_instruction(data_context),
        tools=_make_tools(db, trace),
        generate_content_config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=2048,
        ),
    )

    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name=_APP_NAME,
        session_service=session_service,
    )
    session = await session_service.create_session(
        app_name=_APP_NAME,
        user_id="wgp",
    )

    user_msg = types.Content(
        role="user",
        parts=[types.Part.from_text(text=question)],
    )

    response_text = ""
    async for event in runner.run_async(
        user_id="wgp",
        session_id=session.id,
        new_message=user_msg,
    ):
        if event.is_final_response():
            text = _extract_text(event)
            if text:
                response_text = text

    if not response_text:
        raise ValueError("LLM returned empty response")

    return {
        "response": response_text,
        "table_data": trace.get("table_data"),
        "sql_used": trace.get("sql_used"),
    }
