from __future__ import annotations

from termux_tasker._parse import parse_timeout  # noqa


class TestParseTimeout:
    def test_hours(self) -> None:
        assert parse_timeout("2h") == 7200

    def test_minutes(self) -> None:
        assert parse_timeout("30m") == 1800

    def test_seconds(self) -> None:
        assert parse_timeout("45s") == 45

    def test_default(self) -> None:
        assert parse_timeout("invalid") == 60
