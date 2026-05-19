from __future__ import annotations

import asyncio
from pathlib import Path

from textual import on
from textual.widgets import Button

from termux_tasker.config import RunnerMetadata, BundledRunners
from termux_tasker.ui.base.screen import MenuScreen, LoadingScreen, InfoScreen
from termux_tasker.ui.screens._utils import termux_app, clone_repo


class BundledRunnerScreen(MenuScreen):
    def __init__(self) -> None:
        super().__init__({}, show_back_button=True)
        self.title = "Bundled Runner"
        self._tmp_folders: list[Path] = []
        self._loaded = False

    def on_mount(self) -> None:
        if not self._loaded:
            self._loaded = True
            self._loading = LoadingScreen("Fetching runners")
            termux_app(self).push_screen(self._loading)
            self.run_worker(self._load())

    async def _load(self) -> None:
        app = termux_app(self)
        bundled = BundledRunners.load(app.state.bundled_runners_file)
        self._tmp_folders.clear()

        clone_tasks = [
            asyncio.to_thread(clone_repo, runner_item.url, app.state.tmp_dir, "runner")
            for runner_item in bundled.runners
        ]
        results = await asyncio.gather(*clone_tasks)
        for folder in results:
            if folder is not None:
                self._tmp_folders.append(folder)
                app.state.register_tmp_folder(folder)

        installed_runners: set[str] = set()
        for runner_dir in app.state.runners_dir.iterdir():
            if runner_dir.is_dir():
                meta_path = runner_dir / "metadata.toml"
                if meta_path.exists():
                    meta = RunnerMetadata.load(meta_path)
                    installed_runners.add(meta.general.id)

        items: dict[str, str] = {}
        for tmp_folder in self._tmp_folders:
            meta_path = tmp_folder / "metadata.toml"
            if not meta_path.exists():
                continue
            meta = RunnerMetadata.load(meta_path)
            is_installed = meta.general.id in installed_runners
            label = meta.general.name
            if is_installed:
                label += " \\[Installed]"
                btn_id = ""
            else:
                btn_id = f"install_{meta.general.id}"
            items[label] = btn_id

        self._loading.dismiss(None)
        self.menu_items = items

    @on(Button.Pressed)
    def on_install(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("install_"):
            event.stop()
            runner_id = btn_id[8:]
            for tmp_folder in self._tmp_folders:
                meta_path = tmp_folder / "metadata.toml"
                if meta_path.exists():
                    meta = RunnerMetadata.load(meta_path)
                    if meta.general.id == runner_id:
                        from termux_tasker.runner_validator import RunnerValidator, RunnerValidatorException
                        validator = RunnerValidator(tmp_folder)
                        try:
                            validator.validate_metadata_existed()
                            validator.validate_metadata_essentials()
                        except RunnerValidatorException as e:
                            termux_app(self).push_screen(InfoScreen(message=e.message, severity="error"))
                            return
                        from termux_tasker.ui.screens.install_runner import InstallRunnerScreen
                        termux_app(self).push_screen(InstallRunnerScreen(tmp_folder))
                        return
