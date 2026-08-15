"""DailyPulse CLI entry point.

Usage:
    python -m src.main --type quote
    python -m src.main --type news
    python -m src.main --type insight
    python -m src.main --test
    python -m src.main --force --type quote
    python -m src.main --schedule   # run the local randomized scheduler loop
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from src.ai.gemini_client import GeminiClient, GeminiError
from src.config import ConfigError, PROJECT_ROOT, load_settings
from src.content import insight_generator, news_generator, quote_generator
from src.github.git_manager import GitManager, GitManagerError
from src.news.rss_reader import RSSError
from src.scheduler.scheduler import run_forever
from src.utils.helpers import content_filename
from src.utils.logger import get_logger

logger = get_logger(__name__)

CONTENT_DIR_ATTR = {
    "quote": "quotes_dir",
    "news": "news_dir",
    "insight": "insights_dir",
}

GENERATORS = {
    "quote": quote_generator,
    "news": news_generator,
    "insight": insight_generator,
}

COMMIT_PREFIXES = {
    "quote": "docs: add daily quote",
    "news": "news: add technology digest",
    "insight": "insight: add developer insight",
}

SLOT_TO_TYPE = {
    "morning": "quote",
    "afternoon": "news",
    "evening": "insight",
}


def run_type(content_type: str, force: bool, test_mode: bool, day: date | None = None) -> int:
    """Run a single generator. Returns a process exit code (0 = success)."""
    if content_type not in GENERATORS:
        logger.error("Unknown content type '%s'. Expected one of %s.", content_type, list(GENERATORS))
        return 1

    try:
        settings = load_settings()
    except ConfigError as exc:
        logger.error("Configuration error: %s", exc)
        return 1

    logger.info("Starting %s generation%s", content_type, " (test mode)" if test_mode else "")

    try:
        api_key = settings.require_gemini_api_key()
        client = GeminiClient(api_key=api_key, model=settings.ai_model)
    except (ConfigError, GeminiError) as exc:
        logger.error("Cannot initialize Gemini client: %s", exc)
        return 1

    module = GENERATORS[content_type]
    try:
        path = module.generate(settings, client, force=force, day=day)
    except GeminiError as exc:
        logger.error("Gemini generation failed: %s", exc)
        return 1
    except RSSError as exc:
        logger.error("News retrieval failed: %s", exc)
        return 1
    except Exception as exc:  # noqa: BLE001 - final safety net, never a raw traceback for ops
        logger.error("Unexpected error during %s generation: %s", content_type, exc)
        return 1

    if path is None:
        # Generation was skipped because today's post already exists (duplicate
        # prevention already logged why). That file might still be sitting there
        # uncommitted though — e.g. created by an earlier --test run — so fall
        # back to it and continue on to the git step instead of exiting early.
        directory = getattr(settings, CONTENT_DIR_ATTR[content_type])
        path = content_filename(directory, day)
        if not path.exists():
            logger.error("Expected existing file not found at %s", path)
            return 1
        logger.info("Reusing already-generated file: %s", path)

    if test_mode:
        logger.info("Test mode: skipping git commit/push. File left at %s", path)
        return 0

    try:
        git_manager = GitManager(
            repo_path=PROJECT_ROOT,
            author_name=settings.git_author_name,
            author_email=settings.git_author_email,
        )
        message = f"{COMMIT_PREFIXES[content_type]} - {path.stem}"
        git_manager.commit_and_push(path, message=message, branch=settings.github_branch, push=True)
    except GitManagerError as exc:
        logger.error("Git operation failed: %s", exc)
        return 1

    logger.info("Done.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DailyPulse — automated AI daily content generator.")
    parser.add_argument("--type", choices=list(GENERATORS), help="Which content type to generate.")
    parser.add_argument("--force", action="store_true", help="Regenerate even if today's post already exists.")
    parser.add_argument("--test", action="store_true", help="Generate content without committing/pushing to git.")
    parser.add_argument("--schedule", action="store_true", help="Run the local randomized scheduler loop.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.schedule:
        try:
            settings = load_settings()
        except ConfigError as exc:
            logger.error("Configuration error: %s", exc)
            return 1

        def job(slot: str) -> None:
            run_type(SLOT_TO_TYPE[slot], force=False, test_mode=False)

        logger.info("Starting DailyPulse local scheduler. Press Ctrl+C to stop.")
        run_forever(settings, job)
        return 0

    if not args.type:
        parser.error("--type is required unless --schedule is used.")

    return run_type(args.type, force=args.force, test_mode=args.test)


if __name__ == "__main__":
    sys.exit(main())
