from __future__ import annotations

from pathlib import Path
from typing import Any

from textual import on
from textual.widgets import Button

from termux_tasker.config import RunnerMetadata, RunnerSettings
from termux_tasker.runner_process import RunnerProcess
from termux_tasker.ui.base.log_screen import LogScreen
from termux_tasker.ui.base.screen import (
    MenuScreen,
    LoadingScreen,
    InputScreen,
    InfoScreen,
    ConfirmationScreen,
)
from termux_tasker.ui.screens._utils import (
    termux_app,
    copy_to_tmp,
    parse_property_value,
    is_property_value_empty,
)
from termux_tasker.ui.screens.tasks_menu import TasksMenuScreen


class RunnerMenuScreen(MenuScreen):
    def __init__(self, runner_path: Path) -> None:
        self.runner_path = runner_path
        meta = RunnerMetadata.load(runner_path / "metadata.toml")
        settings = RunnerSettings.load(runner_path / "settings.toml")

        self._fix_session(settings, runner_path)
        desc = self._build_description(meta, settings)
        items = self._build_items(meta, settings)

        super().__init__(items, description=desc, show_back_button=True)
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
        self.description = self._build_description(meta, settings)
        id_to_label = {v: k for k, v in self.menu_items.items()}
        for btn in self.query(Button):
            btn_id = btn.id
            if btn_id is not None and btn_id in id_to_label:
                btn.label = id_to_label[btn_id]

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
    def _build_description(
        meta: RunnerMetadata, settings: RunnerSettings
    ) -> str:
        parts = [
            f"Version: {meta.general.version}",
            f"Enabled: {settings.general.enabled}",
            f"State: {settings.session.state}",
        ]
        for prop_name, prop_val in settings.properties.items():
            parts.append(f"{prop_name}: {prop_val}")
        return "\n".join(parts)

    @staticmethod
    def _build_items(
        meta: RunnerMetadata, settings: RunnerSettings
    ) -> dict[str, str]:
        items: dict[str, str] = {}
        toggle_label = "Disable" if settings.general.enabled else "Enable"
        items[toggle_label] = "toggle"
        items["Show Tasks"] = "show_tasks"
        items["Show Runner Logs"] = "show_logs"
        items["Show metadata.toml"] = "show_metadata"
        items["Show settings.toml"] = "show_settings"
        for prop in meta.properties:
            items[f"Set {prop.name}"] = f"set_{prop.name}"
        items["Update"] = "update"
        items["Uninstall"] = "uninstall"
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

    @on(Button.Pressed, "#show_tasks")
    def on_show_tasks(self, event: Button.Pressed) -> None:
        event.stop()
        termux_app(self).push_screen(TasksMenuScreen(self.runner_path))

    @on(Button.Pressed, "#show_logs")
    def on_show_logs(self, event: Button.Pressed) -> None:
        event.stop()
        termux_app(self).push_screen(
            LogScreen(content=self.runner_path / "stdout", show_follow=True)
        )

    @on(Button.Pressed, "#show_metadata")
    def on_show_metadata(self, event: Button.Pressed) -> None:
        event.stop()
        termux_app(self).push_screen(
            LogScreen(content=self.runner_path / "metadata.toml", show_follow=False)
        )

    @on(Button.Pressed, "#show_settings")
    def on_show_settings(self, event: Button.Pressed) -> None:
        event.stop()
        termux_app(self).push_screen(
            LogScreen(content=self.runner_path / "settings.toml", show_follow=False)
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

    @on(Button.Pressed)
    def on_set_property(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("set_"):
            event.stop()
            prop_name = btn_id[4:]
            self._set_property(prop_name)

    def _set_property(self, prop_name: str) -> None:
        meta = RunnerMetadata.load(self.runner_path / "metadata.toml")
        settings = RunnerSettings.load(self.runner_path / "settings.toml")
        try:
            prop = next(p for p in meta.properties if p.name == prop_name)
        except StopIteration:
            return

        raw = settings.properties.get(prop.name, "")
        cur_val = parse_property_value(raw, prop.input_type)

        def _show_input() -> None:
            termux_app(self).push_screen(
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
            termux_app(self).push_screen(
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
            current_settings = RunnerSettings.load(self.runner_path / "settings.toml")
            if prop.input_type == "checkbox" and isinstance(result, (list, tuple)):
                current_settings.properties[prop.name] = ",".join(str(v) for v in result)
            else:
                current_settings.properties[prop.name] = str(result)
            current_settings.save(self.runner_path / "settings.toml")
            current_meta = RunnerMetadata.load(self.runner_path / "metadata.toml")
            self._refresh_ui(current_meta, current_settings)

        _show_input()
