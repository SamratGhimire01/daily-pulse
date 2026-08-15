from __future__ import annotations

import random
from datetime import date

import pytest

from src.scheduler.scheduler import build_today_schedule, pick_run_time


def test_pick_run_time_within_window():
    rng = random.Random(42)
    day = date(2026, 8, 15)
    for _ in range(50):
        run_at = pick_run_time("07:00", "08:00", day, rng=rng)
        assert run_at.date() == day
        assert (7, 0) <= (run_at.hour, run_at.minute) <= (8, 0)


def test_pick_run_time_invalid_window_raises():
    day = date(2026, 8, 15)
    with pytest.raises(ValueError):
        pick_run_time("09:00", "08:00", day)


def test_build_today_schedule_respects_enabled_flag(tmp_settings):
    tmp_settings.raw["schedule"]["afternoon"]["enabled"] = False
    day = date(2026, 8, 15)

    runs = build_today_schedule(tmp_settings, day)
    slots = [r.slot for r in runs]

    assert "morning" in slots
    assert "evening" in slots
    assert "afternoon" not in slots


def test_build_today_schedule_sorted_by_time(tmp_settings):
    day = date(2026, 8, 15)
    runs = build_today_schedule(tmp_settings, day)
    times = [r.run_at for r in runs]
    assert times == sorted(times)
