from app.config import get_settings


def test_settings_defaults():
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.vision_model == "gemini-2.5-flash"
    assert settings.max_correction_passes == 2
