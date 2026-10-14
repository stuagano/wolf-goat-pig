"""Scorecard vision agent — Vertex Gemini multimodal on Cloud Run."""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    scorecard_service_secret: str = Field(default="", validation_alias="SCORECARD_SERVICE_SECRET")
    gcp_project_id: str = Field(default="seventh-country-232522", validation_alias="GCP_PROJECT_ID")
    gcp_location: str = Field(default="global", validation_alias="GCP_LOCATION")
    vision_model: str = Field(default="gemini-2.5-flash", validation_alias="SCORECARD_VISION_MODEL")
    max_correction_passes: int = Field(default=2, validation_alias="SCORECARD_MAX_CORRECTION_PASSES")
    # Gemini 2.5 thinking tokens count against max_output_tokens. Uncapped, they ate ~7.6k of
    # 8k and truncated the JSON on every scan, so cap thinking and leave room for the answer.
    thinking_budget: int = Field(default=1024, validation_alias="SCORECARD_THINKING_BUDGET")
    max_output_tokens: int = Field(default=16384, validation_alias="SCORECARD_MAX_OUTPUT_TOKENS")
    skip_reference_examples: bool = Field(default=False, validation_alias="SCORECARD_SKIP_REFERENCE_EXAMPLES")
    preprocess_max_dim: int = Field(default=3000, validation_alias="SCORECARD_PREPROCESS_MAX_DIM")
    port: int = int(os.getenv("PORT", "8080"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
