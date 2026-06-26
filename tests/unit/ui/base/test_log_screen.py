from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

from textual.screen import ModalScreen

from termux_tasker.ui.base.log_screen import (
    InotifyWatcher,
    LogHelpScreen,
    LogScreen,
    LogSettingsScreen,
    PollWatcher,
)
from termux_tasker.ui.base import ConfirmationScreen


class TestLogScreenInit:
    def test_stores_string_content(self) -> None:
        screen = LogScreen(content="hello world")
        assert screen.content == "hello world"

    def test_stores_path_content(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path)
        assert screen.content == path

    def test_is_dynamic_enabled_for_path(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path, is_dynamic=True)
        assert screen.is_dynamic is True

    def test_is_dynamic_disabled_for_string(self) -> None:
        screen = LogScreen(content="test", is_dynamic=True)
        assert screen.is_dynamic is False

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

    def test_file_pos_custom_value(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path, offset=42)
        assert screen._file_pos == 42

    def test_auto_scroll_defaults_to_false(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path, is_dynamic=True)
        assert screen.auto_scroll is False

    def test_auto_scroll_custom_value(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path, is_dynamic=True, auto_scroll=True)
        assert screen.auto_scroll is True

    def test_auto_scroll_forced_false_when_not_dynamic(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path, is_dynamic=False, auto_scroll=True)
        assert screen.auto_scroll is False

    def test_on_settings_changed_is_none_by_default(self) -> None:
        screen = LogScreen(content="test")
        assert screen._on_settings_changed is None

    def test_on_settings_changed_called_on_notify(self) -> None:
        mock = MagicMock()
        screen = LogScreen(content="test", on_settings_changed=mock)
        screen._notify_settings_changed()
        mock.assert_called_once_with(False, False, 0)

    def test_on_settings_changed_notify_with_persisted_offset(self) -> None:
        mock = MagicMock()
        screen = LogScreen(content="test", on_settings_changed=mock)
        screen._persisted_offset = 42
        screen._notify_settings_changed()
        mock.assert_called_once_with(False, False, 42)


class TestLogScreenFollow:
    def test_start_follow_moves_file_pos_to_end(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")  # 7 bytes
        screen = LogScreen(content=path, is_dynamic=True)
        screen._file_pos = 0
        with (
            patch.object(InotifyWatcher, "__init__", return_value=None),
            patch.object(screen, "set_interval") as mock_set_interval,
        ):
            screen._start_follow()
            assert screen._file_pos == 7
            mock_set_interval.assert_called_once()

    def test_start_follow_creates_inotify_watcher(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path, is_dynamic=True)
        with (
            patch.object(InotifyWatcher, "__init__", return_value=None),
            patch.object(screen, "set_interval") as mock_set_interval,
        ):
            screen._start_follow()
            assert isinstance(screen._watcher, InotifyWatcher)
            mock_set_interval.assert_called_once_with(1.0, screen._update_log_from_file)

    def test_start_follow_falls_back_to_poll_on_oserror(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path, is_dynamic=True)
        with (
            patch.object(InotifyWatcher, "__init__", side_effect=OSError("no inotify")),
            patch.object(screen, "set_interval") as mock_set_interval,
        ):
            screen._start_follow()
            assert isinstance(screen._watcher, PollWatcher)
            mock_set_interval.assert_called_once()

    def test_start_follow_skipped_for_non_path_content(self) -> None:
        screen = LogScreen(content="string content", is_dynamic=True)
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


class TestLogScreenClose:
    def test_on_close_stops_follow_and_dismisses(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path, is_dynamic=True)
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
        screen = LogScreen(content=path, is_dynamic=True)
        with (
            patch.object(screen, "_stop_follow") as mock_stop,
            patch.object(screen, "dismiss") as mock_dismiss,
        ):
            screen.action_close()
            mock_stop.assert_called_once()
            mock_dismiss.assert_called_once_with(None)


class TestLogSettingsScreenReset:
    def test_on_reset_notifies_with_offset_zero(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("some log content\nmore content\n")
        log_screen = LogScreen(content=path, is_dynamic=True, offset=100)
        settings_screen = LogSettingsScreen(log_screen)
        mock_app = MagicMock()
        with (
            patch.object(ModalScreen, "app", new_callable=PropertyMock, return_value=mock_app),
            patch.object(log_screen, "_stop_follow"),
            patch.object(log_screen, "_load_content"),
        ):
            mock_callback = MagicMock()
            log_screen._on_settings_changed = mock_callback
            mock_event = MagicMock()
            with (
                patch.object(settings_screen, "query_one") as mock_settings_query,
                patch.object(log_screen, "query_one") as mock_log_query,
            ):
                mock_log_query.return_value = MagicMock()
                mock_settings_query.return_value = MagicMock()
                settings_screen.on_reset(mock_event)
        mock_callback.assert_called_once_with(False, False, 0)


class TestLogSettingsScreenWrap:
    def test_on_wrap_changed_preserves_persisted_offset(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("some log content\n")
        log_screen = LogScreen(content=path, is_dynamic=True, offset=100)
        settings_screen = LogSettingsScreen(log_screen)
        log_screen._file_pos = 200
        mock_callback = MagicMock()
        log_screen._on_settings_changed = mock_callback
        mock_event = MagicMock()
        mock_event.value = True
        with (
            patch.object(log_screen, "query_one") as mock_query_one,
            patch.object(log_screen, "_load_content"),
        ):
            mock_query_one.return_value = MagicMock()
            settings_screen.on_wrap_changed(mock_event)
        mock_callback.assert_called_once_with(True, False, 100)
        assert log_screen._persisted_offset == 100


class TestLogSettingsScreenClearLogFile:
    def test_on_clear_log_file_shows_confirmation(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        log_screen = LogScreen(content=path, is_dynamic=True)
        settings_screen = LogSettingsScreen(log_screen)
        mock_app = MagicMock()
        with (
            patch.object(ModalScreen, "app", new_callable=PropertyMock, return_value=mock_app),
        ):
            mock_event = MagicMock()
            settings_screen.on_clear_log_file(mock_event)
        mock_event.stop.assert_called_once()
        mock_app.push_screen.assert_called_once()
        args, _ = mock_app.push_screen.call_args
        assert isinstance(args[0], ConfirmationScreen)

    def test_on_clear_log_file_cancel_does_not_truncate(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content to preserve")
        log_screen = LogScreen(content=path, is_dynamic=True)
        settings_screen = LogSettingsScreen(log_screen)
        mock_app = MagicMock()
        with patch.object(ModalScreen, "app", new_callable=PropertyMock, return_value=mock_app):
            mock_event = MagicMock()
            settings_screen.on_clear_log_file(mock_event)
            callback = mock_app.push_screen.call_args[0][1]
            callback(None)
        assert path.read_text() == "content to preserve"

    def test_on_clear_log_file_confirm_truncates_and_notifies(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content to delete")
        log_screen = LogScreen(content=path, is_dynamic=True)
        settings_screen = LogSettingsScreen(log_screen)
        mock_app = MagicMock()
        with (
            patch.object(ModalScreen, "app", new_callable=PropertyMock, return_value=mock_app),
            patch.object(log_screen, "query_one") as mock_query_one,
            patch.object(log_screen, "_notify_settings_changed") as mock_notify,
        ):
            mock_query_one.return_value = MagicMock()
            mock_event = MagicMock()
            settings_screen.on_clear_log_file(mock_event)
            callback = mock_app.push_screen.call_args[0][1]
            callback("delete_button")
        assert path.read_text() == ""
        assert log_screen._file_pos == 0
        mock_notify.assert_called_once()

    def test_on_clear_log_file_skipped_when_not_a_path(self) -> None:
        log_screen = LogScreen(content="string content")
        settings_screen = LogSettingsScreen(log_screen)
        mock_app = MagicMock()
        with patch.object(ModalScreen, "app", new_callable=PropertyMock, return_value=mock_app):
            mock_event = MagicMock()
            settings_screen.on_clear_log_file(mock_event)
        mock_event.stop.assert_called_once()
        mock_app.push_screen.assert_not_called()


class TestLogHelpScreen:
    def test_on_close_stops_event_and_dismisses(self) -> None:
        screen = LogHelpScreen()
        mock_event = MagicMock()
        with patch.object(screen, "dismiss") as mock_dismiss:
            screen.on_close(mock_event)
        mock_event.stop.assert_called_once()
        mock_dismiss.assert_called_once_with(None)

    def test_action_close_dismisses(self) -> None:
        screen = LogHelpScreen()
        with patch.object(screen, "dismiss") as mock_dismiss:
            screen.action_close()
        mock_dismiss.assert_called_once_with(None)


class TestLogSettingsScreenAutoScroll:
    def test_enable_reads_gap_content(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("line1\nline2\nline3\n")
        log_screen = LogScreen(content=path, is_dynamic=True)
        settings_screen = LogSettingsScreen(log_screen)
        log_screen._file_pos = 6
        mock_callback = MagicMock()
        log_screen._on_settings_changed = mock_callback
        mock_event = MagicMock()
        mock_event.value = True
        mock_log = MagicMock()
        with (
            patch.object(log_screen, "query_one", return_value=mock_log),
            patch.object(log_screen, "_start_follow") as mock_start,
        ):
            settings_screen.on_auto_scroll_changed(mock_event)
        mock_log.write.assert_called_once_with("line2\nline3")
        mock_start.assert_called_once()
        mock_callback.assert_called_once()

    def test_enable_without_gap_does_not_read(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("line1\n")
        log_screen = LogScreen(content=path, is_dynamic=True)
        settings_screen = LogSettingsScreen(log_screen)
        log_screen._file_pos = path.stat().st_size
        mock_callback = MagicMock()
        log_screen._on_settings_changed = mock_callback
        mock_event = MagicMock()
        mock_event.value = True
        mock_log = MagicMock()
        with (
            patch.object(log_screen, "query_one", return_value=mock_log),
            patch.object(log_screen, "_start_follow") as mock_start,
        ):
            settings_screen.on_auto_scroll_changed(mock_event)
        mock_log.write.assert_not_called()
        mock_start.assert_called_once()

    def test_disable_stops_follow(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        log_screen = LogScreen(content=path, is_dynamic=True)
        settings_screen = LogSettingsScreen(log_screen)
        mock_callback = MagicMock()
        log_screen._on_settings_changed = mock_callback
        mock_event = MagicMock()
        mock_event.value = False
        with patch.object(log_screen, "_stop_follow") as mock_stop:
            settings_screen.on_auto_scroll_changed(mock_event)
        mock_stop.assert_called_once()
        mock_callback.assert_called_once()

    def test_enable_for_missing_file_skips_gap(self, tmp_dir: Path) -> None:
        path = tmp_dir / "missing.log"
        log_screen = LogScreen(content=path, is_dynamic=True)
        settings_screen = LogSettingsScreen(log_screen)
        mock_event = MagicMock()
        mock_event.value = True
        with patch.object(log_screen, "_start_follow") as mock_start:
            settings_screen.on_auto_scroll_changed(mock_event)
        mock_start.assert_called_once()

    def test_enable_for_string_content_skips_gap(self) -> None:
        log_screen = LogScreen(content="string content", is_dynamic=True)
        settings_screen = LogSettingsScreen(log_screen)
        mock_event = MagicMock()
        mock_event.value = True
        with patch.object(log_screen, "_start_follow") as mock_start:
            settings_screen.on_auto_scroll_changed(mock_event)
        mock_start.assert_called_once()


class TestLogSettingsScreenClearScreen:
    def test_moves_position_to_end(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("line1\nline2\n")
        log_screen = LogScreen(content=path, is_dynamic=True)
        settings_screen = LogSettingsScreen(log_screen)
        log_screen._file_pos = 3
        log_screen._persisted_offset = 3
        mock_event = MagicMock()
        mock_log = MagicMock()
        with (
            patch.object(log_screen, "query_one", return_value=mock_log),
            patch.object(log_screen, "_notify_settings_changed") as mock_notify,
        ):
            settings_screen.on_clear_screen(mock_event)
        assert log_screen._file_pos == path.stat().st_size
        assert log_screen._persisted_offset == path.stat().st_size
        mock_log.clear.assert_called_once()
        mock_notify.assert_called_once()

    def test_skipped_for_non_path_content(self) -> None:
        log_screen = LogScreen(content="string content", is_dynamic=True)
        settings_screen = LogSettingsScreen(log_screen)
        mock_event = MagicMock()
        with patch.object(log_screen, "_notify_settings_changed") as mock_notify:
            settings_screen.on_clear_screen(mock_event)
        mock_notify.assert_not_called()


class TestLogSettingsScreenHelp:
    def test_on_help_pushes_help_screen(self) -> None:
        log_screen = LogScreen(content="test", is_dynamic=True)
        settings_screen = LogSettingsScreen(log_screen)
        mock_event = MagicMock()
        mock_app = MagicMock()
        with patch.object(ModalScreen, "app", new_callable=PropertyMock, return_value=mock_app):
            settings_screen.on_help(mock_event)
        mock_event.stop.assert_called_once()
        mock_app.push_screen.assert_called_once()
        args, _ = mock_app.push_screen.call_args
        assert isinstance(args[0], LogHelpScreen)


class TestLogSettingsScreenClose:
    def test_on_close_dismisses(self) -> None:
        log_screen = LogScreen(content="test")
        settings_screen = LogSettingsScreen(log_screen)
        mock_event = MagicMock()
        with patch.object(settings_screen, "dismiss") as mock_dismiss:
            settings_screen.on_close(mock_event)
        mock_event.stop.assert_called_once()
        mock_dismiss.assert_called_once_with(None)

    def test_action_close_dismisses(self) -> None:
        log_screen = LogScreen(content="test")
        settings_screen = LogSettingsScreen(log_screen)
        with patch.object(settings_screen, "dismiss") as mock_dismiss:
            settings_screen.action_close()
        mock_dismiss.assert_called_once_with(None)


class TestLogScreenMount:
    def test_on_mount_loads_content(self) -> None:
        screen = LogScreen(content="test")
        with (
            patch.object(screen, "_load_content") as mock_load,
            patch.object(screen, "_start_follow"),
        ):
            screen.on_mount()
        mock_load.assert_called_once()

    def test_on_mount_starts_follow_whenauto_scroll(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path, is_dynamic=True, auto_scroll=True)
        with (
            patch.object(screen, "_load_content"),
            patch.object(screen, "_start_follow") as mock_start,
        ):
            screen.on_mount()
        mock_start.assert_called_once()

    def test_on_mount_does_not_start_follow_withoutauto_scroll(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path, is_dynamic=True, auto_scroll=False)
        with (
            patch.object(screen, "_load_content"),
            patch.object(screen, "_start_follow") as mock_start,
        ):
            screen.on_mount()
        mock_start.assert_not_called()


class TestLogScreenLoadContent:
    def test_loads_from_file_pos(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("line1\nline2\nline3\n")
        screen = LogScreen(content=path)
        screen._file_pos = 6
        mock_log = MagicMock()
        with patch.object(screen, "query_one", return_value=mock_log):
            screen._load_content()
        mock_log.write.assert_called_once_with("line2\nline3")
        assert screen._file_pos == path.stat().st_size

    def test_loads_all_from_offset_zero(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("full content")
        screen = LogScreen(content=path)
        screen._file_pos = 0
        mock_log = MagicMock()
        with patch.object(screen, "query_one", return_value=mock_log):
            screen._load_content()
        mock_log.write.assert_called_once_with("full content")

    def test_file_not_found_shows_message(self, tmp_dir: Path) -> None:
        path = tmp_dir / "nonexistent.log"
        screen = LogScreen(content=path)
        mock_log = MagicMock()
        with patch.object(screen, "query_one", return_value=mock_log):
            screen._load_content()
        mock_log.write.assert_called_once_with(f"File not found: {path}")

    def test_string_content_writes_directly(self) -> None:
        screen = LogScreen(content="hello world")
        mock_log = MagicMock()
        with patch.object(screen, "query_one", return_value=mock_log):
            screen._load_content()
        mock_log.write.assert_called_once_with("hello world")


class TestLogScreenSettings:
    def test_on_settings_pushes_settings_screen(self) -> None:
        screen = LogScreen(content="test")
        mock_event = MagicMock()
        mock_app = MagicMock()
        with patch.object(ModalScreen, "app", new_callable=PropertyMock, return_value=mock_app):
            screen.on_settings(mock_event)
        mock_event.stop.assert_called_once()
        mock_app.push_screen.assert_called_once()
        args, _ = mock_app.push_screen.call_args
        assert isinstance(args[0], LogSettingsScreen)


class TestLogScreenUpdateLog:
    def test_update_when_watcher_reports_change(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path)
        mock_watcher = MagicMock()
        mock_watcher.poll.return_value = True
        screen._watcher = mock_watcher
        with patch.object(screen, "_read_new_content") as mock_read:
            screen._update_log_from_file()
        mock_read.assert_called_once()

    def test_update_when_watcher_reports_no_change(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path)
        mock_watcher = MagicMock()
        mock_watcher.poll.return_value = False
        screen._watcher = mock_watcher
        with patch.object(screen, "_read_new_content") as mock_read:
            screen._update_log_from_file()
        mock_read.assert_not_called()

    def test_update_when_no_watcher(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path)
        screen._watcher = None
        with patch.object(screen, "_read_new_content") as mock_read:
            screen._update_log_from_file()
        mock_read.assert_not_called()


class TestLogScreenReadNewContent:
    def test_reads_new_content_from_file_pos(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("line1\n")
        screen = LogScreen(content=path)
        screen._file_pos = path.stat().st_size
        with open(path, "a") as f:
            f.write("line2\n")
        mock_log = MagicMock()
        with patch.object(screen, "query_one", return_value=mock_log):
            screen._read_new_content()
        mock_log.write.assert_called_once_with("line2")
        assert screen._file_pos == path.stat().st_size

    def test_no_new_content_does_nothing(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        screen = LogScreen(content=path)
        screen._file_pos = path.stat().st_size
        mock_log = MagicMock()
        with patch.object(screen, "query_one", return_value=mock_log):
            screen._read_new_content()
        mock_log.write.assert_not_called()

    def test_skipped_for_non_path_content(self) -> None:
        screen = LogScreen(content="string content")
        screen._read_new_content()  # should not raise
