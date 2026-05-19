from __future__ import annotations

import asyncio
from pathlib import Path

from textual import on
from textual.widgets import Button

from termux_tasker.config import TaskMetadata, BundledTasks
from termux_tasker.ui.base.screen import MenuScreen, LoadingScreen, InfoScreen
from termux_tasker.ui.screens._utils import termux_app, clone_repo


class BundledTaskScreen(MenuScreen):
    def __init__(self, runner_dir: Path) -> None:
        self.runner_dir = runner_dir
        self._tmp_folders: list[Path] = []
        super().__init__({}, show_back_button=True)
        self.title = "Bundled Task"
        self._loaded = False

    def on_mount(self) -> None:
        if not self._loaded:
            self._loaded = True
            self.run_worker(self._load())

    async def _load(self) -> None:
        loading = LoadingScreen("Fetching tasks")
        termux_app(self).push_screen(loading)
        bundled = BundledTasks.load(self.runner_dir / "bundled.toml")
        self._tmp_folders.clear()

        app = termux_app(self)
        clone_tasks = [
            asyncio.to_thread(clone_repo, task_item.url, app.state.tmp_dir, "task")
            for task_item in bundled.tasks
        ]
        results = await asyncio.gather(*clone_tasks)
        for folder in results:
            if folder is not None:
                self._tmp_folders.append(folder)
                app.state.register_tmp_task_folder(folder)

        installed_tasks: set[str] = set()
        tasks_dir = self.runner_dir / "tasks"
        if tasks_dir.exists():
            for task_dir in tasks_dir.iterdir():
                if not task_dir.is_dir():
                    continue
                meta_path = task_dir / "metadata.toml"
                if meta_path.exists():
                    meta = TaskMetadata.load(meta_path)
                    installed_tasks.add(meta.general.id)

        items: dict[str, str] = {}
        for tmp_folder in self._tmp_folders:
            meta_path = tmp_folder / "metadata.toml"
            if not meta_path.exists():
                continue
            meta = TaskMetadata.load(meta_path)
            is_installed = meta.general.id in installed_tasks
            label = meta.general.name
            if is_installed:
                label += " \\[Installed]"
                btn_id = ""
            else:
                btn_id = f"install_{meta.general.id}"
            items[label] = btn_id

        await loading.dismiss(None)
        self.menu_items = items

    @on(Button.Pressed)
    def on_install(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("install_"):
            event.stop()
            task_id = btn_id[8:]
            for tmp_folder in self._tmp_folders:
                meta_path = tmp_folder / "metadata.toml"
                if meta_path.exists():
                    meta = TaskMetadata.load(meta_path)
                    if meta.general.id == task_id:
                        app = termux_app(self)
                        from termux_tasker.task_validator import TaskValidator, TaskValidatorException
                        validator = TaskValidator(self.runner_dir, tmp_folder, app.state.tmp_dir / "validate")
                        try:
                            validator.validate_metadata_existed()
                            validator.validate_metadata_essentials()
                        except TaskValidatorException as e:
                            termux_app(self).push_screen(InfoScreen(message=e.message, severity="error"))
                            return
                        from termux_tasker.ui.screens.install_task import InstallTaskScreen
                        termux_app(self).push_screen(
                            InstallTaskScreen(self.runner_dir, tmp_folder)
                        )
                        return
