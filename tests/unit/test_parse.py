from __future__ import annotations

from datetime import datetime, timezone

from termux_tasker._format import format_timestamp  # noqa
from termux_tasker._parse import (  # noqa
    TIMESTAMP_FORMAT,
    parse_timeout,
    parse_timestamp,
)


class TestParseTimeout:
    def test_hours(self) -> None:
        assert parse_timeout("2h") == 7200

    def test_minutes(self) -> None:
        assert parse_timeout("30m") == 1800

    def test_seconds(self) -> None:
        assert parse_timeout("45s") == 45

    def test_default(self) -> None:
        assert parse_timeout("invalid") == 60

    def test_malformed_suffix_falls_back(self) -> None:
        assert parse_timeout("bogus") == 60
        assert parse_timeout("10x") == 60
        assert parse_timeout("3d") == 60
        assert parse_timeout("") == 60

    def test_zero_is_valid(self) -> None:
        assert parse_timeout("0s") == 0


class TestParseTimestamp:
    def test_round_trip(self) -> None:
        now = datetime.now(timezone.utc)
        parsed = parse_timestamp(format_timestamp(now))
        assert parsed is not None
        assert parsed.strftime(TIMESTAMP_FORMAT) == now.strftime(TIMESTAMP_FORMAT)
        assert parsed.tzinfo == timezone.utc

    def test_none_sentinel(self) -> None:
        assert parse_timestamp("none") is None

    def test_garbage_is_none(self) -> None:
        assert parse_timestamp("not-a-timestamp") is None
        assert parse_timestamp("") is None
