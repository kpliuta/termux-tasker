from __future__ import annotations


def parse_timeout(timeout_str: str) -> int:
    """Parse a ``30s``/``5m``/``1h`` timeout into seconds; 60 when malformed."""
    if timeout_str.endswith("h"):
        return int(timeout_str[:-1]) * 3600
    elif timeout_str.endswith("m"):
        return int(timeout_str[:-1]) * 60
    elif timeout_str.endswith("s"):
        return int(timeout_str[:-1])
    return 60
