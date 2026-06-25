from __future__ import annotations

import ctypes
import os
import select
from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, RichLog, Static

from termux_tasker.ui.base.screen import ConfirmationScreen

_HERE = Path(__file__).parent

_HELP_TEXT = """
Word Wrap: When enabled, long lines wrap to fit the viewing area.
When disabled, horizontal scrolling is needed.

Auto-scroll: When enabled, new content is automatically loaded
as it is written to the file. Useful for monitoring live output.

Clear Screen: Clears the displayed content and moves the read
position to the end of the file. New content continues to appear
if Auto-scroll is on.

Reset: Resets all settings (Word Wrap, Auto-scroll) to their
default values and clears the display.

Clear Log File: Permanently erases all content from the log file
on disk. This action cannot be undone.
"""


# ── File watchers ───────────────────────────────────────────────────────


class FileWatcher(ABC):
    """Abstract base for file change detection."""

    @abstractmethod
    def poll(self) -> bool:
        """Check for changes without blocking."""

    @abstractmethod
    def close(self) -> None:
        """Release resources."""


class InotifyWatcher(FileWatcher):
    """Linux inotify-based file watcher — zero-polling kernel notifications."""

    _IN_MODIFY = 0x00000002

    def __init__(self, path: Path) -> None:
        self._libc = ctypes.CDLL("libc.so.6", use_errno=True)
        self._fd = self._libc.inotify_init()
        if self._fd < 0:
            raise OSError("inotify_init failed")
        self._wd = self._libc.inotify_add_watch(
            self._fd, os.fsencode(path), self._IN_MODIFY
        )
        self._poll = select.poll()
        self._poll.register(self._fd, select.POLLIN)

    def poll(self) -> bool:
        events = self._poll.poll(0)
        if events:
            for fd, _ in events:
                try:
                    os.read(fd, 4096)
                except BlockingIOError:
                    pass
            return True
        return False

    def close(self) -> None:
        self._poll.unregister(self._fd)
        self._libc.inotify_rm_watch(self._fd, self._wd)
        os.close(self._fd)


class PollWatcher(FileWatcher):
    """Smart polling watcher — only reads when file size has grown."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._last_size = path.stat().st_size if path.exists() else 0

    def poll(self) -> bool:
        if not self._path.exists():
            return False
        current = self._path.stat().st_size
        if current > self._last_size:
            self._last_size = current
            return True
        return False

    def close(self) -> None:
        pass


# ── Log Help Screen ─────────────────────────────────────────────────────


class LogHelpScreen(ModalScreen[None]):
    """Modal with user-friendly descriptions of each setting."""

    CSS_PATH = _HERE / "tcss" / "log_help_screen.tcss"
    BINDINGS = [("escape", "close", "Close")]

    def compose(self) -> ComposeResult:
        with Vertical(id="log_help_dialog"):
            with Vertical(id="log_help_text_container"):
                yield Static(_HELP_TEXT, id="log_help_text")
            with Horizontal(id="log_help_close"):
                yield Button("Close", id="close_button", variant="primary")

    @on(Button.Pressed, "#close_button")
    def on_close(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss(None)

    def action_close(self) -> None:
        self.dismiss(None)


# ── Log Settings Screen ─────────────────────────────────────────────────


class LogSettingsScreen(ModalScreen[None]):
    """Modal screen for LogScreen settings.

    Provides checkboxes/buttons that modify the parent LogScreen state
    immediately and notify the caller via the on_settings_changed callback.
    """

    CSS_PATH = _HERE / "tcss" / "log_settings_screen.tcss"
    BINDINGS = [("escape", "close", "Close")]

    def __init__(self, log_screen: LogScreen) -> None:
        super().__init__()
        self._log_screen = log_screen

    def compose(self) -> ComposeResult:
        ls = self._log_screen
        with Vertical(id="log_settings_dialog"):
            with Vertical(id="settings_scrollable"):
                yield Checkbox("Word Wrap", id="wrap_checkbox", value=ls.soft_wrap)
                if ls.is_dynamic:
                    yield Checkbox("Auto-scroll", id="auto_scroll_checkbox", value=ls.auto_scroll)
                    yield Button("Clear Screen", id="clear_screen_button", variant="default")
                    yield Button("Reset", id="reset_button", variant="default")
                    yield Button("Clear Log File", id="clear_log_file_button", variant="error", disabled=not ls.clear_log_file_enabled)
            with Horizontal(id="help_close_row"):
                if ls.is_dynamic:
                    yield Button("Help", id="help_button", variant="default")
                yield Button("Close", id="close_button", variant="primary")

    @on(Checkbox.Changed, "#wrap_checkbox")
    def on_wrap_changed(self, event: Checkbox.Changed) -> None:
        event.stop()
        ls = self._log_screen
        ls.soft_wrap = event.value
        log = ls.query_one(RichLog)
        log.wrap = event.value
        log.clear()
        ls.reload_content()

    @on(Checkbox.Changed, "#auto_scroll_checkbox")
    def on_auto_scroll_changed(self, event: Checkbox.Changed) -> None:
        event.stop()
        ls = self._log_screen
        if event.value:
            ls.enable_auto_scroll()
        else:
            ls.disable_auto_scroll()

    @on(Button.Pressed, "#clear_screen_button")
    def on_clear_screen(self, event: Button.Pressed) -> None:
        event.stop()
        self._log_screen.clear_display()

    @on(Button.Pressed, "#reset_button")
    def on_reset(self, event: Button.Pressed) -> None:
        event.stop()
        ls = self._log_screen
        ls.reset_all()
        self.query_one("#wrap_checkbox", Checkbox).value = False
        if ls.is_dynamic:
            self.query_one("#auto_scroll_checkbox", Checkbox).value = False

    @on(Button.Pressed, "#clear_log_file_button")
    def on_clear_log_file(self, event: Button.Pressed) -> None:
        event.stop()
        ls = self._log_screen
        if not ls.clear_log_file_enabled:
            return
        if not isinstance(ls.content, Path) or not ls.content.exists():
            return

        def _on_confirm(result: str | None) -> None:
            if result is None:
                return
            ls.clear_log_file_on_disk()

        self.app.push_screen(
            ConfirmationScreen(
                message="Permanently erase all content from the log file?\nThis action cannot be undone.",
                ok_button_text="Delete",
                ok_button_id="delete_button",
            ),
            _on_confirm,
        )

    @on(Button.Pressed, "#help_button")
    def on_help(self, event: Button.Pressed) -> None:
        event.stop()
        self.app.push_screen(LogHelpScreen())

    @on(Button.Pressed, "#close_button")
    def on_close(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss(None)

    def action_close(self) -> None:
        self.dismiss(None)


# ── LogScreen ───────────────────────────────────────────────────────────


class LogScreen(ModalScreen[None]):
    """A modal screen for displaying log file contents.

    Shows a RichLog widget with a Settings and Close button bar below it.
    When *is_dynamic* is True, the Settings modal provides additional
    controls (Auto-scroll, Clear Screen, Reset, Clear Log File).

    The caller can pass *on_settings_changed* to be notified whenever
    the user modifies settings (soft_wrap, auto_scroll, file_pos).
    Initial values for *auto_scroll* and *file_pos* can be provided to
    restore previously persisted state.
    """

    CSS_PATH = _HERE / "tcss" / "log_screen.tcss"
    BINDINGS = [("escape", "close", "Close")]

    def __init__(
            self,
            content: str | Path = "",
            is_dynamic: bool = False,
            soft_wrap: bool = False,
            auto_scroll: bool = False,
            offset: int = 0,
            clear_log_file_enabled: bool = True,
            on_settings_changed: Callable[[bool, bool, int], None] | None = None,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.content = content
        self.is_dynamic = is_dynamic and isinstance(content, Path)
        self.soft_wrap = soft_wrap
        self.clear_log_file_enabled = clear_log_file_enabled
        self._timer: Any = None
        self._file_pos = offset
        self._persisted_offset = offset
        self._watcher: FileWatcher | None = None
        self.auto_scroll = auto_scroll if self.is_dynamic else False
        self._on_settings_changed = on_settings_changed

    def reload_content(self) -> None:
        """Re-read content from the persisted offset (after wrap toggle)."""
        if isinstance(self.content, Path):
            self._file_pos = self._persisted_offset
        self._load_content()
        self._notify_settings_changed()

    def enable_auto_scroll(self) -> None:
        """Read gap content, start following the file, and notify."""
        self.auto_scroll = True
        if isinstance(self.content, Path) and self.content.exists():
            current_size = self.content.stat().st_size
            if current_size > self._file_pos:
                log = self.query_one(RichLog)
                with open(self.content, "rb") as f:
                    f.seek(self._file_pos)
                    data = f.read()
                    if data:
                        log.write(data.decode(errors="replace").rstrip("\n"))
        self._start_follow()
        self._notify_settings_changed()

    def disable_auto_scroll(self) -> None:
        """Stop following the file and notify."""
        self.auto_scroll = False
        self._stop_follow()
        self._notify_settings_changed()

    def clear_display(self) -> None:
        """Move read position to end of file, clear view, and notify."""
        if isinstance(self.content, Path) and self.content.exists():
            size = self.content.stat().st_size
            self._file_pos = size
            self._persisted_offset = size
            self.query_one(RichLog).clear()
            self._notify_settings_changed()

    def reset_all(self) -> None:
        """Reset all settings and view to defaults, then notify."""
        self.soft_wrap = False
        self.auto_scroll = False
        self._stop_follow()
        log = self.query_one(RichLog)
        log.wrap = False
        log.clear()
        self._persisted_offset = 0
        self._file_pos = 0
        self._load_content()
        self._notify_settings_changed()
        self._file_pos = 0

    def clear_log_file_on_disk(self) -> None:
        """Truncate the log file and reset read state, then notify."""
        self.content.write_text("")  # type: ignore[union-attr]
        self._file_pos = 0
        self._persisted_offset = 0
        self.query_one(RichLog).clear()
        self._notify_settings_changed()

    def _notify_settings_changed(self) -> None:
        if self._on_settings_changed:
            self._on_settings_changed(self.soft_wrap, self.auto_scroll, self._persisted_offset)

    def compose(self) -> ComposeResult:
        with Vertical(id="log_dialog"):
            yield RichLog(highlight=True, markup=False, wrap=self.soft_wrap)
            with Horizontal(id="log_controls"):
                yield Button("Settings", id="settings_button", variant="default")
                yield Button("Close", id="close_button", variant="primary")

    def on_mount(self) -> None:
        self._load_content()
        if self.auto_scroll:
            self._start_follow()

    def _load_content(self) -> None:
        log = self.query_one(RichLog)
        if isinstance(self.content, Path):
            if self.content.exists():
                with open(self.content, "rb") as f:
                    f.seek(self._file_pos)
                    data = f.read()
                    log.write(data.decode(errors="replace").rstrip("\n"))
                    self._file_pos = f.tell()
            else:
                log.write(f"File not found: {self.content}")
        else:
            log.write(self.content)

    def _start_follow(self) -> None:
        if isinstance(self.content, Path) and self.content.exists():
            self._file_pos = self.content.stat().st_size
            try:
                self._watcher = InotifyWatcher(self.content)
            except OSError:
                self._watcher = PollWatcher(self.content)
            self._timer = self.set_interval(1.0, self._update_log_from_file)

    def _stop_follow(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None
        if self._watcher:
            self._watcher.close()
            self._watcher = None

    @on(Button.Pressed, "#settings_button")
    def on_settings(self, event: Button.Pressed) -> None:
        event.stop()
        self.app.push_screen(LogSettingsScreen(self))

    @on(Button.Pressed, "#close_button")
    def on_close(self, event: Button.Pressed) -> None:
        event.stop()
        self._stop_follow()
        self.dismiss(None)

    def action_close(self) -> None:
        self._stop_follow()
        self.dismiss(None)

    def _update_log_from_file(self) -> None:
        if self._watcher and self._watcher.poll():
            self._read_new_content()

    def _read_new_content(self) -> None:
        if isinstance(self.content, Path) and self.content.exists():
            log = self.query_one(RichLog)
            with open(self.content, "rb") as f:
                f.seek(self._file_pos)
                data = f.read()
                self._file_pos = f.tell()
            if data:
                log.write(data.decode(errors="replace").rstrip("\n"))
