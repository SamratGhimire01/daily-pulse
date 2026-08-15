"""Simple, consistent logging for DailyPulse.

Deliberately does not log anything from environment variables or config
sections that might hold secrets (API keys, tokens).
"""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def get_logger(name: str = "daily_pulse") -> logging.Logger:
    global _CONFIGURED

    if not _CONFIGURED:
        handler = logging.StreamHandler(stream=sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        # Attach to the real root logger so every module logger (each named
        # after its own __name__, e.g. "src.main", "src.content.quote_generator")
        # propagates up to it and actually gets printed.
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(handler)
        _CONFIGURED = True

    return logging.getLogger(name)