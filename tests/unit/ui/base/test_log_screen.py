from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from textual.widgets import Checkbox

from termux_tasker.ui.base.log_screen import InotifyWatcher, LogScreen, PollWatcher


class TestLogScreenInit:
    def test_stores_string_content(self) -> None:
        screen = LogScreen(content="hello world")
        assert screen.content == "hello world"

    def test_stores_path_content(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path)
        assert screen.content == path

    def test_show_follow_enabled_for_path(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path, show_follow=True)
        assert screen.show_follow is True

    def test_show_follow_disabled_for_string(self) -> None:
        screen = LogScreen(content="test", show_follow=True)
        assert screen.show_follow is False

    def test_soft_wrap_defaults_to_false(self) -> None:
        screen = LogScreen(content="test")
        assert screen.soft_wrap is False

    def test_soft_wrap_custom_value(self) -> None:
        screen = LogScreen(content="test", soft_wrap=True)
        assert screen.soft_wrap is True

    def test_watcher_is_none_initially(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path)
        assert screen._watcher is None

    def test_timer_is_none_initially(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path)
        assert screen._timer is None

    def test_file_pos_starts_at_zero(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path)
        assert screen._file_pos == 0


class TestLogScreenFollow:
    def test_start_follow_creates_inotify_watcher(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path, show_follow=True)
        with (
            patch.object(InotifyWatcher, "__init__", return_value=None),
            patch.object(screen, "set_interval") as mock_set_interval,
            patch.object(screen, "query_one") as mock_query,
        ):
            screen._start_follow()
            assert isinstance(screen._watcher, InotifyWatcher)
            mock_set_interval.assert_called_once_with(1.0, screen._update_log_from_file)
            mock_query.assert_called_once_with("#follow_checkbox", Checkbox)

    def test_start_follow_falls_back_to_poll_on_oserror(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path, show_follow=True)
        with (
            patch.object(InotifyWatcher, "__init__", side_effect=OSError("no inotify")),
            patch.object(screen, "set_interval") as mock_set_interval,
            patch.object(screen, "query_one") as mock_query,
        ):
            screen._start_follow()
            assert isinstance(screen._watcher, PollWatcher)
            mock_set_interval.assert_called_once()
            mock_query.assert_called_once_with("#follow_checkbox", Checkbox)

    def test_start_follow_skipped_for_non_path_content(self) -> None:
        screen = LogScreen(content="string content", show_follow=True)
        with patch.object(screen, "set_interval") as mock_set_interval:
            screen._start_follow()
            assert screen._watcher is None
            mock_set_interval.assert_not_called()

    def test_stop_follow_closes_watcher_and_stops_timer(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path)
        mock_timer = MagicMock()
        mock_watcher = MagicMock()
        screen._timer = mock_timer
        screen._watcher = mock_watcher
        screen._stop_follow()
        mock_watcher.close.assert_called_once()
        mock_timer.stop.assert_called_once()
        assert screen._timer is None
        assert screen._watcher is None

    def test_stop_follow_handles_none_timer_and_watcher(self) -> None:
        screen = LogScreen(content="test")
        screen._timer = None
        screen._watcher = None
        screen._stop_follow()

    def test_on_follow_changed_checked_starts_follow(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path, show_follow=True)
        mock_event = MagicMock()
        mock_event.value = True
        with patch.object(screen, "_start_follow") as mock_start:
            screen.on_follow_changed(mock_event)
            mock_start.assert_called_once()

    def test_on_follow_changed_unchecked_stops_follow(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path, show_follow=True)
        mock_event = MagicMock()
        mock_event.value = False
        with patch.object(screen, "_stop_follow") as mock_stop:
            screen.on_follow_changed(mock_event)
            mock_stop.assert_called_once()


class TestLogScreenReset:
    def test_reset_clears_file_pos(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("line 1\nline 2\n")
        screen = LogScreen(content=path)
        screen._file_pos = 5
        with patch.object(screen, "query_one") as mock_query:
            screen.on_reset(MagicMock())
        assert screen._file_pos == path.stat().st_size

    def test_reset_skipped_for_non_path_content(self) -> None:
        screen = LogScreen(content="test")
        screen._file_pos = 5
        screen.on_reset(MagicMock())
        assert screen._file_pos == 5


class TestLogScreenClose:
    def test_on_close_stops_follow_and_dismisses(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path, show_follow=True)
        mock_event = MagicMock()
        with (
            patch.object(screen, "_stop_follow") as mock_stop,
            patch.object(screen, "dismiss") as mock_dismiss,
        ):
            screen.on_close(mock_event)
            mock_event.stop.assert_called_once()
            mock_stop.assert_called_once()
            mock_dismiss.assert_called_once_with(None)

    def test_action_close_stops_follow_and_dismisses(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path, show_follow=True)
        with (
            patch.object(screen, "_stop_follow") as mock_stop,
            patch.object(screen, "dismiss") as mock_dismiss,
        ):
            screen.action_close()
            mock_stop.assert_called_once()
            mock_dismiss.assert_called_once_with(None)
