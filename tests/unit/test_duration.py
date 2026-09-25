from __future__ import annotations

import pytest

from termux_tasker.ui.screens._format import format_compact_duration, format_optional   # noqa


@pytest.mark.parametrize(
    "seconds,expected",
    [
        (0, "0"),
        (1, "1"),
        (23, "23"),
        (31, "31"),
        (59, "59"),
        (60, "01:00"),
        (83, "01:23"),
        (105, "01:45"),
        (1293, "21:33"),
        (3599, "59:59"),
        (3600, "01:00:00"),
        (3721, "01:02:01"),
        (36021, "10:00:21"),
    ],
)
def test_format_compact_duration(seconds: int, expected: str) -> None:
    assert format_compact_duration(seconds) == expected


def test_format_compact_duration_clamps_negative() -> None:
    assert format_compact_duration(-5) == "0"


def test_format_optional_applies_formatter() -> None:
    assert format_optional(93, format_compact_duration) == "01:33"


def test_format_optional_none_uses_label() -> None:
    assert format_optional(None, format_compact_duration) == "n/a"


def test_format_optional_custom_none_label() -> None:
    assert format_optional(None, format_compact_duration, none_label="—") == "—"


def test_format_optional_without_formatter_returns_value() -> None:
    assert format_optional("ready") == "ready"
    assert format_optional(None) == "n/a"
