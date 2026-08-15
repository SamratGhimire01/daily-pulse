from __future__ import annotations

from datetime import date

from src.utils.helpers import (
    already_exists,
    content_filename,
    ensure_dir,
    today_str,
    truncate_to_words,
)


def test_today_str_format():
    d = date(2026, 8, 15)
    assert today_str(d) == "2026-08-15"


def test_content_filename(tmp_path):
    d = date(2026, 8, 15)
    path = content_filename(tmp_path, d)
    assert path == tmp_path / "2026-08-15.md"


def test_already_exists_false_when_missing(tmp_path):
    d = date(2026, 8, 15)
    assert already_exists(tmp_path, d) is False


def test_already_exists_true_when_present(tmp_path):
    d = date(2026, 8, 15)
    (tmp_path / "2026-08-15.md").write_text("hello")
    assert already_exists(tmp_path, d) is True


def test_truncate_to_words_no_op_when_short():
    text = "one two three"
    assert truncate_to_words(text, 10) == text


def test_truncate_to_words_truncates():
    text = " ".join(str(i) for i in range(20))
    result = truncate_to_words(text, 5)
    assert result.startswith("0 1 2 3 4")
    assert result.endswith("…")


def test_ensure_dir_creates_nested(tmp_path):
    target = tmp_path / "a" / "b" / "c"
    ensure_dir(target)
    assert target.exists()
