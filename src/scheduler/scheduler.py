"""Lightweight local scheduler.

For local/manual use only. In production, prefer a systemd timer, cron,
or GitHub Actions scheduled workflow (see deployment/ and .github/workflows/)
rather than keeping this process running 24/7.

Picks a random execution time inside each configured window per day, and
tracks which (date, slot) pairs have already run so restarts don't
duplicate a run within the same day.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from src.utils.logger import get_logger

logger = get_logger(__name__)

SLOTS = ("morning", "afternoon", "evening")


@dataclass
class ScheduledRun:
    slot: str
    run_at: datetime


def _parse_hhmm(value: str, on_day: date) -> datetime:
    hour, minute = (int(p) for p in value.split(":"))
    return datetime(on_day.year, on_day.month, on_day.day, hour, minute)


def pick_run_time(start: str, end: str, on_day: date, rng: random.Random | None = None) -> datetime:
    """Pick a random datetime within [start, end) on the given day."""
    rng = rng or random
    start_dt = _parse_hhmm(start, on_day)
    end_dt = _parse_hhmm(end, on_day)
    if end_dt <= start_dt:
        raise ValueError(f"Window end ({end}) must be after start ({start}).")
    delta_seconds = int((end_dt - start_dt).total_seconds())
    offset = rng.randint(0, delta_seconds)
    return start_dt + timedelta(seconds=offset)


def build_today_schedule(settings, on_day: date | None = None) -> list[ScheduledRun]:
    """Build today's randomized run times for every enabled slot."""
    on_day = on_day or date.today()
    runs: list[ScheduledRun] = []
    for slot in SLOTS:
        window = settings.schedule_window(slot)
        if not window.get("enabled", True):
            continue
        run_at = pick_run_time(window["start"], window["end"], on_day)
        runs.append(ScheduledRun(slot=slot, run_at=run_at))
    return sorted(runs, key=lambda r: r.run_at)


def run_forever(settings, job_fn, poll_seconds: int = 30) -> None:
    """Run job_fn(slot) at a randomized time inside each window, every day.

    job_fn is responsible for its own duplicate-prevention (the content
    generators already skip if today's file exists), so a restart or a
    missed/late tick is safe.
    """
    completed_today: set[tuple[date, str]] = set()
    current_day = date.today()
    todays_runs = build_today_schedule(settings, current_day)
    logger.info("Today's schedule: %s", [(r.slot, r.run_at.strftime("%H:%M:%S")) for r in todays_runs])

    while True:
        now = datetime.now()

        if now.date() != current_day:
            current_day = now.date()
            todays_runs = build_today_schedule(settings, current_day)
            logger.info(
                "New day — rebuilt schedule: %s",
                [(r.slot, r.run_at.strftime("%H:%M:%S")) for r in todays_runs],
            )

        for run in todays_runs:
            key = (current_day, run.slot)
            if key in completed_today:
                continue
            if now >= run.run_at:
                logger.info("Triggering scheduled '%s' run.", run.slot)
                try:
                    job_fn(run.slot)
                except Exception as exc:  # noqa: BLE001 - never let one bad run kill the loop
                    logger.error("Scheduled run for '%s' failed: %s", run.slot, exc)
                completed_today.add(key)

        time.sleep(poll_seconds)
