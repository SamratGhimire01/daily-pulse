from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is importable as `src...` regardless of how pytest is invoked.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from src.config import Settings


@pytest.fixture
def tmp_settings(tmp_path) -> Settings:
    """A Settings object pointing entirely at a temp directory."""
    (tmp_path / "quotes").mkdir()
    (tmp_path / "news").mkdir()
    (tmp_path / "insights").mkdir()

    raw = {
        "project": {"name": "DailyPulse Test"},
        "ai": {"model": "gemini-2.5-flash"},
        "content": {
            "max_words": 400,
            "quotes_dir": str(tmp_path / "quotes"),
            "news_dir": str(tmp_path / "news"),
            "insights_dir": str(tmp_path / "insights"),
        },
        "github": {"branch": "main"},
        "news": {"max_articles": 3, "feeds": ["https://example.com/feed.xml"]},
        "schedule": {
            "morning": {"enabled": True, "start": "07:00", "end": "08:00"},
            "afternoon": {"enabled": True, "start": "12:00", "end": "13:00"},
            "evening": {"enabled": True, "start": "19:00", "end": "20:00"},
        },
    }

    # Note: content dirs above are absolute paths, and Path(a) / absolute_str
    # resolves to the absolute path, so Settings.quotes_dir etc. resolve
    # correctly to these temp dirs even though the property joins onto
    # PROJECT_ROOT internally.
    return Settings(
        raw=raw,
        gemini_api_key="fake-key-for-tests",
        github_repo_url=None,
        github_token=None,
        git_author_name="Test Bot",
        git_author_email="test@example.com",
    )
