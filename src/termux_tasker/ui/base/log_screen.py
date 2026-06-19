from __future__ import annotations

import ctypes
import os
import select
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, RichLog


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


# ── LogScreen ───────────────────────────────────────────────────────────


class LogScreen(ModalScreen[None]):
    """A modal screen for displaying logs with an optional 'follow' feature.

    When follow mode is enabled (via a Checkbox), a file watcher polls
    for new content and appends it to the RichLog widget. Uses inotify
    when available, with a smart-polling fallback.
    Tracks ``_file_pos`` to read incrementally.

    The Follow checkbox label shows which watcher is active:
    ``Follow (i)`` for inotify, ``Follow (p)`` for polling,
    or ``Follow`` (no tag) when follow is off.
    """

    CSS = """
LogScreen {
    align: center middle;
}

#log_dialog {
    width: 90%;
    height: 90%;
    border: tall $primary;
    background: $surface;
}

RichLog {
    height: 1fr;
    border: tall $panel;
    padding-left: 1;
}

#log_controls {
    height: auto;
    align: right middle;
    padding-top: 1;
}

#log_controls Button {
    width: 1fr;
    margin: 0 2;
}
"""
    BINDINGS = [("escape", "close", "Close")]

    def __init__(
            self,
            content: str | Path = "",
            show_follow: bool = False,
            soft_wrap: bool = False,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.content = content
        self.show_follow = show_follow and isinstance(content, Path)
        self.soft_wrap = soft_wrap
        self._timer: Any = None
        self._file_pos = 0
        self._watcher: FileWatcher | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="log_dialog"):
            yield RichLog(highlight=True, markup=False, wrap=self.soft_wrap)
            with Horizontal(id="log_controls"):
                yield Checkbox("Wrap", id="wrap_checkbox", value=self.soft_wrap)
                if self.show_follow:
                    yield Checkbox("Follow", id="follow_checkbox")
                    yield Button("Reset", id="reset_button", variant="default")
                yield Button("Close", id="close_button", variant="primary")

    def on_mount(self) -> None:
        self._load_content()

    def _load_content(self) -> None:
        log = self.query_one(RichLog)
        if isinstance(self.content, Path):
            if self.content.exists():
                with open(self.content, "rb") as f:
                    data = f.read()
                    log.write(data.decode(errors="replace").rstrip("\n"))
                    self._file_pos = f.tell()
            else:
                log.write(f"File not found: {self.content}")
        else:
            log.write(self.content)

    def _start_follow(self) -> None:
        if isinstance(self.content, Path):
            try:
                self._watcher = InotifyWatcher(self.content)
                tag = "(i)"
            except OSError:
                self._watcher = PollWatcher(self.content)
                tag = "(p)"
            self._timer = self.set_interval(1.0, self._update_log_from_file)
            cb = self.query_one("#follow_checkbox", Checkbox)
            cb.label = f"Follow {tag}"

    def _stop_follow(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None
        if self._watcher:
            self._watcher.close()
            self._watcher = None
        try:
            cb = self.query_one("#follow_checkbox", Checkbox)
            cb.label = "Follow"
        except Exception:
            pass

    @on(Checkbox.Changed, "#follow_checkbox")
    def on_follow_changed(self, event: Checkbox.Changed) -> None:
        if event.value:
            self._start_follow()
        else:
            self._stop_follow()

    @on(Checkbox.Changed, "#wrap_checkbox")
    def on_wrap_changed(self, event: Checkbox.Changed) -> None:
        event.stop()
        self.soft_wrap = event.value
        log = self.query_one(RichLog)
        log.wrap = event.value
        log.clear()
        self._load_content()

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

    @on(Button.Pressed, "#reset_button")
    def on_reset(self, event: Button.Pressed) -> None:
        event.stop()
        if isinstance(self.content, Path) and self.content.exists():
            self._file_pos = self.content.stat().st_size
            self.query_one(RichLog).clear()

    @on(Button.Pressed, "#close_button")
    def on_close(self, event: Button.Pressed) -> None:
        event.stop()
        self._stop_follow()
        self.dismiss(None)

    def action_close(self) -> None:
        self._stop_follow()
        self.dismiss(None)
