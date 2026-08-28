from __future__ import annotations

from pathlib import Path
from typing import Any

from textual import on
from textual.widgets import Button

from termux_tasker.config import RunnerMetadata, RunnerSettings
from termux_tasker.runner_process import RunnerProcess
from termux_tasker.ui.base.log_screen import LogScreen
from termux_tasker.ui.base import (
    ButtonConfig,
    ButtonLayout,
    MenuScreen,
    LoadingScreen,
    ConfirmationScreen,
)
from termux_tasker.ui.screens._utils import (
    termux_app,
    copy_to_tmp,
)
from termux_tasker.ui.screens.properties import PropertiesScreen
from termux_tasker.ui.screens.tasks_menu import TasksMenuScreen
from termux_tasker.ui.screens.widgets.description import (
    KeyValueEntry,
    StateEntry,
    StateWidget,
)


class RunnerMenuScreen(MenuScreen):
    _RUNNER_STATES: tuple[StateEntry, ...] = (
        StateEntry("off", "off", color="$text-error"),
        StateEntry("initialization", "initialization"),
        StateEntry("before-exec", "before-exec"),
        StateEntry("exec", "exec", children=("before-task", "task-exec", "after-task")),
        StateEntry("before-task", "├─ before-task"),
        StateEntry("task-exec", "├─ task-exec"),
        StateEntry("after-task", "└─ after-task"),
        StateEntry("after-exec", "after-exec"),
        StateEntry("idle", "idle", color="$text-warning"),
        StateEntry("termination", "termination", color="$text-error"),
    )

    def __init__(self, runner_path: Path) -> None:
        self.runner_path = runner_path
        meta = RunnerMetadata.load(runner_path / "metadata.toml")
        settings = RunnerSettings.load(runner_path / "settings.toml")

        self._fix_session(settings, runner_path)
        self._state = StateWidget(
            id="description-widget",
            key_value_entries=(
                KeyValueEntry("Version", meta.general.version),
                KeyValueEntry("Enabled", str(settings.general.enabled)),
            ),
            current_state=settings.session.state,
            states_entries=self._RUNNER_STATES,
        )
        items = self._build_items(meta, settings)

        super().__init__(items, description_widget=self._state, show_back_button=True)
        self.title = "Runner"
        self.sub_title = meta.general.name
        self._poll_timer: Any = None

    def on_mount(self) -> None:
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
        self._state.key_value_entries = (
            KeyValueEntry("Version", meta.general.version),
            KeyValueEntry("Enabled", str(settings.general.enabled)),
        )
        self._state.current_state = settings.session.state

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
