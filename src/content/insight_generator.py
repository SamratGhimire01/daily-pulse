"""Generates the evening developer/AI insight post."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from src.ai.gemini_client import GeminiClient
from src.config import Settings
from src.utils.helpers import already_exists, content_filename, ensure_dir, truncate_to_words
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROMPT = """You are writing a short "Developer Insight" post for a personal developer journal.

Pick ONE topic from a varied pool such as: a programming concept, a useful Python tip, an \
AI/ML concept, a software engineering principle, a Linux tip, a Git/GitHub concept, a database \
concept, a developer productivity technique, a small project idea, or a lesson learned from \
software development. Vary the topic day to day — avoid always picking the most obvious or \
overused one.

Keep it concise, concrete, and genuinely useful. Avoid marketing language, fake statistics, and \
excessive emojis.

Respond in EXACTLY this Markdown format and nothing else:

# Developer Insight

## Topic

<short topic title>

## Explanation

<2-4 sentence explanation>

## Practical Example

<a short, concrete example — a code snippet, command, or scenario>

## Takeaway

<1-2 sentence practical takeaway>
"""


def generate(settings: Settings, client: GeminiClient, force: bool = False, day: date | None = None) -> Path | None:
    """Generate today's developer insight post. Returns the file path, or None if skipped."""
    directory = settings.insights_dir
    ensure_dir(directory)

    if not force and already_exists(directory, day):
        logger.info("Insight for today already exists, skipping (use --force to override).")
        return None

    logger.info("Requesting developer insight from Gemini...")
    text = client.generate(PROMPT)
    text = truncate_to_words(text, settings.max_words)

    path = content_filename(directory, day)
    path.write_text(text.strip() + "\n", encoding="utf-8")
    logger.info("Saved %s", path)
    return path
