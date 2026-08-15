from __future__ import annotations

import time
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.news.rss_reader import RSSError, fetch_recent_articles


def _fake_entry(title, link, summary="", published_parsed=None):
    return SimpleNamespace(
        title=title,
        link=link,
        summary=summary,
        published_parsed=published_parsed or time.gmtime(),
    )


def _fake_feed(title, entries):
    return SimpleNamespace(
        bozo=False,
        feed={"title": title},
        entries=entries,
    )


def test_fetch_recent_articles_success():
    feed = _fake_feed("Example Feed", [_fake_entry("Story One", "https://example.com/1")])

    with patch("src.news.rss_reader.feedparser.parse", return_value=feed):
        articles = fetch_recent_articles(["https://example.com/rss"], max_articles=3)

    assert len(articles) == 1
    assert articles[0].title == "Story One"
    assert articles[0].source == "Example Feed"


def test_fetch_recent_articles_respects_max_articles():
    entries = [_fake_entry(f"Story {i}", f"https://example.com/{i}") for i in range(5)]
    feed = _fake_feed("Example Feed", entries)

    with patch("src.news.rss_reader.feedparser.parse", return_value=feed):
        articles = fetch_recent_articles(["https://example.com/rss"], max_articles=2)

    assert len(articles) == 2


def test_fetch_recent_articles_no_feeds_configured():
    with pytest.raises(RSSError):
        fetch_recent_articles([], max_articles=3)


def test_fetch_recent_articles_all_feeds_fail():
    with patch("src.news.rss_reader.feedparser.parse", side_effect=Exception("boom")):
        with pytest.raises(RSSError):
            fetch_recent_articles(["https://example.com/rss"], max_articles=3)


def test_fetch_recent_articles_skips_malformed_entries():
    good = _fake_entry("Good Story", "https://example.com/good")
    bad = SimpleNamespace(title="", link="", summary="", published_parsed=time.gmtime())
    feed = _fake_feed("Example Feed", [good, bad])

    with patch("src.news.rss_reader.feedparser.parse", return_value=feed):
        articles = fetch_recent_articles(["https://example.com/rss"], max_articles=5)

    assert len(articles) == 1
    assert articles[0].title == "Good Story"
