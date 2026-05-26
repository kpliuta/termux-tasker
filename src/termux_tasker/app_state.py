from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

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

        import importlib.resources as res
        pkg = res.files("termux_tasker")
        self.default_app_config_file = Path(str(pkg / "resources" / "default.app.toml"))
        self.bundled_runners_file = Path(str(pkg / "resources" / "bundled_runners.toml"))

        self.runners: dict[str, RunnerProcess] = {}
        self._current_runner_path: Optional[Path] = None
        self._current_task_path: Optional[Path] = None
        self._tmp_runner_folders: list[Path] = []
        self._tmp_task_folders: list[Path] = []

    @property
    def current_runner_path(self) -> Optional[Path]:
        return self._current_runner_path

    @current_runner_path.setter
    def current_runner_path(self, value: Optional[Path]) -> None:
        self._current_runner_path = value

    @property
    def current_task_path(self) -> Optional[Path]:
        return self._current_task_path

    @current_task_path.setter
    def current_task_path(self, value: Optional[Path]) -> None:
        self._current_task_path = value

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
