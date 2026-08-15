"""Generates the afternoon tech news digest post from real RSS articles."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from src.ai.gemini_client import GeminiClient
from src.config import Settings
from src.news.rss_reader import Article, fetch_recent_articles
from src.utils.helpers import already_exists, content_filename, ensure_dir, truncate_to_words
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROMPT_TEMPLATE = """You are writing a short "Tech Update" digest for a personal developer \
journal, based ONLY on the real articles provided below. Do not invent facts, statistics, or \
stories that are not in the provided articles.

Articles:
{articles_block}

For EACH article, write a section in exactly this Markdown format:

# Tech Update

## Headline

<a clear, non-clickbait headline based on the article>

## Summary

<2-3 sentence factual summary of what the article actually says>

## Why It Matters

<1-2 sentences on practical relevance to developers/tech-minded readers>

## Source

<the source name and URL exactly as given>

---

Repeat this block for each article (separated by "---"), then stop. Do not add any \
introduction, conclusion, or extra commentary outside these blocks.
"""


def _format_articles(articles: list[Article]) -> str:
    blocks = []
    for i, a in enumerate(articles, start=1):
        blocks.append(
            f"{i}. Title: {a.title}\n"
            f"   Source: {a.source}\n"
            f"   URL: {a.link}\n"
            f"   Summary/excerpt: {a.summary[:600]}"
        )
    return "\n\n".join(blocks)


def generate(settings: Settings, client: GeminiClient, force: bool = False, day: date | None = None) -> Path | None:
    """Generate today's news digest. Returns the file path, or None if skipped."""
    directory = settings.news_dir
    ensure_dir(directory)

    if not force and already_exists(directory, day):
        logger.info("News digest for today already exists, skipping (use --force to override).")
        return None

    logger.info("Fetching recent articles from RSS feeds...")
    articles = fetch_recent_articles(settings.news_feeds, max_articles=settings.news_max_articles)
    logger.info("Fetched %d article(s).", len(articles))

    prompt = PROMPT_TEMPLATE.format(articles_block=_format_articles(articles))

    logger.info("Requesting news digest from Gemini...")
    text = client.generate(prompt)
    text = truncate_to_words(text, settings.max_words * settings.news_max_articles)

    path = content_filename(directory, day)
    path.write_text(text.strip() + "\n", encoding="utf-8")
    logger.info("Saved %s", path)
    return path
