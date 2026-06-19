from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from termux_tasker.ui.base.log_screen import FileWatcher, InotifyWatcher, PollWatcher


class TestFileWatcherABC:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            FileWatcher()  # type: ignore[abstract]


class TestPollWatcher:
    def test_poll_returns_false_on_unchanged_file(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("line 1\n")
        watcher = PollWatcher(path)
        assert watcher.poll() is False

    def test_poll_returns_true_when_file_grows(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("line 1\n")
        watcher = PollWatcher(path)
        path.write_text("line 1\nline 2\n")
        assert watcher.poll() is True

    def test_poll_stays_false_after_growth_detected(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("line 1\n")
        watcher = PollWatcher(path)
        path.write_text("line 1\nline 2\n")
        watcher.poll()
        assert watcher.poll() is False

    def test_poll_returns_false_when_file_shrinks(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("line 1\nline 2\n")
        watcher = PollWatcher(path)
        path.write_text("line 1\n")
        assert watcher.poll() is False

    def test_poll_returns_false_when_file_deleted(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("line 1\n")
        watcher = PollWatcher(path)
        path.unlink()
        assert watcher.poll() is False

    def test_poll_returns_true_after_regrowth(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("line 1\n")
        watcher = PollWatcher(path)
        path.write_text("line 1\nline 2\n")
        watcher.poll()
        path.write_text("line 1\nline 2\nline 3\n")
        assert watcher.poll() is True

    def test_close_does_not_raise(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("content")
        watcher = PollWatcher(path)
        watcher.close()


class TestInotifyWatcher:
    def test_init_failure_raises_oserror(self) -> None:
        mock_libc = MagicMock()
        mock_libc.inotify_init.return_value = -1
        with patch("termux_tasker.ui.base.log_screen.ctypes.CDLL") as mock_cdll:
            mock_cdll.return_value = mock_libc
            with pytest.raises(OSError, match="inotify_init failed"):
                InotifyWatcher(Path("/tmp/test.log"))

    def test_poll_returns_true_on_event(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("line 1\n")
        mock_poll = MagicMock()
        mock_poll.poll.return_value = [(3, 1)]
        mock_libc = MagicMock()
        mock_libc.inotify_init.return_value = 3
        with (
            patch("termux_tasker.ui.base.log_screen.ctypes.CDLL") as mock_cdll,
            patch("termux_tasker.ui.base.log_screen.select.poll") as mock_poll_cls,
            patch("termux_tasker.ui.base.log_screen.os.read") as mock_read,
        ):
            mock_cdll.return_value = mock_libc
            mock_poll_cls.return_value = mock_poll
            watcher = InotifyWatcher(path)
            result = watcher.poll()
            assert result is True
            mock_read.assert_called_once_with(3, 4096)

    def test_poll_returns_false_without_events(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("line 1\n")
        mock_poll = MagicMock()
        mock_poll.poll.return_value = []
        mock_libc = MagicMock()
        mock_libc.inotify_init.return_value = 3
        with (
            patch("termux_tasker.ui.base.log_screen.ctypes.CDLL") as mock_cdll,
            patch("termux_tasker.ui.base.log_screen.select.poll") as mock_poll_cls,
        ):
            mock_cdll.return_value = mock_libc
            mock_poll_cls.return_value = mock_poll
            watcher = InotifyWatcher(path)
            result = watcher.poll()
            assert result is False

    def test_close_cleans_up_resources(self, tmp_dir: Path) -> None:
        path = tmp_dir / "test.log"
        path.write_text("line 1\n")
        mock_poll = MagicMock()
        mock_libc = MagicMock()
        mock_libc.inotify_init.return_value = 3
        with (
            patch("termux_tasker.ui.base.log_screen.ctypes.CDLL") as mock_cdll,
            patch("termux_tasker.ui.base.log_screen.select.poll") as mock_poll_cls,
            patch("termux_tasker.ui.base.log_screen.os.close") as mock_close,
        ):
            mock_cdll.return_value = mock_libc
            mock_poll_cls.return_value = mock_poll
            watcher = InotifyWatcher(path)
            watcher.close()
            mock_poll.unregister.assert_called_once_with(3)
            mock_libc.inotify_rm_watch.assert_called_once()
            mock_close.assert_called_once_with(3)
