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
    logger = logging.getLogger(name)

    if not _CONFIGURED:
        handler = logging.StreamHandler(stream=sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        root = logging.getLogger("daily_pulse")
        root.setLevel(logging.INFO)
        root.addHandler(handler)
        root.propagate = False
        _CONFIGURED = True

    return logger
