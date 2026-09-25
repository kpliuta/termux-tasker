from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


def format_compact_duration(total_seconds: int) -> str:
    """Format seconds with minimal width: ``23``, ``01:23`` or ``01:00:21``."""
    clamped = max(0, int(total_seconds))
    if clamped < 60:
        return f"{clamped}"
    minutes, seconds = divmod(clamped, 60)
    if minutes < 60:
        return f"{minutes:02d}:{seconds:02d}"
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_optional(
    value: T | None,
    format_fn: Callable[[Any], str] | None = None,
    none_label: str = "n/a",
) -> str | T:
    """Format an optional value, e.g. ``format_optional(time, format_compact_duration)``.

    Returns ``none_label`` when the value is missing, calls ``format_fn``
    on it otherwise, or returns the value as-is when no formatter is given.
    """
    if value is None:
        return none_label
    if format_fn is None:
        return value
    return format_fn(value)
