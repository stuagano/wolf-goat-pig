from app.config import get_settings


def test_settings_defaults():
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.vision_model == "gemini-2.5-flash"
    # Correction re-reads degraded results and pushed scans toward the 120s API timeout.
    assert settings.max_correction_passes == 0
    # Thinking must leave room for the JSON answer, or every scan truncates (MAX_TOKENS).
    assert settings.thinking_budget < settings.max_output_tokens // 4
