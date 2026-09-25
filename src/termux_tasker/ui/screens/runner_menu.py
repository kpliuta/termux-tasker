from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from textual import on
from textual.content import Content
from textual.widgets import Button

from termux_tasker import proc_stats
from termux_tasker.config import (
    RunnerMetadata,
    RunnerSessionInfo,
    RunnerSettings,
    TaskSessionInfo,
    TaskSettings,
)
from termux_tasker._parse import parse_timeout
from termux_tasker.runner_process import RunnerProcess
from termux_tasker.ui.base.log_screen import LogScreen
from termux_tasker.ui.base import (
    ButtonConfig,
    ButtonLayout,
    MenuScreen,
    LoadingScreen,
    ConfirmationScreen,
)
from termux_tasker.ui.screens._ui_utils import go_home
from termux_tasker.ui.screens._state_colors import RUNNER_STATE_COLORS
from termux_tasker.ui.screens._utils import (
    termux_app,
    copy_to_tmp,
)
from termux_tasker.ui.screens._format import format_compact_duration, format_optional
from termux_tasker.ui.screens.properties import PropertiesScreen
from termux_tasker.ui.screens.tasks_menu import TasksMenuScreen
from termux_tasker.ui.screens.widgets.description import (
    KeyValueEntry,
    StateEntry,
    StateWidget,
)


_DIM_STYLE = "$foreground-disabled"
_FALLBACK_STATE_STYLE = "$text-success"

_RUNNER_LAST_DURATION_ATTRS: dict[str, str] = {
    "initialization": "last_run_init_duration",
    "before-exec": "last_run_before_duration",
    "after-exec": "last_run_after_duration",
    "termination": "last_run_termination_duration",
}

_TASK_LAST_DURATION_ATTRS: dict[str, str] = {
    "before-task": "last_run_before_duration",
    "task-exec": "last_run_exec_duration",
    "after-task": "last_run_after_duration",
}

_EXEC_CHILD_STATES = ("before-task", "task-exec", "after-task")


def _timer_suffix(
    last_sec: int | None,
    elapsed_sec: int | None,
    dim_style: str,
    active_style: str,
) -> Content:
    """A ``[last][elapsed?]`` suffix with theme variable span styles.

    ``elapsed_sec=None`` renders the previous value only (inactive row).
    """
    if elapsed_sec is None:
        return Content.assemble((f"[{format_optional(last_sec, format_compact_duration)}]", dim_style))
    return Content.assemble(
        (f"[{format_optional(last_sec, format_compact_duration)}]", dim_style),
        (f"[{format_compact_duration(elapsed_sec)}]", f"bold {active_style}"),
    )


def _session_durations(
    session: RunnerSessionInfo | TaskSessionInfo,
    attrs: Mapping[str, str],
) -> dict[str, int | None]:
    """Pick previous-run durations for the given state ids."""
    durations: dict[str, int | None] = {}
    for state_id, attr in attrs.items():
        value = getattr(session, attr, None)
        durations[state_id] = value if isinstance(value, int) else None
    return durations


def _timed_row(
    last_sec: int | None,
    elapsed_sec: int | None,
    current_state: str,
    state_id: str,
) -> Content:
    """One ``[last][elapsed?]`` row; elapsed only when the row is active."""
    return _timer_suffix(
        last_sec,
        elapsed_sec if state_id == current_state else None,
        dim_style=_DIM_STYLE,
        active_style=RUNNER_STATE_COLORS.get(state_id, _FALLBACK_STATE_STYLE),
    )


def build_key_value_entries(
    meta: RunnerMetadata,
    settings: RunnerSettings,
    pid_text: str,
    rss_text: str,
) -> tuple[KeyValueEntry, ...]:
    """Top description rows: version, enabled flag, live PID/RSS, last run."""
    last_run = settings.session.last_run
    return (
        KeyValueEntry("Version", meta.general.version),
        KeyValueEntry("Enabled", str(settings.general.enabled)),
        KeyValueEntry("PID", pid_text),
        KeyValueEntry("RSS", rss_text),
        KeyValueEntry("Last Run", last_run if last_run != "none" else "n/a"),
    )


def build_state_suffixes(
    current_state: str,
    last_durations: dict[str, int | None],
    task_last_durations: dict[str, int | None] | None,
    elapsed_sec: int | None,
    exec_progress: tuple[int, int] | None,
    idle_remaining: int | None,
) -> dict[str, Content]:
    """Per-state suffixes for the runner lifecycle list.

    Runner-level rows always show the previous-run duration (dimmed) plus
    the live elapsed time in the state color when the row is active.
    Task-level rows work the same way but read the currently running
    task's durations — when no task is running they carry no suffix at
    all. ``exec`` shows ``[i/n]`` while a task state is active; ``idle``
    shows the countdown to the next iteration.
    """
    suffixes: dict[str, Content] = {}
    for state_id in _RUNNER_LAST_DURATION_ATTRS:
        suffixes[state_id] = _timed_row(
            last_durations.get(state_id), elapsed_sec, current_state, state_id
        )
    if task_last_durations is not None:
        for state_id in _TASK_LAST_DURATION_ATTRS:
            suffixes[state_id] = _timed_row(
                task_last_durations.get(state_id), elapsed_sec, current_state, state_id
            )
    if exec_progress is not None and current_state in _EXEC_CHILD_STATES:
        index, total = exec_progress
        color = RUNNER_STATE_COLORS.get("exec", _FALLBACK_STATE_STYLE)
        suffixes["exec"] = Content.assemble((f"[{index}/{total}]", color))
    if current_state == "idle" and idle_remaining is not None:
        color = RUNNER_STATE_COLORS.get("idle", _FALLBACK_STATE_STYLE)
        suffixes["idle"] = Content.assemble(
            (f"[{format_compact_duration(idle_remaining)}]", f"bold {color}")
        )
    return suffixes


class RunnerMenuScreen(MenuScreen):
    _RUNNER_STATES: tuple[StateEntry, ...] = (
        StateEntry("off", "off", color=RUNNER_STATE_COLORS["off"]),
        StateEntry("initialization", "initialization"),
        StateEntry("before-exec", "before-exec"),
        StateEntry("exec", "exec", children=("before-task", "task-exec", "after-task")),
        StateEntry("before-task", "├─ before-task"),
        StateEntry("task-exec", "├─ task-exec"),
        StateEntry("after-task", "└─ after-task"),
        StateEntry("after-exec", "after-exec"),
        StateEntry("idle", "idle", color=RUNNER_STATE_COLORS["idle"]),
        StateEntry("termination", "termination", color=RUNNER_STATE_COLORS["termination"]),
    )

    def __init__(self, runner_path: Path) -> None:
        self.runner_path = runner_path
        meta = RunnerMetadata.load(runner_path / "metadata.toml")
        settings = RunnerSettings.load(runner_path / "settings.toml")

        self._fix_session(settings, runner_path)
        self._state = StateWidget(
            id="description-widget",
            key_value_entries=build_key_value_entries(meta, settings, "n/a", "n/a"),
            current_state=settings.session.state,
            states_entries=self._RUNNER_STATES,
            state_suffixes=build_state_suffixes(
                current_state=settings.session.state,
                last_durations=_session_durations(
                    settings.session, _RUNNER_LAST_DURATION_ATTRS
                ),
                task_last_durations=None,
                elapsed_sec=None,
                exec_progress=None,
                idle_remaining=None,
            ),
        )
        items = self._build_items(meta, settings)

        super().__init__(items, description_widget=self._state, show_home_button=True, show_back_button=True)
        self.title = "Runner"
        self.sub_title = meta.general.name
        self._poll_timer: Any = None

    def on_mount(self) -> None:
        self._poll_state()
        self._start_polling()

    def on_unmount(self) -> None:
        self._stop_polling()

    def _start_polling(self) -> None:
        settings = RunnerSettings.load(self.runner_path / "settings.toml")
        if settings.general.enabled:
            self._poll_timer = self.set_interval(1.0, self._poll_state)

    def _stop_polling(self) -> None:
        if self._poll_timer is not None:
            self._poll_timer.stop()
            self._poll_timer = None

    def _poll_state(self) -> None:
        meta = RunnerMetadata.load(self.runner_path / "metadata.toml")
        settings = RunnerSettings.load(self.runner_path / "settings.toml")
        if not settings.general.enabled:
            self._stop_polling()
        self._refresh_ui(meta, settings)

    def _refresh_ui(
        self, meta: RunnerMetadata, settings: RunnerSettings
    ) -> None:
        self.menu_items = self._build_items(meta, settings)
        pid_text, rss_text = self._pid_rss_texts(meta.general.id)
        self._state.key_value_entries = build_key_value_entries(
            meta, settings, pid_text, rss_text
        )
        self._state.current_state = settings.session.state
        self._state.state_suffixes = self._build_suffixes(settings)

    def _live_proc(self, runner_id: str) -> RunnerProcess | None:
        """Live runner process, if the runner is currently enabled/running."""
        app = termux_app(self)
        return app.state.runners.get(runner_id)

    def _pid_rss_texts(self, runner_id: str) -> tuple[str, str]:
        """Live ``(pid, rss)`` texts; ``n/a`` when nothing is executing."""
        proc = self._live_proc(runner_id)
        if proc is None:
            return "n/a", "n/a"
        live_pids = proc.live_pids
        if not live_pids:
            return "n/a", "n/a"
        tree = proc_stats.tree_stats(live_pids)
        if tree.num_procs == 0:
            return "n/a", "n/a"
        label = live_pids[0] if live_pids[0] in tree.pids else tree.pids[0]
        extra = tree.num_procs - 1
        pid_text = f"{label}+{extra}" if extra > 0 else f"{label}"
        return pid_text, proc_stats.format_bytes(tree.rss_total)

    def _build_suffixes(self, settings: RunnerSettings) -> dict[str, Content]:
        """Assemble timer/progress suffixes from persisted + live runner data."""
        current_state = settings.session.state
        elapsed_sec: int | None = None
        task_last: dict[str, int | None] | None = None
        progress: tuple[int, int] | None = None
        idle_remaining: int | None = None
        proc = self._live_proc(self._runner_id())
        if proc is not None:
            elapsed_sec = proc.state_elapsed()
            if proc.current_task_path is not None:
                task_settings = TaskSettings.load(
                    proc.current_task_path / "settings.toml"
                )
                task_last = _session_durations(
                    task_settings.session, _TASK_LAST_DURATION_ATTRS
                )
            if proc.exec_total > 0:
                progress = (proc.exec_index, proc.exec_total)
            if current_state == "idle":
                idle_remaining = max(0, parse_timeout(settings.general.timeout) - elapsed_sec)
        return build_state_suffixes(
            current_state=current_state,
            last_durations=_session_durations(
                settings.session, _RUNNER_LAST_DURATION_ATTRS
            ),
            task_last_durations=task_last,
            elapsed_sec=elapsed_sec,
            exec_progress=progress,
            idle_remaining=idle_remaining,
        )

    def _runner_id(self) -> str:
        meta = RunnerMetadata.load(self.runner_path / "metadata.toml")
        return meta.general.id

    def _fix_session(self, settings: RunnerSettings, runner_path: Path) -> None:
        """Reset stale session state (same pattern as TaskMenuScreen).

        Runners are forced to "off" (vs tasks forced to "stopped")
        because "off" is the runner's terminal state.
        """
        app = termux_app(self) if hasattr(self, "app") else None
        if app and settings.session.session_id != app.state.session_id:
            settings.session.state = "off"
        if app:
            settings.session.session_id = app.state.session_id
            settings.save(runner_path / "settings.toml")

    @staticmethod
    def _build_items(
        meta: RunnerMetadata, settings: RunnerSettings
    ) -> list[ButtonConfig]:
        items: list[ButtonConfig] = []
        toggle_label = "Disable" if settings.general.enabled else "Enable"
        items.append(ButtonConfig("toggle", toggle_label, variant="warning"))
        items.append(ButtonConfig("properties", "Properties"))
        items.append(ButtonConfig("show_tasks", "Tasks"))
        items.append(ButtonConfig("show_logs", "Logs"))
        items.append(ButtonConfig("show_metadata", "Show metadata.toml"))
        items.append(ButtonConfig("show_settings", "Show settings.toml"))
        items.append(ButtonConfig("update", "Update", variant="primary", layout=ButtonLayout.BOTTOM))
        items.append(ButtonConfig("uninstall", "Uninstall", variant="error", layout=ButtonLayout.BOTTOM))
        return items

    @on(Button.Pressed, "#toggle")
    def on_toggle(self, event: Button.Pressed) -> None:
        event.stop()
        self.run_worker(self._toggle())

    async def _toggle(self) -> None:
        """Enable or disable the runner.

        When disabling: shutdown the runner process and remove it from
        app.state.runners.  When enabling: save settings first (so the
        intent is persisted even if construction fails), create a new
        RunnerProcess, and launch the asyncio lifecycle loop.
        """
        app = termux_app(self)
        meta = RunnerMetadata.load(self.runner_path / "metadata.toml")
        settings = RunnerSettings.load(self.runner_path / "settings.toml")

        if settings.general.enabled:
            loading = LoadingScreen("Runner shutting down")
            await termux_app(self).push_screen(loading)
            runner_proc = app.state.runners.get(meta.general.id)
            if runner_proc:
                await runner_proc.shutdown()
                del app.state.runners[meta.general.id]
            await loading.dismiss(None)
            settings = RunnerSettings.load(self.runner_path / "settings.toml")
            settings.general.enabled = False
        else:
            settings.general.enabled = True
            settings.save(self.runner_path / "settings.toml")
            runner_proc = RunnerProcess(
                self.runner_path, app.state.session_id, app.state.tmp_dir
            )
            app.state.runners[meta.general.id] = runner_proc
            loading = LoadingScreen("Runner starting up")
            await termux_app(self).push_screen(loading)
            runner_proc.run()
            await loading.dismiss(None)

        settings.save(self.runner_path / "settings.toml")
        meta = RunnerMetadata.load(self.runner_path / "metadata.toml")
        settings = RunnerSettings.load(self.runner_path / "settings.toml")
        self._refresh_ui(meta, settings)
        if settings.general.enabled:
            self._start_polling()
        else:
            self._stop_polling()

    @on(Button.Pressed, "#properties")
    def on_properties(self, event: Button.Pressed) -> None:
        event.stop()
        meta = RunnerMetadata.load(self.runner_path / "metadata.toml")
        termux_app(self).push_screen(
            PropertiesScreen(
                self.runner_path, meta.properties, meta.general.name
            )
        )

    @on(Button.Pressed, "#show_tasks")
    def on_show_tasks(self, event: Button.Pressed) -> None:
        event.stop()
        termux_app(self).push_screen(TasksMenuScreen(self.runner_path))

    @on(Button.Pressed, "#show_logs")
    def on_show_logs(self, event: Button.Pressed) -> None:
        event.stop()
        settings = RunnerSettings.load(self.runner_path / "settings.toml")

        def _on_settings_changed(soft_wrap: bool, auto_scroll: bool, offset: int) -> None:
            rs = RunnerSettings.load(self.runner_path / "settings.toml")
            rs.log.soft_wrap = soft_wrap
            rs.log.auto_scroll = auto_scroll
            rs.log.offset = offset
            rs.save(self.runner_path / "settings.toml")

        termux_app(self).push_screen(
            LogScreen(
                content=self.runner_path / "stdout",
                is_dynamic=True,
                soft_wrap=settings.log.soft_wrap,
                auto_scroll=settings.log.auto_scroll,
                offset=settings.log.offset,
                clear_log_file_enabled=settings.session.state == "off",
                on_settings_changed=_on_settings_changed,
            )
        )

    @on(Button.Pressed, "#show_metadata")
    def on_show_metadata(self, event: Button.Pressed) -> None:
        event.stop()
        termux_app(self).push_screen(
            LogScreen(content=self.runner_path / "metadata.toml")
        )

    @on(Button.Pressed, "#show_settings")
    def on_show_settings(self, event: Button.Pressed) -> None:
        event.stop()
        termux_app(self).push_screen(
            LogScreen(content=self.runner_path / "settings.toml")
        )

    @on(Button.Pressed, "#update")
    def on_update(self, event: Button.Pressed) -> None:
        event.stop()
        from termux_tasker.ui.screens.install_runner_version import InstallRunnerVersionScreen
        app = termux_app(self)
        tmp_folder = copy_to_tmp(self.runner_path, app.state.tmp_dir, "runner")
        app.state.register_tmp_folder(tmp_folder)
        termux_app(self).push_screen(InstallRunnerVersionScreen(tmp_folder))

    @on(Button.Pressed, "#uninstall")
    def on_uninstall(self, event: Button.Pressed) -> None:
        event.stop()
        meta = RunnerMetadata.load(self.runner_path / "metadata.toml")

        async def on_confirm(result: str | None) -> None:
            if result is not None:
                await self._do_uninstall()

        termux_app(self).push_screen(
            ConfirmationScreen(
                message=f"Are you sure you want to uninstall {meta.general.name} runner?",
                ok_button_text="Yes",
                cancel_button_text="No",
                ok_button_id="yes_uninstall",
            ),
            on_confirm,
        )

    async def _do_uninstall(self) -> None:
        app = termux_app(self)
        meta = RunnerMetadata.load(self.runner_path / "metadata.toml")
        settings = RunnerSettings.load(self.runner_path / "settings.toml")

        if settings.session.state != "off":
            loading = LoadingScreen("Runner shutting down")
            await termux_app(self).push_screen(loading)
            runner_proc = app.state.runners.get(meta.general.id)
            if runner_proc:
                await runner_proc.shutdown()
                del app.state.runners[meta.general.id]
                settings.general.enabled = False
                settings.save(self.runner_path / "settings.toml")
            await loading.dismiss(None)

        import shutil
        shutil.rmtree(self.runner_path, ignore_errors=True)

        termux_app(self).pop_screen()   # noqa

    @on(Button.Pressed, "#home")
    def on_home_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        go_home(self)
