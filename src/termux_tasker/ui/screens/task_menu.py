from __future__ import annotations

import asyncio
import re
import shutil
from pathlib import Path
from typing import Any

from textual import on
from textual.widgets import Button

from termux_tasker.config import TaskMetadata, TaskSettings
from termux_tasker.ui.base.screen import (
    MenuScreen,
    LoadingScreen,
    InputScreen,
    InfoScreen,
    ConfirmationScreen,
    LogScreen,
)
from termux_tasker.ui.screens._utils import (
    termux_app,
    copy_to_tmp,
    parse_property_value,
    is_property_value_empty,
)

_TIMEOUT_RE = re.compile(r"^[0-9]+[hms]$")


class TaskMenuScreen(MenuScreen):
    def __init__(self, task_dir: Path) -> None:
        self.task_dir = task_dir
        self.runner_dir = task_dir.parent.parent
        meta = TaskMetadata.load(task_dir / "metadata.toml")
        settings = TaskSettings.load(task_dir / "settings.toml")

        self._fix_session(settings, task_dir)
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
        settings = TaskSettings.load(self.task_dir / "settings.toml")
        if settings.general.enabled:
            self._poll_timer = self.set_interval(1.0, self._poll_state)

    def _stop_polling(self) -> None:
        if self._poll_timer is not None:
            self._poll_timer.stop()
            self._poll_timer = None

    def _poll_state(self) -> None:
        meta = TaskMetadata.load(self.task_dir / "metadata.toml")
        settings = TaskSettings.load(self.task_dir / "settings.toml")
        if not settings.general.enabled:
            self._stop_polling()
        self._refresh_ui(meta, settings)

    def _refresh_ui(
        self, meta: TaskMetadata, settings: TaskSettings
    ) -> None:
        self.menu_items = self._build_items(meta, settings)
        self.description = self._build_description(meta, settings)
        id_to_label = {v: k for k, v in self.menu_items.items()}
        for btn in self.query(Button):
            if btn.id in id_to_label:
                btn.label = id_to_label[btn.id]

    def _fix_session(self, settings: TaskSettings, task_dir: Path) -> None:
        app = termux_app(self) if hasattr(self, "app") else None
        if app and settings.session.session_id != app.state.session_id:
            settings.session.state = "stopped"
        if app:
            settings.session.session_id = app.state.session_id
            settings.save(task_dir / "settings.toml")

    def _build_description(
        self, meta: TaskMetadata, settings: TaskSettings
    ) -> str:
        parts = [
            f"Version: {meta.general.version}",
            f"Enabled: {settings.general.enabled}",
            f"State: {settings.session.state}",
            f"Timeout: {settings.general.timeout}",
        ]
        for prop_name, prop_val in settings.properties.items():
            parts.append(f"{prop_name}: {prop_val}")
        return "\n".join(parts)

    def _build_items(
        self, meta: TaskMetadata, settings: TaskSettings
    ) -> dict[str, str]:
        items: dict[str, str] = {}
        toggle_label = "Disable" if settings.general.enabled else "Enable"
        items[toggle_label] = "toggle"
        items["Show metadata.toml"] = "show_metadata"
        items["Show settings.toml"] = "show_settings"
        items["Set Timeout"] = "set_timeout"
        for prop in meta.properties:
            items[f"Set {prop.name}"] = f"set_{prop.name}"
        items["Update"] = "update"
        items["Uninstall"] = "uninstall"
        return items

    @on(Button.Pressed, "#toggle")
    def on_toggle(self, event: Button.Pressed) -> None:
        event.stop()
        settings = TaskSettings.load(self.task_dir / "settings.toml")
        settings.general.enabled = not settings.general.enabled
        settings.save(self.task_dir / "settings.toml")
        meta = TaskMetadata.load(self.task_dir / "metadata.toml")
        settings = TaskSettings.load(self.task_dir / "settings.toml")
        self._refresh_ui(meta, settings)
        if settings.general.enabled:
            self._start_polling()
        else:
            self._stop_polling()

    @on(Button.Pressed, "#show_metadata")
    def on_show_metadata(self, event: Button.Pressed) -> None:
        event.stop()
        self.app.push_screen(
            LogScreen(content=self.task_dir / "metadata.toml", show_follow=False)
        )

    @on(Button.Pressed, "#show_settings")
    def on_show_settings(self, event: Button.Pressed) -> None:
        event.stop()
        self.app.push_screen(
            LogScreen(content=self.task_dir / "settings.toml", show_follow=False)
        )

    @on(Button.Pressed, "#set_timeout")
    def on_set_timeout(self, event: Button.Pressed) -> None:

        def _show_input() -> None:
            settings = TaskSettings.load(self.task_dir / "settings.toml")
            self.app.push_screen(
                InputScreen(
                    title="Timeout",
                    input_type="text",
                    current_value=settings.general.timeout,
                ),
                _on_result,
            )

        def _warn_empty() -> None:
            self.app.push_screen(
                InfoScreen(
                    message="Timeout is required and must have a value.",
                    severity="warning",
                ),
                lambda _: _show_input(),
            )

        def _warn_format() -> None:
            self.app.push_screen(
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
            settings = TaskSettings.load(self.task_dir / "settings.toml")
            settings.general.timeout = val
            settings.save(self.task_dir / "settings.toml")
            meta = TaskMetadata.load(self.task_dir / "metadata.toml")
            settings = TaskSettings.load(self.task_dir / "settings.toml")
            self._refresh_ui(meta, settings)

        _show_input()

    @on(Button.Pressed, "#update")
    def on_update(self, event: Button.Pressed) -> None:
        event.stop()
        from termux_tasker.ui.screens.install_task_version import InstallTaskVersionScreen
        app = termux_app(self)
        tmp_folder = copy_to_tmp(self.task_dir, app.state.tmp_dir, "task")
        app.state.register_tmp_task_folder(tmp_folder)
        self.app.push_screen(
            InstallTaskVersionScreen(self.runner_dir, tmp_folder)
        )

    @on(Button.Pressed, "#uninstall")
    def on_uninstall(self, event: Button.Pressed) -> None:
        event.stop()
        meta = TaskMetadata.load(self.task_dir / "metadata.toml")

        def on_confirm(result: str | None) -> None:
            if result is not None:
                self.run_worker(self._do_uninstall())

        self.app.push_screen(
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
        self.app.push_screen(loading)

        settings = TaskSettings.load(self.task_dir / "settings.toml")
        while settings.session.state != "stopped":
            await asyncio.sleep(0.5)
            settings = TaskSettings.load(self.task_dir / "settings.toml")

        loading.dismiss(None)

        shutil.rmtree(self.task_dir, ignore_errors=True)
        self.app.pop_screen()

    @on(Button.Pressed)
    def on_set_property(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("set_"):
            event.stop()
            prop_name = btn_id[4:]
            self._set_property(prop_name)

    def _set_property(self, prop_name: str) -> None:
        meta = TaskMetadata.load(self.task_dir / "metadata.toml")
        settings = TaskSettings.load(self.task_dir / "settings.toml")
        prop = next((p for p in meta.properties if p.name == prop_name), None)
        if prop is None:
            return

        raw = settings.properties.get(prop.name, "")
        cur_val = parse_property_value(raw, prop.input_type)

        def _show_input() -> None:
            self.app.push_screen(
                InputScreen(
                    title=prop.name,
                    description=prop.description or "",
                    input_type=prop.input_type,
                    options=prop.options or [],
                    current_value=cur_val,
                ),
                _on_result,
            )

        def _warn_and_retry() -> None:
            self.app.push_screen(
                InfoScreen(
                    message=f"'{prop.name}' is required and must have a value.",
                    severity="warning",
                ),
                lambda _: _show_input(),
            )

        def _on_result(result: Any) -> None:
            if result is None:
                return
            if not prop.optional and is_property_value_empty(result, prop.input_type):
                _warn_and_retry()
                return
            settings = TaskSettings.load(self.task_dir / "settings.toml")
            if prop.input_type == "checkbox" and isinstance(result, (list, tuple)):
                settings.properties[prop.name] = ",".join(str(v) for v in result)
            else:
                settings.properties[prop.name] = str(result)
            settings.save(self.task_dir / "settings.toml")
            meta = TaskMetadata.load(self.task_dir / "metadata.toml")
            settings = TaskSettings.load(self.task_dir / "settings.toml")
            self._refresh_ui(meta, settings)

        _show_input()
