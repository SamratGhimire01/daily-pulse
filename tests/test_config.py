from __future__ import annotations

import pytest

from src.config import ConfigError, load_settings


def test_load_settings_from_real_yaml():
    settings = load_settings()  # uses the real config/settings.yaml, no .env required
    assert settings.project_name == "DailyPulse"
    assert settings.github_branch == "main"
    assert settings.news_max_articles >= 1
    assert "morning" in settings.raw["schedule"]


def test_missing_settings_file_raises(tmp_path):
    with pytest.raises(ConfigError):
        load_settings(settings_path=tmp_path / "does_not_exist.yaml")


def test_require_gemini_api_key_missing(tmp_settings):
    tmp_settings.gemini_api_key = None
    with pytest.raises(ConfigError):
        tmp_settings.require_gemini_api_key()


def test_require_gemini_api_key_present(tmp_settings):
    assert tmp_settings.require_gemini_api_key() == "fake-key-for-tests"


def test_schedule_window_unknown_slot(tmp_settings):
    with pytest.raises(ConfigError):
        tmp_settings.schedule_window("midnight")
