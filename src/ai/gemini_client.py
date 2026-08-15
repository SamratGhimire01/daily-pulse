"""Thin wrapper around the Google Gen AI SDK (google-genai).

Uses the current recommended client: `from google import genai`.
Keeps retry/error-handling logic in one place so generators stay simple.
"""

from __future__ import annotations

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.utils.logger import get_logger

logger = get_logger(__name__)


class GeminiError(Exception):
    """Raised when the Gemini API cannot fulfil a request after retries."""


class GeminiClient:
    """Wraps google-genai's Client for simple text generation calls."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        if not api_key:
            raise GeminiError("Missing Gemini API key.")
        self.model = model
        try:
            # Imported lazily so the rest of the codebase (and tests) can
            # run without the google-genai package installed if needed.
            from google import genai

            self._client = genai.Client(api_key=api_key)
        except Exception as exc:  # pragma: no cover - import/env errors
            raise GeminiError(f"Failed to initialize Gemini client: {exc}") from exc

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
    )
    def _call(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        text = getattr(response, "text", None)
        if not text:
            raise GeminiError("Gemini returned an empty response.")
        return text.strip()

    def generate(self, prompt: str) -> str:
        """Generate text from a prompt, raising GeminiError on failure."""
        try:
            return self._call(prompt)
        except Exception as exc:
            logger.error("Gemini API call failed: %s", type(exc).__name__)
            raise GeminiError(f"Gemini API call failed: {exc}") from exc
