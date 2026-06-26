from __future__ import annotations

from pathlib import Path

from textual import on
from textual.widgets import Button

from termux_tasker.config import TaskMetadata, TaskSettings
from termux_tasker.ui.base import MenuScreen
from termux_tasker.ui.screens._utils import termux_app
from termux_tasker.ui.screens.task_type import TaskTypeScreen
from termux_tasker.ui.screens.task_menu import TaskMenuScreen

class TasksMenuScreen(MenuScreen):
    def __init__(self, runner_path: Path) -> None:
        self.runner_path = runner_path
        super().__init__({"Install Task": "install_task"}, show_back_button=True)
        self.title = "Tasks"
        self._refresh()

    def _refresh(self) -> None:
        items: dict[str, str] = {}
        tasks_path = self.runner_path / "tasks"

        if tasks_path.exists():
            for task_path in sorted(tasks_path.iterdir()):
                if not task_path.is_dir():
                    continue
                meta_path = task_path / "metadata.toml"
                if not meta_path.exists():
                    continue
                meta = TaskMetadata.load(meta_path)
                settings = TaskSettings.load(task_path / "settings.toml")
                status = "enabled" if settings.general.enabled else "disabled"
                items[rf"{meta.general.name} \[{status}]"] = f"open_{meta.general.id}"

        items["Install Task"] = "install_task"
        self.menu_items = items

    @on(Button.Pressed, "#install_task")
    def on_install(self, event: Button.Pressed) -> None:
        event.stop()
        termux_app(self).push_screen(TaskTypeScreen(self.runner_path))

    @on(Button.Pressed)
    def on_open(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("open_"):
            event.stop()
            task_id = btn_id[5:]
            tasks_path = self.runner_path / "tasks"
            if not tasks_path.exists():
                return
            for task_path in tasks_path.iterdir():
                if not task_path.is_dir():
                    continue
                meta_path = task_path / "metadata.toml"
                if meta_path.exists():
                    meta = TaskMetadata.load(meta_path)
                    if meta.general.id == task_id:
                        termux_app(self).push_screen(TaskMenuScreen(task_path))
                        return
