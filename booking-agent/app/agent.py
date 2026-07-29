"""Gemini Computer Use agent loop for ForeTees book/cancel."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from google import genai
from google.genai import types

from . import browser as browser_ops
from .config import Settings, get_settings
from .jobs import BookingJob, JobKind, JobStatus, job_store, screenshot_to_b64

logger = logging.getLogger("booking_agent.agent")

SYSTEM_INSTRUCTION = """
You are automating Wingpoint Golf Club / ForeTees tee-time booking in a browser.

RULES:
1. Never type usernames or passwords. For login:
   - Navigate to the Wingpoint member login page if needed.
   - Call request_confirmation(kind="login", explanation=...).
   - After the user confirms, call enter_foretees_credentials().
2. Before clicking Submit Request, Submit Changes, or Cancel Reservation:
   - Call request_confirmation(kind="submit", explanation=...).
   - Only click the button after the user confirms.
3. Stay on wingpointgolf.com and ftapp.wingpointgolf.com only.
4. When the booking/cancel outcome is clear from the page (success or ForeTees
   error messages), call report_booking_result(...).
5. Prefer precise clicks on visible tee-time links and form controls.
6. If stuck after several attempts, call report_booking_result(success=false, ...).
""".strip()

REQUEST_CONFIRMATION_DECL = types.FunctionDeclaration(
    name="request_confirmation",
    description=(
        "Pause and ask the end user to confirm before a sensitive step "
        "(login or final submit/cancel)."
    ),
    parameters_json_schema={
        "type": "object",
        "properties": {
            "kind": {
                "type": "string",
                "enum": ["login", "submit", "safety"],
                "description": "Which sensitive step needs confirmation",
            },
            "explanation": {
                "type": "string",
                "description": "Short human-readable explanation for the user",
            },
        },
        "required": ["kind", "explanation"],
    },
)

ENTER_CREDENTIALS_DECL = types.FunctionDeclaration(
    name="enter_foretees_credentials",
    description=(
        "Fill and submit the Wingpoint login form using server-side credentials. "
        "Call only after request_confirmation(kind='login') was approved."
    ),
    parameters_json_schema={"type": "object", "properties": {}},
)

REPORT_RESULT_DECL = types.FunctionDeclaration(
    name="report_booking_result",
    description="Report the final booking or cancel outcome and end the task.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "title": {"type": "string"},
            "messages": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["success"],
    },
)


def _client(settings: Settings) -> genai.Client:
    return genai.Client(
        vertexai=True,
        project=settings.gcp_project_id,
        location=settings.gcp_location,
    )


def _generate_config(settings: Settings) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.2,
        tools=[
            # Every predefined action stays enabled — browser.execute_computer_action
            # implements the full Gemini 2.5 set, including drag_and_drop.
            types.Tool(
                computer_use=types.ComputerUse(
                    environment=types.Environment.ENVIRONMENT_BROWSER,
                )
            ),
            types.Tool(
                function_declarations=[
                    REQUEST_CONFIRMATION_DECL,
                    ENTER_CREDENTIALS_DECL,
                    REPORT_RESULT_DECL,
                ]
            ),
        ],
    )


def _goal_text(job: BookingJob, settings: Settings) -> str:
    args = job.args
    login_url = f"{settings.wingpoint_base}{settings.login_page}"
    tee_url = f"{settings.wingpoint_base}{settings.tee_time_page}"
    ft_base = settings.foretees_base

    if job.kind == JobKind.BOOK:
        players = args.get("players") or []
        players_line = ", ".join(players) if players else "(none — book solo)"
        return (
            f"Book a ForeTees tee time.\n"
            f"- Login page: {login_url}\n"
            f"- After login, open tee-time entry: {tee_url} (extract SSO into ForeTees)\n"
            f"- ForeTees base: {ft_base}\n"
            f"- Date (YYYY-MM-DD): {args.get('date')}\n"
            f"- Time label exactly: {args.get('time')}\n"
            f"- Transport mode select value: {args.get('transport_mode') or 'WLK'} "
            f"(WLK=Walking, CRT=Cart, PC=Push Cart)\n"
            f"- Co-players to add: {players_line}\n"
            f"Use Member_sheet?calDate=MM/DD/YYYY after SSO. Click the exact time link, "
            f"add co-players if listed, set transport, then submit."
        )

    ttdata = args.get("ttdata")
    return (
        f"Cancel a ForeTees tee time.\n"
        f"- Login page: {login_url}\n"
        f"- ForeTees base: {ft_base}\n"
        f"- Preferred: open {ft_base}/Member_teelist_list and cancel the booking "
        f"with ttdata={ttdata!r}\n"
        f"- Fallback date/time: {args.get('date')} / {args.get('time')}\n"
        f"Click Cancel Reservation only after confirmation."
    )


def _function_calls(response: Any) -> list[Any]:
    calls: list[Any] = []
    if not response.candidates:
        return calls
    content = response.candidates[0].content
    if not content or not content.parts:
        return calls
    for part in content.parts:
        if part.function_call:
            calls.append(part.function_call)
    return calls


def _safety_decision(fc: Any) -> dict[str, Any] | None:
    args = dict(fc.args or {})
    decision = args.get("safety_decision")
    if isinstance(decision, dict):
        return decision
    return None


async def _pause_for_confirm(
    job: BookingJob,
    kind: str,
    explanation: str,
    page: Any,
) -> bool:
    png = await page.screenshot(type="png", full_page=False)
    job.status = JobStatus.NEEDS_CONFIRMATION
    job.confirm_kind = kind
    job.explanation = explanation
    job.screenshot_b64 = screenshot_to_b64(png)
    job.confirm_event = asyncio.Event()
    job.confirm_decision = None
    job.touch()
    logger.info("job %s waiting for confirm kind=%s", job.id, kind)
    await job.confirm_event.wait()
    approved = bool(job.confirm_decision)
    job.status = JobStatus.RUNNING
    job.confirm_kind = None
    job.explanation = None
    job.screenshot_b64 = None
    job.touch()
    return approved


async def _function_response_part(
    name: str,
    page: Any,
    payload: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> types.Part:
    png = await page.screenshot(type="png", full_page=False)
    response_body = {"url": page.url, **payload}
    if extra:
        response_body.update(extra)
    return types.Part(
        function_response=types.FunctionResponse(
            name=name,
            response=response_body,
            parts=[
                types.FunctionResponsePart(
                    inline_data=types.FunctionResponseBlob(
                        mime_type="image/png",
                        data=png,
                    )
                )
            ],
        )
    )


async def run_job(job: BookingJob) -> dict[str, Any]:
    settings = get_settings()
    client = _client(settings)
    config = _generate_config(settings)

    browser = await browser_ops.launch_browser(settings)
    context, page = await browser_ops.new_page(browser, settings)
    job.browser = browser
    job.context = context
    job.page = page

    try:
        await page.goto(
            f"{settings.wingpoint_base}{settings.login_page}",
            wait_until="domcontentloaded",
        )
        png = await page.screenshot(type="png", full_page=False)
        job.contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(text=_goal_text(job, settings)),
                    types.Part.from_bytes(data=png, mime_type="image/png"),
                ],
            )
        ]

        for turn in range(settings.max_agent_turns):
            job.touch()
            logger.info("job %s turn %s url=%s", job.id, turn + 1, page.url)
            response = await asyncio.to_thread(
                lambda: client.models.generate_content(
                    model=settings.computer_use_model,
                    contents=job.contents,
                    config=config,
                )
            )
            job.contents.append(response.candidates[0].content)

            calls = _function_calls(response)
            if not calls:
                text = getattr(response, "text", None) or "Agent stopped without a result"
                job.status = JobStatus.FAILED
                job.error = text
                return job.to_response()

            fr_parts: list[types.Part] = []
            terminal: dict[str, Any] | None = None

            for fc in calls:
                name = fc.name
                args = dict(fc.args or {})
                extra_fr: dict[str, Any] = {}

                safety = _safety_decision(fc)
                if safety and str(safety.get("decision", "")).lower() in {
                    "require_confirmation",
                    "require_user_confirmation",
                }:
                    explanation = str(
                        safety.get("explanation")
                        or args.get("explanation")
                        or "The safety system requires your confirmation."
                    )
                    approved = await _pause_for_confirm(job, "safety", explanation, page)
                    if not approved:
                        job.status = JobStatus.FAILED
                        job.error = "User denied safety confirmation"
                        await job.close_browser()
                        return job.to_response()
                    extra_fr["safety_acknowledgement"] = "true"

                if name == "request_confirmation":
                    kind = str(args.get("kind") or "safety")
                    explanation = str(args.get("explanation") or "Confirmation required")
                    approved = await _pause_for_confirm(job, kind, explanation, page)
                    if not approved:
                        job.status = JobStatus.FAILED
                        job.error = "User denied confirmation"
                        await job.close_browser()
                        return job.to_response()
                    fr_parts.append(
                        await _function_response_part(
                            name,
                            page,
                            {"result": "confirmed"},
                            extra_fr,
                        )
                    )
                    continue

                if name == "enter_foretees_credentials":
                    username = job.args.get("username") or ""
                    password = job.args.get("password") or ""
                    result = await browser_ops.enter_credentials(page, username, password)
                    await browser_ops.settle(page, 800)
                    fr_parts.append(
                        await _function_response_part(
                            name,
                            page,
                            {"result": result},
                            extra_fr,
                        )
                    )
                    continue

                if name == "report_booking_result":
                    messages = args.get("messages") or []
                    if isinstance(messages, str):
                        messages = [messages]
                    terminal = {
                        "success": bool(args.get("success")),
                        "title": str(args.get("title") or ""),
                        "messages": [str(m) for m in messages],
                    }
                    fr_parts.append(
                        await _function_response_part(
                            name,
                            page,
                            {"result": "acknowledged"},
                            extra_fr,
                        )
                    )
                    continue

                # Heuristic: treat credential typing attempts as forbidden.
                if name == "type_text_at" and "password" in page.url.lower():
                    fr_parts.append(
                        await _function_response_part(
                            name,
                            page,
                            {
                                "result": (
                                    "blocked: use enter_foretees_credentials after "
                                    "request_confirmation(kind=login)"
                                )
                            },
                            extra_fr,
                        )
                    )
                    continue

                result = await browser_ops.execute_computer_action(
                    page,
                    name,
                    args,
                    settings.screen_width,
                    settings.screen_height,
                )
                await browser_ops.settle(page, 500)
                fr_parts.append(
                    await _function_response_part(
                        name,
                        page,
                        {"result": result},
                        extra_fr,
                    )
                )

            job.contents.append(types.Content(role="user", parts=fr_parts))

            if terminal is not None:
                job.status = JobStatus.COMPLETED
                job.result = terminal
                await job.close_browser()
                return job.to_response()

        job.status = JobStatus.FAILED
        job.error = f"Exceeded max agent turns ({settings.max_agent_turns})"
        await job.close_browser()
        return job.to_response()
    except Exception as exc:
        logger.exception("job %s crashed", job.id)
        job.status = JobStatus.FAILED
        job.error = str(exc)
        await job.close_browser()
        return job.to_response()


async def start_job(kind: JobKind, args: dict[str, Any]) -> dict[str, Any]:
    job = await job_store.create(kind, args)

    async def _runner() -> None:
        async with job.lock:
            await run_job(job)

    asyncio.create_task(_runner())

    # Wait until the job either needs confirmation or finishes the first stretch.
    for _ in range(600):  # up to ~5 minutes of polling at 0.5s
        await asyncio.sleep(0.5)
        if job.status in {
            JobStatus.NEEDS_CONFIRMATION,
            JobStatus.COMPLETED,
            JobStatus.FAILED,
        }:
            return job.to_response()
    job.status = JobStatus.FAILED
    job.error = "Timed out waiting for agent progress"
    await job.close_browser()
    return job.to_response()


async def confirm_job(job_id: str, confirm: bool) -> dict[str, Any]:
    job = await job_store.get(job_id)
    if not job:
        return {"status": "failed", "success": False, "error": "Unknown job_id"}

    if job.status != JobStatus.NEEDS_CONFIRMATION:
        # Idempotent: if already terminal, return that.
        if job.status in {JobStatus.COMPLETED, JobStatus.FAILED}:
            return job.to_response()
        return {
            "status": "failed",
            "success": False,
            "error": f"Job is {job.status.value}, not awaiting confirmation",
            "job_id": job_id,
        }

    job.confirm_decision = confirm
    job.confirm_event.set()

    for _ in range(600):
        await asyncio.sleep(0.5)
        if job.status in {
            JobStatus.NEEDS_CONFIRMATION,
            JobStatus.COMPLETED,
            JobStatus.FAILED,
        }:
            return job.to_response()

    return {
        "status": "failed",
        "success": False,
        "error": "Timed out after confirmation",
        "job_id": job_id,
    }
