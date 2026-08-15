"""Generates the morning quote + reflection post."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from src.ai.gemini_client import GeminiClient
from src.config import Settings
from src.utils.helpers import already_exists, content_filename, ensure_dir, truncate_to_words
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROMPT = """You are writing a short daily "Daily Quote" post for a personal developer journal.

Rules:
- Choose ONE real, well-known quote related to technology, building things, learning, or \
persistence, and its correct attribution.
- If you are not confident the attribution is accurate, do NOT fabricate one. Instead, write \
an ORIGINAL one-sentence thought yourself and label it clearly as "An original thought" \
instead of attributing it to anyone.
- Do not reuse extremely overused quotes if you can find a good, meaningful, less generic one.
- Write a short 2-4 sentence reflection on the quote in a natural, thoughtful, non-corporate tone.
- Avoid emojis, hashtags, and marketing language.

Respond in EXACTLY this Markdown format and nothing else:

# Daily Quote

> "<the quote text>"

— <attribution, or "An original thought" if no confident attribution exists>

## Reflection

<2-4 sentence reflection>
"""


def generate(settings: Settings, client: GeminiClient, force: bool = False, day: date | None = None) -> Path | None:
    """Generate today's quote post. Returns the file path, or None if skipped (already exists)."""
    directory = settings.quotes_dir
    ensure_dir(directory)

    if not force and already_exists(directory, day):
        logger.info("Quote for today already exists, skipping (use --force to override).")
        return None

    logger.info("Requesting quote content from Gemini...")
    text = client.generate(PROMPT)
    text = truncate_to_words(text, settings.max_words)

    path = content_filename(directory, day)
    path.write_text(text.strip() + "\n", encoding="utf-8")
    logger.info("Saved %s", path)
    return path
