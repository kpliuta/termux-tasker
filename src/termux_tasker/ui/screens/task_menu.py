from __future__ import annotations

import asyncio
import re
import shutil
from pathlib import Path
from typing import Any

from textual import on
from textual.content import Content
from textual.widgets import Button

from termux_tasker.config import RunnerSettings, TaskMetadata, TaskSettings
from termux_tasker.runner_process import RunnerProcess
from termux_tasker.ui.base.log_screen import LogScreen
from termux_tasker.ui.base import (
    ButtonConfig,
    ButtonLayout,
    MenuScreen,
    LoadingScreen,
    ConfirmationScreen,
    FileBrowserScreen,
)
from termux_tasker._parse import parse_timeout
from termux_tasker.ui.screens._format import format_compact_duration, format_optional
from termux_tasker.ui.screens._state_colors import TASK_STATE_COLORS
from termux_tasker.ui.screens._utils import (
    termux_app,
    copy_to_tmp,
)
from termux_tasker.ui.screens._ui_utils import ask_validated_input, go_home
from termux_tasker.ui.screens.properties import PropertiesScreen
from termux_tasker.ui.screens.widgets.description import (
    KeyValueEntry,
    StateEntry,
    StateWidget,
)

_TIMEOUT_RE = re.compile(r"^[0-9]+[hms]$")

_STOPPED_STYLE = "$text-warning"


def build_task_key_value_entries(
    meta: TaskMetadata,
    settings: TaskSettings,
) -> tuple[KeyValueEntry, ...]:
    """Top description rows: version, enabled flag, timeout, last run/status."""
    last_run = settings.session.last_run
    last_status = settings.session.last_run_status
    return (
        KeyValueEntry("Version", meta.general.version),
        KeyValueEntry("Enabled", str(settings.general.enabled)),
        KeyValueEntry("Timeout", settings.general.timeout or "(not set)"),
        KeyValueEntry("Last Run", last_run if last_run != "none" else "n/a"),
        KeyValueEntry("Last Status", last_status if last_status != "none" else "n/a"),
    )


def task_phase_durations(
    settings: TaskSettings,
) -> tuple[int | None, int | None, int | None]:
    """This task's before-task / task-exec / after-task durations."""
    session = settings.session
    return (
        session.last_run_before_duration,
        session.last_run_exec_duration,
        session.last_run_after_duration,
    )


def build_task_suffixes(
    current_state: str,
    phase_durations: tuple[int | None, int | None, int | None],
    elapsed_sec: int | None,
    idle_remaining: int | None,
) -> dict[str, Content]:
    """Per-state suffixes for the task lifecycle list.

    ``stopped`` shows the parent runner's idle countdown (visible only
    while the runner is idle). ``running`` shows the summed task-phase
    durations plus the live elapsed time when the task is executing.
    """
    suffixes: dict[str, Content] = {}
    if current_state == "stopped" and idle_remaining is not None:
        suffixes["stopped"] = Content.assemble(
            (f"[{format_compact_duration(idle_remaining)}]", f"bold {_STOPPED_STYLE}")
        )
    if current_state == "running":
        last = format_optional(
            sum(value or 0 for value in phase_durations), format_compact_duration
        )
        if elapsed_sec is None:
            suffixes["running"] = Content.assemble(
                (f"[{last}]", "$foreground-disabled")
            )
        else:
            suffixes["running"] = Content.assemble(
                (f"[{last}]", "$foreground-disabled"),
                (f"[{format_compact_duration(elapsed_sec)}]", "bold $text-success"),
            )
    return suffixes


class TaskMenuScreen(MenuScreen):
    _TASK_STATES: tuple[StateEntry, ...] = (
        StateEntry("stopped", "stopped", color=TASK_STATE_COLORS["stopped"]),
        StateEntry("running", "running"),
    )

    def __init__(self, task_path: Path) -> None:
        self.task_path = task_path
        self.runner_path = task_path.parent.parent
        meta = TaskMetadata.load(task_path / "metadata.toml")
        settings = TaskSettings.load(task_path / "settings.toml")

        self._fix_session(settings, task_path)
        self._state = StateWidget(
            id="description-widget",
            key_value_entries=build_task_key_value_entries(meta, settings),
            current_state=settings.session.state,
            states_entries=self._TASK_STATES,
            state_suffixes=build_task_suffixes(
                current_state=settings.session.state,
                phase_durations=task_phase_durations(settings),
                elapsed_sec=None,
                idle_remaining=None,
            ),
        )
        items = self._build_items(meta, settings)

        super().__init__(items, description_widget=self._state, show_home_button=True, show_back_button=True)
        self.title = "Task"
        self.sub_title = meta.general.name
        self._poll_timer: Any = None

    def on_mount(self) -> None:
        self._poll_state()
        self._start_polling()

    def on_unmount(self) -> None:
        self._stop_polling()

    def _start_polling(self) -> None:
        settings = TaskSettings.load(self.task_path / "settings.toml")
        if settings.general.enabled:
            self._poll_timer = self.set_interval(1.0, self._poll_state)

    def _stop_polling(self) -> None:
        if self._poll_timer is not None:
            self._poll_timer.stop()
            self._poll_timer = None

    def _poll_state(self) -> None:
        meta = TaskMetadata.load(self.task_path / "metadata.toml")
        settings = TaskSettings.load(self.task_path / "settings.toml")
        if not settings.general.enabled:
            self._stop_polling()
        self._refresh_ui(meta, settings)

    def _refresh_ui(
        self, meta: TaskMetadata, settings: TaskSettings
    ) -> None:
        self.menu_items = self._build_items(meta, settings)
        self._state.key_value_entries = build_task_key_value_entries(meta, settings)
        self._state.current_state = settings.session.state
        self._state.state_suffixes = self._build_suffixes(settings)

    def _runner_id(self) -> str:
        meta = TaskMetadata.load(self.task_path / "metadata.toml")
        return meta.general.runner_id

    def _live_runner_proc(self) -> RunnerProcess | None:
        """Parent runner's live process, if the runner is currently running."""
        app = termux_app(self)
        return app.state.runners.get(self._runner_id())

    def _build_suffixes(self, settings: TaskSettings) -> dict[str, Content]:
        """Assemble timer suffixes from persisted + live task/runner data."""
        current_state = settings.session.state
        elapsed_sec: int | None = None
        idle_remaining: int | None = None
        proc = self._live_runner_proc()
        if proc is not None:
            if current_state == "running" and proc.current_task_path == self.task_path:
                elapsed_sec = proc.state_elapsed()
            runner_settings = RunnerSettings.load(self.runner_path / "settings.toml")
            if runner_settings.session.state == "idle" and settings.general.enabled:
                idle_remaining = max(
                    0, parse_timeout(runner_settings.general.timeout) - proc.state_elapsed()
                )
        return build_task_suffixes(
            current_state=current_state,
            phase_durations=task_phase_durations(settings),
            elapsed_sec=elapsed_sec,
            idle_remaining=idle_remaining,
        )

    def _fix_session(self, settings: TaskSettings, task_path: Path) -> None:
        """Reset stale session state on app restart.

        If the recorded session_id doesn't match the current app session,
        force the task to "stopped".  This prevents tasks from being stuck
        in a "running" state after an app restart or crash.
        """
        app = termux_app(self) if hasattr(self, "app") else None
        if app and settings.session.session_id != app.state.session_id:
            settings.session.state = "stopped"
        if app:
            settings.session.session_id = app.state.session_id
            settings.save(task_path / "settings.toml")

    def _build_items(
        self, meta: TaskMetadata, settings: TaskSettings
    ) -> list[ButtonConfig]:
        items: list[ButtonConfig] = []
        toggle_label = "Disable" if settings.general.enabled else "Enable"
        items.append(ButtonConfig("toggle", toggle_label, variant="warning"))
        items.append(ButtonConfig("properties", "Properties"))
        items.append(ButtonConfig("timeout", "Set Timeout"))
        items.append(ButtonConfig("show_metadata", "Show metadata.toml"))
        items.append(ButtonConfig("show_settings", "Show settings.toml"))
        items.append(ButtonConfig("update", "Update", variant="primary", layout=ButtonLayout.BOTTOM))
        items.append(ButtonConfig("uninstall", "Uninstall", variant="error", layout=ButtonLayout.BOTTOM))
        output_dir = self.task_path / "output"
        if output_dir.exists():
            items.append(ButtonConfig("show_output", "Show output"))
        return items

    @on(Button.Pressed, "#toggle")
    def on_toggle(self, event: Button.Pressed) -> None:
        event.stop()
        settings = TaskSettings.load(self.task_path / "settings.toml")
        settings.general.enabled = not settings.general.enabled
        settings.save(self.task_path / "settings.toml")
        meta = TaskMetadata.load(self.task_path / "metadata.toml")
        settings = TaskSettings.load(self.task_path / "settings.toml")
        self._refresh_ui(meta, settings)
        if settings.general.enabled:
            self._start_polling()
        else:
            self._stop_polling()

    @on(Button.Pressed, "#properties")
    def on_properties(self, event: Button.Pressed) -> None:
        event.stop()
        meta = TaskMetadata.load(self.task_path / "metadata.toml")
        termux_app(self).push_screen(
            PropertiesScreen(
                self.task_path, meta.properties, meta.general.name, is_task=True
            )
        )

    @on(Button.Pressed, "#show_metadata")
    def on_show_metadata(self, event: Button.Pressed) -> None:
        event.stop()
        termux_app(self).push_screen(
            LogScreen(content=self.task_path / "metadata.toml")
        )

    @on(Button.Pressed, "#show_settings")
    def on_show_settings(self, event: Button.Pressed) -> None:
        event.stop()
        termux_app(self).push_screen(
            LogScreen(content=self.task_path / "settings.toml")
        )

    @on(Button.Pressed, "#show_output")
    def on_show_output(self, event: Button.Pressed) -> None:
        event.stop()
        output_dir = self.task_path / "output"
        termux_app(self).push_screen(
            FileBrowserScreen(path=output_dir, read_only=True, expand=True)
        )

    @on(Button.Pressed, "#timeout")
    def on_set_timeout(self, event: Button.Pressed) -> None:
        """Open timeout input with interactive validation.

        Delegates the prompt/validate/re-prompt loop to
        ``ask_validated_input``: empty or format-invalid values show a
        warning ``InfoScreen`` and re-prompt; a valid value is saved and
        the screen refreshed.
        """
        event.stop()

        def _on_valid(result: Any) -> None:
            val = str(result).strip()
            ts = TaskSettings.load(self.task_path / "settings.toml")
            ts.general.timeout = val
            ts.save(self.task_path / "settings.toml")
            meta = TaskMetadata.load(self.task_path / "metadata.toml")
            ts = TaskSettings.load(self.task_path / "settings.toml")
            self._refresh_ui(meta, ts)

        settings = TaskSettings.load(self.task_path / "settings.toml")
        ask_validated_input(
            termux_app(self),
            title="Timeout",
            input_type="text",
            current_value=settings.general.timeout,
            is_valid=lambda r: bool(_TIMEOUT_RE.match(str(r).strip())),
            on_valid=_on_valid,
            empty_message="Timeout is required and must have a value.",
            invalid_message="Invalid timeout format. Use e.g. 30s, 5m, 1h.",
        )

    @on(Button.Pressed, "#update")
    def on_update(self, event: Button.Pressed) -> None:
        event.stop()
        from termux_tasker.ui.screens.install_task_version import InstallTaskVersionScreen
        app = termux_app(self)
        tmp_folder = copy_to_tmp(self.task_path, app.state.tmp_dir, "task")
        app.state.register_tmp_task_folder(tmp_folder)
        termux_app(self).push_screen(
            InstallTaskVersionScreen(self.runner_path, tmp_folder)
        )

    @on(Button.Pressed, "#uninstall")
    def on_uninstall(self, event: Button.Pressed) -> None:
        event.stop()
        meta = TaskMetadata.load(self.task_path / "metadata.toml")

        async def on_confirm(result: str | None) -> None:
            if result is not None:
                await self._do_uninstall()

        termux_app(self).push_screen(
            ConfirmationScreen(
                message=(
                    f"Are you sure you want to uninstall {meta.general.name} task?"
                ),
                ok_button_text="Yes",
                cancel_button_text="No",
                ok_button_id="yes_uninstall",
            ),
            on_confirm,
        )

    async def _do_uninstall(self) -> None:
        loading = LoadingScreen("Awaiting task termination")
        await termux_app(self).push_screen(loading)

        while True:
            settings = TaskSettings.load(self.task_path / "settings.toml")
            if settings.session.state == "stopped":
                break
            await asyncio.sleep(0.5)

        await loading.dismiss(None)

        shutil.rmtree(self.task_path, ignore_errors=True)
        termux_app(self).pop_screen()   # noqa

    @on(Button.Pressed, "#home")
    def on_home_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        go_home(self)
