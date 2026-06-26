from __future__ import annotations

from pathlib import Path

from textual import on
from textual.widgets import Button

from termux_tasker.config import RunnerMetadata
from termux_tasker.ui.base import MenuScreen
from termux_tasker.ui.screens._utils import termux_app


class InstallRunnerScreen(MenuScreen):
    def __init__(self, tmp_runner_folder: Path) -> None:
        self.tmp_runner_folder = tmp_runner_folder
        meta = RunnerMetadata.load(tmp_runner_folder / "metadata.toml")

        super().__init__(
            menu_items={"Install": "install"},
            description=meta.general.description or "",
            show_back_button=True,
        )
        self.title = "Install Runner"
        self.sub_title = meta.general.name

    @on(Button.Pressed, "#install")
    def on_install(self, event: Button.Pressed) -> None:
        event.stop()
        from termux_tasker.ui.screens.install_runner_version import InstallRunnerVersionScreen
        termux_app(self).push_screen(
            InstallRunnerVersionScreen(self.tmp_runner_folder)
        )
