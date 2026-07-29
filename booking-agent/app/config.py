"""ForeTees booking agent — Gemini Computer Use + Playwright on Cloud Run."""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    booking_service_secret: str = ""
    gcp_project_id: str = "seventh-country-232522"
    gcp_location: str = "global"
    # Must be a model that actually serves the Computer Use tool. Vertex rejects
    # `gemini-3.5-flash` here with "computer use is not supported for this model
    # in this region" (8/8 calls on the global endpoint), and Gemini 3.x emits a
    # different FunctionCall name set than browser.execute_computer_action
    # implements. The dedicated 2.5 model answers reliably and speaks that set.
    computer_use_model: str = "gemini-2.5-computer-use-preview-10-2025"
    max_agent_turns: int = 40
    job_ttl_seconds: int = 900
    screen_width: int = 1280
    screen_height: int = 720
    headless: bool = True
    wingpoint_base: str = "https://www.wingpointgolf.com"
    login_page: str = "/public/member-login-465.html"
    tee_time_page: str = "/members/golf/make-a-tee-time-703.html"
    foretees_base: str = "https://ftapp.wingpointgolf.com/v5/wingpointgcc_flxrez0_m30"
    port: int = int(os.getenv("PORT", "8080"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
