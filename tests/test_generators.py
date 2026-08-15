from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from src.content import insight_generator, news_generator, quote_generator
from src.news.rss_reader import Article


class FakeGeminiClient:
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.calls = []

    def generate(self, prompt: str) -> str:
        self.calls.append(prompt)
        return self.response_text


def test_quote_generator_writes_file(tmp_settings):
    fake_client = FakeGeminiClient("# Daily Quote\n\n> \"Test quote\"\n\n— Someone\n\n## Reflection\n\nA thought.")
    day = date(2026, 8, 15)

    path = quote_generator.generate(tmp_settings, fake_client, force=False, day=day)

    assert path is not None
    assert path.exists()
    assert path.name == "2026-08-15.md"
    assert "Daily Quote" in path.read_text()
    assert len(fake_client.calls) == 1


def test_quote_generator_skips_duplicate(tmp_settings):
    fake_client = FakeGeminiClient("content")
    day = date(2026, 8, 15)

    first = quote_generator.generate(tmp_settings, fake_client, force=False, day=day)
    second = quote_generator.generate(tmp_settings, fake_client, force=False, day=day)

    assert first is not None
    assert second is None
    assert len(fake_client.calls) == 1  # second call never hit the API


def test_quote_generator_force_regenerates(tmp_settings):
    fake_client = FakeGeminiClient("content")
    day = date(2026, 8, 15)

    quote_generator.generate(tmp_settings, fake_client, force=False, day=day)
    second = quote_generator.generate(tmp_settings, fake_client, force=True, day=day)

    assert second is not None
    assert len(fake_client.calls) == 2


def test_insight_generator_writes_file(tmp_settings):
    fake_client = FakeGeminiClient("# Developer Insight\n\n## Topic\n\nCaching\n")
    day = date(2026, 8, 15)

    path = insight_generator.generate(tmp_settings, fake_client, force=False, day=day)

    assert path is not None
    assert "Developer Insight" in path.read_text()


def test_news_generator_writes_file_with_mocked_articles(tmp_settings):
    fake_client = FakeGeminiClient("# Tech Update\n\n## Headline\n\nSomething happened\n")
    day = date(2026, 8, 15)

    fake_articles = [
        Article(
            title="Big AI release",
            summary="A company released something.",
            link="https://example.com/a1",
            source="Example News",
            published=None,
        )
    ]

    with patch("src.content.news_generator.fetch_recent_articles", return_value=fake_articles) as mock_fetch:
        path = news_generator.generate(tmp_settings, fake_client, force=False, day=day)

    mock_fetch.assert_called_once()
    assert path is not None
    assert "Tech Update" in path.read_text()
    assert "Big AI release" in fake_client.calls[0]  # article title was included in the prompt


def test_news_generator_propagates_rss_error(tmp_settings):
    from src.news.rss_reader import RSSError

    fake_client = FakeGeminiClient("content")
    day = date(2026, 8, 15)

    with patch("src.content.news_generator.fetch_recent_articles", side_effect=RSSError("no feeds")):
        try:
            news_generator.generate(tmp_settings, fake_client, force=False, day=day)
            assert False, "expected RSSError to propagate"
        except RSSError:
            pass
