from __future__ import annotations

import importlib.resources as res
import uuid
from pathlib import Path

from termux_tasker.runner_process import RunnerProcess


class AppState:
    def __init__(self, app_version: str) -> None:
        self.app_version = app_version
        self.session_id = str(uuid.uuid4())

        home = Path.home()
        self.work_dir = home / ".termux-tasker"
        self.runners_path = self.work_dir / "runners"
        self.tmp_dir = self.work_dir / ".tmp"
        self.app_config_file = self.work_dir / "app.toml"

        pkg_path = Path(str(res.files("termux_tasker")))
        self.app_root_path = pkg_path.parent.parent
        self.default_app_config_file = pkg_path / "resources" / "default.app.toml"
        self.bundled_runners_file = pkg_path / "resources" / "bundled_runners.toml"

        self.runners: dict[str, RunnerProcess] = {}
        self._tmp_runner_folders: list[Path] = []
        self._tmp_task_folders: list[Path] = []

    def register_tmp_folder(self, folder: Path) -> None:
        self._tmp_runner_folders.append(folder)

    def register_tmp_task_folder(self, folder: Path) -> None:
        self._tmp_task_folders.append(folder)

    def cleanup(self) -> None:
        import shutil
        for folder in self._tmp_runner_folders:
            shutil.rmtree(folder, ignore_errors=True)
        for folder in self._tmp_task_folders:
            shutil.rmtree(folder, ignore_errors=True)
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def ensure_dirs(self) -> None:
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.runners_path.mkdir(parents=True, exist_ok=True)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
