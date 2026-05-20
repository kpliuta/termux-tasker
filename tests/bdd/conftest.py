from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from termux_tasker.app import TermuxTaskerApp
    from tests.bdd.pilot_driver import PilotDriver

from termux_tasker.config import (
    RunnerMetadata,
    RunnerSettings,
    TaskMetadata,
    TaskSettings,
)

# ── Inline resource definitions (BDD owns these; tests/resources/ is for manual testing) ──

SH_RUNNER_METADATA = """\
[general]
id = "sh_runner"
name = "Simple sh runner"
description = "A simple shell-based runner. Executes shell scripts as tasks."
version = "1.1.0"
app_min_version = ">=0.1.0"

[[property]]
name = "property-1"
description = "Description of Property 1"
input-type = "text"
optional = false

[[property]]
name = "property-2"
description = "Description of Property 2"
input-type = "text"
optional = false
default = "Property 1 Default"

[[property]]
name = "property-3"
description = "Description of Property 3"
input-type = "radio"
optional = false
options = ["one", "two", "three"]

[[property]]
name = "property-4"
description = "Description of Property 4"
input-type = "checkbox"
optional = false
options = ["one", "two", "three"]

[[task-validator]]
command = "test -f {task_dir}/required_file"

[exec]
initialization = 'echo init'
before-exec = 'echo before-exec'
before-task = 'echo before-task'
task-exec = 'sh {task_dir}/required_file'
after-task = 'echo after-task'
after-exec = 'echo after-exec'
termination = 'echo termination'
"""

SH_RUNNER_MALFORMED_NO_EXEC_METADATA = """\
[general]
id = "sh_runner_malformed_no_exec"
name = "No exec"
version = "1.1.0"
app_min_version = ">=0.1.0"
"""

SH_RUNNER_TASK_METADATA = """\
[general]
id = "sh_runner_task"
name = "Simple sh runner task"
description = "A demo task for the Simple sh runner."
version = "10"
runner_id = "sh_runner"
runner_min_version = ">=1.1.0,<2.0.0"
default_timeout = "1m"

[[property]]
name = "task-property-1"
description = "Description of Property 1"
input-type = "text"
optional = false
"""

SH_RUNNER_TASK_NO_REQUIRED_FILE_METADATA = """\
[general]
id = "sh_runner_task_malformed_no_required_file"
name = "No required file"
version = "1"
runner_id = "sh_runner"
runner_min_version = ">=1.1.0,<2.0.0"
default_timeout = "1m"

[[property]]
name = "task-property-1"
description = "Description of Property 1"
input-type = "text"
optional = false
"""

SH_RUNNER_TASK_WRONG_VERSION_METADATA = """\
[general]
id = "sh_runner_task_malformed_wrong_runner_version"
name = "Wrong Runner Version"
version = "1"
runner_id = "sh_runner"
runner_min_version = ">=10.1.0"
default_timeout = "1m"

[[property]]
name = "task-property-1"
description = "Description of Property 1"
input-type = "text"
optional = false
"""

REQUIRED_FILE_CONTENT = '#!/bin/sh\necho "Success"\n'

RUNNER_REQUIRED_META = """\
[general]
id = "test_runner"
name = "Test Runner"
version = "1.0.0"
app_min_version = ">=0.1.0"

[[property]]
name = "prop-1"
description = "First required property"
input-type = "text"
optional = false

[[property]]
name = "prop-2"
description = "Second required property"
input-type = "text"
optional = false

[exec]
task-exec = 'echo test'
"""

TASK_REQUIRED_META = """\
[general]
id = "test_task"
name = "Test Task"
version = "1.0.0"
runner_id = "sh_runner"
runner_min_version = ">=0.1.0"
default_timeout = "1m"

[[property]]
name = "task-prop-1"
description = "First required property"
input-type = "text"
optional = false

[[property]]
name = "task-prop-2"
description = "Second required property"
input-type = "text"
optional = false
"""


def _write_runner(dir_path: Path, metadata: str) -> Path:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / "metadata.toml").write_text(metadata)
    return dir_path


def _write_task(dir_path: Path, metadata: str) -> Path:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / "metadata.toml").write_text(metadata)
    (dir_path / "required_file").write_text(REQUIRED_FILE_CONTENT)
    return dir_path


# ── Low-level fixtures (disk management) ────────────────────────────────


@pytest.fixture
def tmp_dir() -> Iterator[Path]:
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path, ignore_errors=True)


# ── Runner fixtures (set up runner directories on disk) ─────────────────


@pytest.fixture
def sh_runner_dir(tmp_dir: Path) -> Path:
    dst = tmp_dir / "runners" / "sh_runner"
    _write_runner(dst, SH_RUNNER_METADATA)
    settings = RunnerSettings()
    settings.general.enabled = False
    settings.session.session_id = "test-session"
    settings.session.state = "off"
    settings.save(dst / "settings.toml")
    return dst


@pytest.fixture
def sh_runner_enabled(sh_runner_dir: Path) -> Path:
    settings = RunnerSettings.load(sh_runner_dir / "settings.toml")
    settings.general.enabled = True
    settings.save(sh_runner_dir / "settings.toml")
    return sh_runner_dir


@pytest.fixture
def sh_runner_malformed_no_exec_dir(tmp_dir: Path) -> Path:
    return _write_runner(
        tmp_dir / "runners" / "sh_runner_malformed_no_exec",
        SH_RUNNER_MALFORMED_NO_EXEC_METADATA,
    )


# ── Task fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def sh_runner_task_dir(tmp_dir: Path) -> Path:
    dst = tmp_dir / "tasks" / "sh_runner_task"
    _write_task(dst, SH_RUNNER_TASK_METADATA)
    settings = TaskSettings()
    settings.general.enabled = False
    settings.session.session_id = "test-session"
    settings.session.state = "stopped"
    settings.save(dst / "settings.toml")
    return dst


@pytest.fixture
def sh_runner_task_enabled(sh_runner_task_dir: Path) -> Path:
    settings = TaskSettings.load(sh_runner_task_dir / "settings.toml")
    settings.general.enabled = True
    settings.save(sh_runner_task_dir / "settings.toml")
    return sh_runner_task_dir


@pytest.fixture
def sh_runner_task_no_required_file_dir(tmp_dir: Path) -> Path:
    return _write_runner(
        tmp_dir / "tasks" / "sh_runner_task_malformed_no_required_file",
        SH_RUNNER_TASK_NO_REQUIRED_FILE_METADATA,
    )


@pytest.fixture
def sh_runner_task_wrong_version_dir(tmp_dir: Path) -> Path:
    return _write_task(
        tmp_dir / "tasks" / "sh_runner_task_malformed_wrong_runner_version",
        SH_RUNNER_TASK_WRONG_VERSION_METADATA,
    )


# ── Metadata fixtures ────────────────────────────────────────────────────


@pytest.fixture
def runner_metadata(tmp_dir: Path) -> RunnerMetadata:
    path = _write_runner(tmp_dir / "_meta_runner", SH_RUNNER_METADATA)
    return RunnerMetadata.load(path / "metadata.toml")


@pytest.fixture
def task_metadata(tmp_dir: Path) -> TaskMetadata:
    path = _write_task(tmp_dir / "_meta_task", SH_RUNNER_TASK_METADATA)
    return TaskMetadata.load(path / "metadata.toml")


# ── App state fixture (legacy) ────────────────────────────────────────────


@pytest.fixture
def app_state_fixture(tmp_dir: Path) -> Any:
    _runners_dir = tmp_dir / "runners"
    _tmp_dir = tmp_dir / ".tmp"

    class FakeAppState:
        runners_dir: Path = _runners_dir
        tmp_dir: Path = _tmp_dir
        runners: dict = {}
        session_id = "test-session"
        app_version = "0.1.0"

        def ensure_dirs(self) -> None:
            self.runners_dir.mkdir(parents=True, exist_ok=True)
            self.tmp_dir.mkdir(parents=True, exist_ok=True)

    state = FakeAppState()
    state.ensure_dirs()
    return state


# ── Pilot-driven fixtures ─────────────────────────────────────────────────


@pytest.fixture
def app(tmp_dir: Path) -> TermuxTaskerApp:
    """Create a TermuxTaskerApp configured with tmp_dir as work directory."""
    from termux_tasker.app import TermuxTaskerApp

    app = TermuxTaskerApp(app_version="0.1.0")
    app.state.work_dir = tmp_dir
    app.state.runners_dir = tmp_dir / "runners"
    app.state.tmp_dir = tmp_dir / ".tmp"
    app.state.app_config_file = tmp_dir / "app.toml"
    app.state.ensure_dirs()
    return app


# ── Mocks for external operations (git clone, file copy, etc.) ─────────


@pytest.fixture(autouse=True)
def mock_external_ops(monkeypatch):
    """Mock git/filesystem operations so BDD tests don't need a real git binary or network."""
    import re
    import uuid
    from pathlib import Path

    _GITHUB_URL_RE = re.compile(
        r"^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(\.git)?$"
    )

    def _mock_clone_repo(url: str, tmp_dir: Path, prefix: str) -> Path | None:
        if not _GITHUB_URL_RE.match(url):
            return None
        tmp_folder = tmp_dir / f"{prefix}_{uuid.uuid4().hex}"
        tmp_folder.mkdir(parents=True, exist_ok=True)
        (tmp_folder / "metadata.toml").write_text(SH_RUNNER_METADATA)
        return tmp_folder

    def _mock_copy_to_tmp(src: Path, tmp_dir: Path, prefix: str) -> Path:
        tmp_folder = tmp_dir / f"{prefix}_{uuid.uuid4().hex}"
        tmp_folder.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, tmp_folder, dirs_exist_ok=True)
        return tmp_folder

    def _mock_fetch_git_tags(_repo_path: Path) -> tuple[list[str], str]:
        return ["v1.0.0"], "main"

    def _mock_git_checkout(_repo_path: Path, _tag: str) -> bool:
        return True

    _CLONE_MODULES = [
        "termux_tasker.ui.screens._utils",
        "termux_tasker.ui.screens.runner_type",
        "termux_tasker.ui.screens.task_type",
        "termux_tasker.ui.screens.bundled_runner",
        "termux_tasker.ui.screens.bundled_task",
    ]
    for mod_name in _CLONE_MODULES:
        try:
            monkeypatch.setattr(f"{mod_name}.clone_repo", _mock_clone_repo)
        except AttributeError:
            pass

    _COPY_MODULES = [
        "termux_tasker.ui.screens._utils",
        "termux_tasker.ui.screens.runner_type",
        "termux_tasker.ui.screens.task_type",
    ]
    for mod_name in _COPY_MODULES:
        try:
            monkeypatch.setattr(f"{mod_name}.copy_to_tmp", _mock_copy_to_tmp)
        except AttributeError:
            pass

    _TAG_MODULES = [
        "termux_tasker.ui.screens._utils",
        "termux_tasker.ui.screens.install_runner_version",
        "termux_tasker.ui.screens.install_task_version",
    ]
    for mod_name in _TAG_MODULES:
        try:
            monkeypatch.setattr(f"{mod_name}.fetch_git_tags", _mock_fetch_git_tags)
        except AttributeError:
            pass

    _CHECKOUT_MODULES = [
        "termux_tasker.ui.screens._utils",
        "termux_tasker.ui.screens.install_runner_version",
        "termux_tasker.ui.screens.install_task_version",
    ]
    for mod_name in _CHECKOUT_MODULES:
        try:
            monkeypatch.setattr(f"{mod_name}.git_checkout", _mock_git_checkout)
        except AttributeError:
            pass


@pytest.fixture
def pilot(app: TermuxTaskerApp, tmp_dir: Path) -> Iterator[PilotDriver]:
    """Start the app in headless mode and return a sync PilotDriver.

    Sets up a basic runner (sh_runner) on disk before launching so
    that the app finds it when it reads the runner's directory.
    """
    from termux_tasker.config import RunnerSettings, TaskSettings

    # Set up a basic runner on disk before the app starts
    runner_dst = tmp_dir / "runners" / "sh_runner"
    _write_runner(runner_dst, SH_RUNNER_METADATA)
    settings = RunnerSettings()
    settings.general.enabled = False
    settings.session.session_id = "test-session"
    settings.session.state = "off"
    settings.save(runner_dst / "settings.toml")

    # Set up a basic task under the runner
    task_dst = runner_dst / "tasks" / "sh_runner_task"
    _write_task(task_dst, SH_RUNNER_TASK_METADATA)
    task_settings = TaskSettings()
    task_settings.general.enabled = False
    task_settings.session.session_id = "test-session"
    task_settings.session.state = "stopped"
    task_settings.save(task_dst / "settings.toml")

    from tests.bdd.pilot_driver import PilotDriver

    driver = PilotDriver(app)
    driver.start()
    yield driver
    driver.stop()
