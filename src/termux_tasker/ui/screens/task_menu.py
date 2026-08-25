from __future__ import annotations

import asyncio
import re
import shutil
from pathlib import Path
from typing import Any

from textual import on
from textual.widgets import Button

from termux_tasker.config import TaskMetadata, TaskSettings
from termux_tasker.ui.base.log_screen import LogScreen
from termux_tasker.ui.base import (
    ButtonConfig,
    ButtonLayout,
    MenuScreen,
    LoadingScreen,
    InputScreen,
    InfoScreen,
    ConfirmationScreen,
    FileBrowserScreen,
)
from termux_tasker.ui.screens._utils import (
    termux_app,
    copy_to_tmp,
)
from termux_tasker.ui.screens.properties import PropertiesScreen

_TIMEOUT_RE = re.compile(r"^[0-9]+[hms]$")


class TaskMenuScreen(MenuScreen):
    def __init__(self, task_path: Path) -> None:
        self.task_path = task_path
        self.runner_path = task_path.parent.parent
        meta = TaskMetadata.load(task_path / "metadata.toml")
        settings = TaskSettings.load(task_path / "settings.toml")

        self._fix_session(settings, task_path)
        desc = self._build_description(meta, settings)
        items = self._build_items(meta, settings)

        super().__init__(items, description=desc, show_back_button=True)
        self.title = "Task"
        self.sub_title = meta.general.name
        self._poll_timer: Any = None

    def on_mount(self) -> None:
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
        self.description = self._build_description(meta, settings)

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

    @staticmethod
    def _build_description(
        meta: TaskMetadata, settings: TaskSettings
    ) -> str:
        parts = [
            f"Version: {meta.general.version}",
            f"Enabled: {settings.general.enabled}",
            f"State: {settings.session.state}",
            f"Timeout: {settings.general.timeout}",
        ]
        return "\n".join(parts)

    def _build_items(
        self, meta: TaskMetadata, settings: TaskSettings
    ) -> list[ButtonConfig]:
        items: list[ButtonConfig] = []
        toggle_label = "Disable" if settings.general.enabled else "Enable"
        items.append(ButtonConfig("toggle", toggle_label, variant="warning"))
        items.append(ButtonConfig("properties", "Properties"))
        items.append(ButtonConfig("show_metadata", "Show metadata.toml"))
        items.append(ButtonConfig("show_settings", "Show settings.toml"))
        items.append(ButtonConfig("timeout", "Set Timeout"))
        items.append(ButtonConfig("update", "Update", variant="primary", layout=ButtonLayout.BOTTOM))
        items.append(ButtonConfig("uninstall", "Uninstall", variant="error", layout=ButtonLayout.BOTTOM))
        output_dir = self.task_path / "output"
        if output_dir.exists():
            items.append(ButtonConfig("show_output", "Show output"))
        return items

    @on(Button.Pressed, "#properties")
    def on_properties(self, event: Button.Pressed) -> None:
        event.stop()
        meta = TaskMetadata.load(self.task_path / "metadata.toml")
        termux_app(self).push_screen(
            PropertiesScreen(
                self.task_path, meta.properties, meta.general.name
            )
        )

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

        Uses a closure chain to create a multistep dialog:
          _show_input → InputScreen[1] ─(on result)─→ _on_result
               ↑                                            │
               └──── _warn_xxx ─→ InfoScreen ───────────────┘

        [1] Shows the current value as prefill.
        On empty or invalid format: warning InfoScreen → re-prompt.
        On valid format: save and refresh.
        """
        event.stop()

        def _show_input() -> None:
            settings = TaskSettings.load(self.task_path / "settings.toml")
            termux_app(self).push_screen(
                InputScreen(
                    title="Timeout",
                    input_type="text",
                    current_value=settings.general.timeout,
                ),
                _on_result,
            )

        def _warn_empty() -> None:
            termux_app(self).push_screen(
                InfoScreen(
                    message="Timeout is required and must have a value.",
                    severity="warning",
                ),
                lambda _: _show_input(),
            )

        def _warn_format() -> None:
            termux_app(self).push_screen(
                InfoScreen(
                    message="Invalid timeout format. Use e.g. 30s, 5m, 1h.",
                    severity="warning",
                ),
                lambda _: _show_input(),
            )

        def _on_result(result: Any) -> None:
            if result is None:
                return
            val = str(result).strip()
            if not val:
                _warn_empty()
                return
            if not _TIMEOUT_RE.match(val):
                _warn_format()
                return
            settings = TaskSettings.load(self.task_path / "settings.toml")
            settings.general.timeout = val
            settings.save(self.task_path / "settings.toml")
            meta = TaskMetadata.load(self.task_path / "metadata.toml")
            settings = TaskSettings.load(self.task_path / "settings.toml")
            self._refresh_ui(meta, settings)

        _show_input()

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
