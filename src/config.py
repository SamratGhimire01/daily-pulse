"""Loads configuration from config/settings.yaml (non-secret) and .env (secrets).

Keeping these separate means settings.yaml is safe to commit, while .env
(which holds API keys and tokens) is git-ignored.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.yaml"


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


@dataclass
class Settings:
    """Typed view over the merged YAML + environment configuration."""

    raw: dict[str, Any]
    gemini_api_key: str | None
    github_repo_url: str | None
    github_token: str | None
    git_author_name: str
    git_author_email: str

    @property
    def project_name(self) -> str:
        return self.raw.get("project", {}).get("name", "DailyPulse")

    @property
    def ai_model(self) -> str:
        return self.raw.get("ai", {}).get("model", "gemini-2.5-flash")

    @property
    def max_words(self) -> int:
        return int(self.raw.get("content", {}).get("max_words", 400))

    @property
    def quotes_dir(self) -> Path:
        return PROJECT_ROOT / self.raw.get("content", {}).get("quotes_dir", "content/quotes")

    @property
    def news_dir(self) -> Path:
        return PROJECT_ROOT / self.raw.get("content", {}).get("news_dir", "content/news")

    @property
    def insights_dir(self) -> Path:
        return PROJECT_ROOT / self.raw.get("content", {}).get("insights_dir", "content/insights")

    @property
    def github_branch(self) -> str:
        return self.raw.get("github", {}).get("branch", "main")

    @property
    def news_feeds(self) -> list[str]:
        return list(self.raw.get("news", {}).get("feeds", []))

    @property
    def news_max_articles(self) -> int:
        return int(self.raw.get("news", {}).get("max_articles", 3))

    def schedule_window(self, slot: str) -> dict[str, Any]:
        windows = self.raw.get("schedule", {})
        if slot not in windows:
            raise ConfigError(f"Unknown schedule slot '{slot}'. Expected one of {list(windows)}.")
        return windows[slot]

    def require_gemini_api_key(self) -> str:
        if not self.gemini_api_key:
            raise ConfigError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key "
                "from https://aistudio.google.com/app/apikey"
            )
        return self.gemini_api_key


def load_settings(
    settings_path: Path | str = DEFAULT_SETTINGS_PATH,
    env_path: Path | str | None = None,
) -> Settings:
    """Load YAML settings and .env secrets into a single Settings object.

    Never raises just because secrets are missing — that's only checked
    lazily (require_gemini_api_key) so that commands like config validation
    or dry runs can work without an API key.
    """
    settings_path = Path(settings_path)
    if not settings_path.exists():
        raise ConfigError(f"Settings file not found: {settings_path}")

    with settings_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    if env_path is not None:
        load_dotenv(dotenv_path=env_path, override=False)
    else:
        load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)

    return Settings(
        raw=raw,
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        github_repo_url=os.getenv("GITHUB_REPO_URL") or None,
        github_token=os.getenv("GITHUB_TOKEN") or None,
        git_author_name=os.getenv("GIT_AUTHOR_NAME", "DailyPulse Bot"),
        git_author_email=os.getenv("GIT_AUTHOR_EMAIL", "dailypulse-bot@users.noreply.github.com"),
    )
