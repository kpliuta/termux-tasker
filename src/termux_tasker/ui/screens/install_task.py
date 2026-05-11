from __future__ import annotations

from pathlib import Path

from textual import on
from textual.widgets import Button

from termux_tasker.config import TaskMetadata
from termux_tasker.ui.base.screen import MenuScreen


class InstallTaskScreen(MenuScreen):
    def __init__(self, runner_dir: Path, tmp_task_folder: Path) -> None:
        self.runner_dir = runner_dir
        self.tmp_task_folder = tmp_task_folder
        meta = TaskMetadata.load(tmp_task_folder / "metadata.toml")

        super().__init__(
            menu_items={"Install": "install"},
            description=meta.general.description or "",
            show_back_button=True,
        )
        self.title = "Install Task"
        self.sub_title = meta.general.name

    @on(Button.Pressed, "#install")
    def on_install(self, event: Button.Pressed) -> None:
        event.stop()
        from termux_tasker.ui.screens.install_task_version import InstallTaskVersionScreen
        self.app.push_screen(
            InstallTaskVersionScreen(self.runner_dir, self.tmp_task_folder)
        )
