"""Playwright helpers for Computer Use action execution."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from playwright.async_api import Browser, Page, async_playwright

from .config import Settings

logger = logging.getLogger("booking_agent.browser")

WINGPOINT_LOGIN_SELECTORS = {
    "username": 'input[name="UserLOGIN"]',
    "password": 'input[name="UserPWD"]',
    "submit": 'input[name="btnLogon"]',
}


def normalize_x(x: int, screen_width: int) -> int:
    return int(x / 1000 * screen_width)


def normalize_y(y: int, screen_height: int) -> int:
    return int(y / 1000 * screen_height)


async def launch_browser(settings: Settings) -> Browser:
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        headless=settings.headless,
        args=["--disable-dev-shm-usage", "--no-sandbox"],
    )
    # Keep playwright manager on the browser object for cleanup.
    browser._wgp_playwright = pw  # type: ignore[attr-defined]
    return browser


async def new_page(browser: Browser, settings: Settings) -> tuple[Any, Page]:
    context = await browser.new_context(
        viewport={"width": settings.screen_width, "height": settings.screen_height},
        ignore_https_errors=True,
    )
    page = await context.new_page()
    return context, page


async def enter_credentials(page: Page, username: str, password: str) -> str:
    """Fill Wingpoint login without sending the password through the model."""
    await page.wait_for_selector(WINGPOINT_LOGIN_SELECTORS["username"], timeout=15000)
    await page.fill(WINGPOINT_LOGIN_SELECTORS["username"], username)
    await page.fill(WINGPOINT_LOGIN_SELECTORS["password"], password)
    await page.click(WINGPOINT_LOGIN_SELECTORS["submit"])
    await page.wait_for_load_state("networkidle")
    return "credentials_submitted"


async def execute_computer_action(
    page: Page,
    name: str,
    args: dict[str, Any],
    screen_width: int,
    screen_height: int,
) -> str:
    """Execute a Gemini Computer Use predefined function via Playwright."""
    try:
        if name == "open_web_browser":
            return "success"

        if name == "wait_5_seconds":
            await page.wait_for_timeout(5000)
            return "success"

        if name == "go_back":
            await page.go_back(wait_until="domcontentloaded")
            return "success"

        if name == "go_forward":
            await page.go_forward(wait_until="domcontentloaded")
            return "success"

        if name == "search":
            return "unsupported_in_this_environment"

        if name == "navigate":
            url = args.get("url") or args.get("address")
            if not url:
                return "error: missing url"
            await page.goto(str(url), wait_until="domcontentloaded")
            return "success"

        if name in {"click_at", "hover_at"}:
            x = normalize_x(int(args["x"]), screen_width)
            y = normalize_y(int(args["y"]), screen_height)
            if name == "hover_at":
                await page.mouse.move(x, y)
            else:
                await page.mouse.click(x, y)
            return "success"

        if name == "type_text_at":
            x = normalize_x(int(args["x"]), screen_width)
            y = normalize_y(int(args["y"]), screen_height)
            text = str(args.get("text", ""))
            press_enter = bool(args.get("press_enter", False))
            clear_before = bool(args.get("clear_before_typing", True))
            await page.mouse.click(x, y)
            await page.wait_for_timeout(100)
            if clear_before:
                await page.keyboard.press("Meta+A")
                await page.keyboard.press("Backspace")
            await page.keyboard.type(text, delay=20)
            if press_enter:
                await page.keyboard.press("Enter")
            return "success"

        if name == "key_combination":
            keys = args.get("keys") or args.get("key")
            if isinstance(keys, list):
                await page.keyboard.press("+".join(str(k) for k in keys))
            elif keys:
                await page.keyboard.press(str(keys))
            return "success"

        if name == "scroll_document":
            direction = str(args.get("direction", "down")).lower()
            delta = 600 if direction in {"down", "right"} else -600
            if direction in {"left", "right"}:
                await page.mouse.wheel(delta, 0)
            else:
                await page.mouse.wheel(0, delta)
            return "success"

        if name == "scroll_at":
            x = normalize_x(int(args.get("x", 500)), screen_width)
            y = normalize_y(int(args.get("y", 500)), screen_height)
            direction = str(args.get("direction", "down")).lower()
            magnitude = int(args.get("magnitude", 800))
            await page.mouse.move(x, y)
            dx = dy = 0
            if direction == "down":
                dy = magnitude
            elif direction == "up":
                dy = -magnitude
            elif direction == "right":
                dx = magnitude
            elif direction == "left":
                dx = -magnitude
            await page.mouse.wheel(dx, dy)
            return "success"

        if name == "drag_and_drop":
            x = normalize_x(int(args["x"]), screen_width)
            y = normalize_y(int(args["y"]), screen_height)
            dest_x = normalize_x(int(args.get("destination_x", args["x"])), screen_width)
            dest_y = normalize_y(int(args.get("destination_y", args["y"])), screen_height)
            await page.mouse.move(x, y)
            await page.mouse.down()
            await page.mouse.move(dest_x, dest_y, steps=12)
            await page.mouse.up()
            return "success"

        logger.warning("Unrecognized computer action: %s", name)
        return f"unknown_function:{name}"
    except Exception as exc:
        logger.exception("Action %s failed", name)
        return f"error: {exc}"


async def settle(page: Page, ms: int = 400) -> None:
    await page.wait_for_timeout(ms)
    await asyncio.sleep(0)
