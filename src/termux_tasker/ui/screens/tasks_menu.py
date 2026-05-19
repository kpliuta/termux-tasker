from __future__ import annotations

from pathlib import Path

from textual import on
from textual.widgets import Button

from termux_tasker.config import TaskMetadata, TaskSettings
from termux_tasker.ui.base.screen import MenuScreen
from termux_tasker.ui.screens._utils import termux_app
from termux_tasker.ui.screens.task_type import TaskTypeScreen
from termux_tasker.ui.screens.task_menu import TaskMenuScreen

class TasksMenuScreen(MenuScreen):
    def __init__(self, runner_dir: Path) -> None:
        self.runner_dir = runner_dir
        super().__init__({"Install Task": "install_task"}, show_back_button=True)
        self.title = "Tasks"
        self._refresh()

    def _refresh(self) -> None:
        items: dict[str, str] = {}
        tasks_dir = self.runner_dir / "tasks"

        if tasks_dir.exists():
            for task_dir in sorted(tasks_dir.iterdir()):
                if not task_dir.is_dir():
                    continue
                meta_path = task_dir / "metadata.toml"
                if not meta_path.exists():
                    continue
                meta = TaskMetadata.load(meta_path)
                settings = TaskSettings.load(task_dir / "settings.toml")
                status = "enabled" if settings.general.enabled else "disabled"
                items[rf"{meta.general.name} \[{status}]"] = f"open_{meta.general.id}"

        items["Install Task"] = "install_task"
        self.menu_items = items

    @on(Button.Pressed, "#install_task")
    def on_install(self, event: Button.Pressed) -> None:
        event.stop()
        termux_app(self).push_screen(TaskTypeScreen(self.runner_dir))

    @on(Button.Pressed)
    def on_open(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("open_"):
            event.stop()
            task_id = btn_id[5:]
            tasks_dir = self.runner_dir / "tasks"
            if not tasks_dir.exists():
                return
            for task_dir in tasks_dir.iterdir():
                if not task_dir.is_dir():
                    continue
                meta_path = task_dir / "metadata.toml"
                if meta_path.exists():
                    meta = TaskMetadata.load(meta_path)
                    if meta.general.id == task_id:
                        termux_app(self).push_screen(TaskMenuScreen(task_dir))
                        return
