"""Small, dependency-free helper functions shared across generators."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path


def today_str(today: date | None = None) -> str:
    """Return today's date as YYYY-MM-DD (UTC-naive, uses local system date)."""
    return (today or datetime.now().date()).isoformat()


def content_filename(directory: Path, day: date | None = None) -> Path:
    """Build the expected Markdown filename for a given content directory + day."""
    return directory / f"{today_str(day)}.md"


def already_exists(directory: Path, day: date | None = None) -> bool:
    """True if today's post already exists in the given content directory."""
    return content_filename(directory, day).exists()


def word_count(text: str) -> int:
    return len(text.split())


def truncate_to_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip() + "…"


def ensure_dir(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
