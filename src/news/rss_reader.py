"""Fetches recent tech articles from configurable RSS feeds.

Deliberately does not scrape article bodies — only uses what the feed
itself provides (title, summary, link, published date), which is enough
for Gemini to summarize honestly without inventing details.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import feedparser

from src.utils.logger import get_logger

logger = get_logger(__name__)


class RSSError(Exception):
    """Raised when no usable articles could be retrieved from any feed."""


@dataclass
class Article:
    title: str
    summary: str
    link: str
    source: str
    published: datetime | None


def _parse_published(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        value = getattr(entry, attr, None)
        if value:
            return datetime(*value[:6], tzinfo=timezone.utc)
    return None


def fetch_recent_articles(
    feeds: list[str],
    max_articles: int = 3,
    max_age_hours: int = 48,
) -> list[Article]:
    """Fetch and merge recent articles across all configured feeds.

    Skips feeds that fail to parse instead of crashing the whole run.
    Raises RSSError only if every single feed failed or yielded nothing.
    """
    if not feeds:
        raise RSSError("No RSS feeds configured in config/settings.yaml (news.feeds).")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    articles: list[Article] = []
    working_feeds = 0

    for url in feeds:
        try:
            parsed = feedparser.parse(url)
        except Exception as exc:  # pragma: no cover - network errors
            logger.warning("Failed to fetch feed %s: %s", url, exc)
            continue

        if getattr(parsed, "bozo", False) and not getattr(parsed, "entries", None):
            logger.warning("Malformed or empty feed: %s", url)
            continue

        source_name = parsed.feed.get("title", url) if hasattr(parsed, "feed") else url
        working_feeds += 1

        for entry in parsed.entries:
            published = _parse_published(entry)
            if published and published < cutoff:
                continue
            title = getattr(entry, "title", "").strip()
            link = getattr(entry, "link", "").strip()
            summary = getattr(entry, "summary", "").strip()
            if not title or not link:
                continue
            articles.append(
                Article(
                    title=title,
                    summary=summary,
                    link=link,
                    source=source_name,
                    published=published,
                )
            )

    if working_feeds == 0:
        raise RSSError("All configured RSS feeds failed to load.")

    if not articles:
        raise RSSError("No recent articles found in any configured feed.")

    articles.sort(key=lambda a: a.published or cutoff, reverse=True)
    return articles[:max_articles]
