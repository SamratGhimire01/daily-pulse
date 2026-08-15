from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.ai.gemini_client import GeminiClient, GeminiError


def _fake_genai_module(response_text="Hello from Gemini"):
    fake_client_instance = MagicMock()
    fake_client_instance.models.generate_content.return_value = SimpleNamespace(text=response_text)

    fake_genai_module = MagicMock()
    fake_genai_module.Client.return_value = fake_client_instance
    return fake_genai_module, fake_client_instance


def test_missing_api_key_raises():
    with pytest.raises(GeminiError):
        GeminiClient(api_key="", model="gemini-2.5-flash")


def test_generate_returns_text():
    fake_module, fake_instance = _fake_genai_module("A generated quote.")

    with patch.dict("sys.modules", {"google": MagicMock(genai=fake_module), "google.genai": fake_module}):
        client = GeminiClient(api_key="fake-key", model="gemini-2.5-flash")
        result = client.generate("Give me a quote")

    assert result == "A generated quote."
    fake_instance.models.generate_content.assert_called_once()


def test_generate_raises_on_empty_response():
    fake_module, fake_instance = _fake_genai_module("")

    with patch.dict("sys.modules", {"google": MagicMock(genai=fake_module), "google.genai": fake_module}):
        client = GeminiClient(api_key="fake-key", model="gemini-2.5-flash")
        with pytest.raises(GeminiError):
            client.generate("Give me a quote")


def test_generate_wraps_api_exceptions():
    fake_module = MagicMock()
    fake_instance = MagicMock()
    fake_instance.models.generate_content.side_effect = RuntimeError("rate limited")
    fake_module.Client.return_value = fake_instance

    with patch.dict("sys.modules", {"google": MagicMock(genai=fake_module), "google.genai": fake_module}):
        client = GeminiClient(api_key="fake-key", model="gemini-2.5-flash")
        with pytest.raises(GeminiError):
            client.generate("Give me a quote")
