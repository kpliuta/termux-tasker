from __future__ import annotations

from pathlib import Path
from typing import Any

from textual import on
from textual.widgets import Button

from termux_tasker.config import RunnerMetadata, RunnerSettings
from termux_tasker.ui.base.screen import MenuScreen
from termux_tasker.ui.screens._utils import termux_app
from termux_tasker.ui.screens.runner_menu import RunnerMenuScreen


class RunnersScreen(MenuScreen):
    def __init__(self) -> None:
        super().__init__({}, show_back_button=True)
        self.title = "Runners"
        self._poll_timer: Any = None

    def on_mount(self) -> None:
        self._refresh()
        self._start_polling()

    def on_unmount(self) -> None:
        self._stop_polling()

    def _start_polling(self) -> None:
        self._poll_timer = self.set_interval(1.0, self._poll)

    def _stop_polling(self) -> None:
        if self._poll_timer is not None:
            self._poll_timer.stop()
            self._poll_timer = None

    def _poll(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        app = termux_app(self)
        items: dict[str, str] = {}
        runners_path = app.state.runners_path
        runner_paths: list[Path] = sorted(runners_path.iterdir())
        for runner_path in runner_paths:
            if not runner_path.is_dir():
                continue
            meta_path = runner_path / "metadata.toml"
            if not meta_path.exists():
                continue
            meta = RunnerMetadata.load(meta_path)
            settings = RunnerSettings.load(runner_path / "settings.toml")
            status = self._status_str(settings)
            items[rf"{meta.general.name} \[{status}]"] = f"open_{meta.general.id}"

        items["Install Runner"] = "install_runner"
        self.menu_items = items

    @staticmethod
    def _status_str(settings: RunnerSettings) -> str:
        if not settings.general.enabled:
            return "disabled"
        return settings.session.state

    @on(Button.Pressed)
    def on_any_button(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id == "install_runner":
            event.stop()
            from termux_tasker.ui.screens.runner_type import RunnerTypeScreen
            termux_app(self).push_screen(RunnerTypeScreen())
        elif btn_id.startswith("open_"):
            event.stop()
            runner_id = btn_id[5:]
            app = termux_app(self)
            for runner_path in app.state.runners_path.iterdir():
                if not runner_path.is_dir():
                    continue
                meta_path = runner_path / "metadata.toml"
                if meta_path.exists():
                    meta = RunnerMetadata.load(meta_path)
                    if meta.general.id == runner_id:
                        termux_app(self).push_screen(RunnerMenuScreen(runner_path))
                        return
