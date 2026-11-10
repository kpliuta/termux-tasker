from __future__ import annotations

from datetime import datetime, timezone

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

_NEVER_RUN = "none"


def parse_timeout(timeout_str: str) -> int:
    """Parse a ``30s``/``5m``/``1h`` timeout into seconds; 60 when malformed.

    Total: never raises on bad input (unknown suffix, non-numeric value,
    empty string, or a non-string).
    """
    try:
        if timeout_str.endswith("h"):
            return int(timeout_str[:-1]) * 3600
        elif timeout_str.endswith("m"):
            return int(timeout_str[:-1]) * 60
        elif timeout_str.endswith("s"):
            return int(timeout_str[:-1])
    except (ValueError, AttributeError, TypeError):
        return 60
    return 60


def parse_timestamp(last_run: str) -> datetime | None:
    """Parse a UTC file timestamp; None when never run or malformed."""
    if last_run == _NEVER_RUN:
        return None
    try:
        return datetime.strptime(last_run, TIMESTAMP_FORMAT).replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None
