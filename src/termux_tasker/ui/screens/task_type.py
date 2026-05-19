from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from textual import on
from textual.widgets import Button

from termux_tasker.ui.base.screen import (
    MenuScreen, InputScreen, InfoScreen, FileBrowserScreen,
)
from termux_tasker.ui.screens._utils import (
    termux_app, clone_repo, copy_to_tmp, GITHUB_URL_RE,
)


class TaskTypeScreen(MenuScreen):
    def __init__(self, runner_dir: Path) -> None:
        self.runner_dir = runner_dir
        super().__init__(
            menu_items={
                "Bundled": "bundled",
                "GitHub URL": "github_url",
                "Local Storage": "local_storage",
            },
            show_back_button=True,
        )
        self.title = "Task Type"

    @on(Button.Pressed, "#bundled")
    def on_bundled(self, event: Button.Pressed) -> None:
        event.stop()
        from termux_tasker.ui.screens.bundled_task import BundledTaskScreen
        self.app.push_screen(BundledTaskScreen(self.runner_dir))

    @on(Button.Pressed, "#github_url")
    def on_github(self, event: Button.Pressed) -> None:
        event.stop()

        def on_url(result: Any) -> None:
            if result is not None:
                self._process_github_url(result)

        self.app.push_screen(
            InputScreen(
                title="GitHub URL",
                input_type="text",
                current_value="https://github.com/",
            ),
            on_url,
        )

    @on(Button.Pressed, "#local_storage")
    def on_local(self, event: Button.Pressed) -> None:
        event.stop()

        def on_folder(result: Optional[Path]) -> None:
            if result is not None:
                app = termux_app(self)
                tmp_folder = copy_to_tmp(result, app.state.tmp_dir, "task")
                app.state.register_tmp_task_folder(tmp_folder)
                from termux_tasker.task_validator import TaskValidator, TaskValidatorException
                validator = TaskValidator(self.runner_dir, tmp_folder, app.state.tmp_dir / "validate")
                try:
                    validator.validate_metadata_existed()
                    validator.validate_metadata_essentials()
                except TaskValidatorException as e:
                    self.app.push_screen(InfoScreen(message=e.message, severity="error"))
                    return
                from termux_tasker.ui.screens.install_task import InstallTaskScreen
                self.app.push_screen(InstallTaskScreen(self.runner_dir, tmp_folder))

        self.app.push_screen(
            FileBrowserScreen(select_folder=True, path=Path.home()),
            on_folder,
        )

    def _process_github_url(self, url: str) -> None:
        if not GITHUB_URL_RE.match(url):
            self.app.push_screen(
                InfoScreen(message=f"Invalid GitHub URL: {url}", severity="error")
            )
            return

        app = termux_app(self)
        folder = clone_repo(url, app.state.tmp_dir, "task")
        if folder is None:
            self.app.push_screen(
                InfoScreen(
                    message=f"Repository not found or inaccessible: {url}",
                    severity="error",
                )
            )
            return
        app.state.register_tmp_task_folder(folder)
        from termux_tasker.task_validator import TaskValidator, TaskValidatorException
        validator = TaskValidator(self.runner_dir, folder, app.state.tmp_dir / "validate")
        try:
            validator.validate_metadata_existed()
            validator.validate_metadata_essentials()
        except TaskValidatorException as e:
            self.app.push_screen(InfoScreen(message=e.message, severity="error"))
            return
        from termux_tasker.ui.screens.install_task import InstallTaskScreen
        self.app.push_screen(InstallTaskScreen(self.runner_dir, folder))
