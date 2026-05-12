from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from termux_tasker.runner_process import (
    RunnerProcess,
    _parse_timeout,
)


RUNNER_METADATA = """\
[general]
id = "test-runner"
name = "Test Runner"
version = "0.1.0"
app_min_version = ">=0.1.0"

[exec]
task-exec = "echo {task_dir}"
"""


class TestParseTimeout:
    def test_hours(self) -> None:
        assert _parse_timeout("2h") == 7200

    def test_minutes(self) -> None:
        assert _parse_timeout("30m") == 1800

    def test_seconds(self) -> None:
        assert _parse_timeout("45s") == 45

    def test_default(self) -> None:
        assert _parse_timeout("invalid") == 60


class TestRunnerProcessInit:
    def test_init(self, tmp_dir: Path) -> None:
        runner_dir = tmp_dir / "runner"
        runner_dir.mkdir()
        (runner_dir / "metadata.toml").write_text(RUNNER_METADATA)

        proc = RunnerProcess(runner_dir, "test-session", tmp_dir / ".tmp")
        assert proc.runner_dir == runner_dir
        assert proc.session_id == "test-session"
        assert proc.shutting_down is False


@pytest.mark.asyncio
class TestRunnerProcessRun:
    @patch("termux_tasker.runner_process.asyncio.create_subprocess_exec")
    async def test_run_basic(self, mock_subprocess, tmp_dir: Path) -> None:
        runner_dir = tmp_dir / "runner"
        runner_dir.mkdir()
        (runner_dir / "metadata.toml").write_text(RUNNER_METADATA)
        (runner_dir / "settings.toml").write_text('''\
[general]
enabled = true
timeout = "1m"

[properties]

[session]
session_id = "none"
state = "off"
''')

        tasks_dir = runner_dir / "tasks"
        tasks_dir.mkdir()

        mock_proc = AsyncMock()
        mock_proc.wait.return_value = 0
        mock_subprocess.return_value = mock_proc

        proc = RunnerProcess(runner_dir, "test-session", tmp_dir / ".tmp")
        proc.shutting_down = True
        proc._run_lock = False

        await proc._run_loop()

        assert proc.settings.session.state == "off"

    @patch("termux_tasker.runner_process.asyncio.create_subprocess_exec")
    async def test_run_with_error(self, mock_subprocess, tmp_dir: Path) -> None:
        runner_dir = tmp_dir / "runner"
        runner_dir.mkdir()
        (runner_dir / "metadata.toml").write_text(RUNNER_METADATA)
        (runner_dir / "settings.toml").write_text('''\
[general]
enabled = true
timeout = "1m"

[properties]

[session]
session_id = "none"
state = "off"
''')

        tasks_dir = runner_dir / "tasks"
        tasks_dir.mkdir()

        mock_proc = AsyncMock()
        mock_proc.wait.return_value = 1
        mock_subprocess.return_value = mock_proc

        proc = RunnerProcess(runner_dir, "test-session", tmp_dir / ".tmp")
        proc.shutting_down = True
        proc._run_lock = False

        await proc._run_loop()
        assert proc.settings.session.state == "off"


class TestRunnerProcessShutdown:
    @patch("termux_tasker.runner_process.asyncio.create_subprocess_exec")
    async def test_shutdown(self, mock_subprocess, tmp_dir: Path) -> None:
        runner_dir = tmp_dir / "runner"
        runner_dir.mkdir()
        (runner_dir / "metadata.toml").write_text(RUNNER_METADATA)
        (runner_dir / "settings.toml").write_text('''\
[general]
enabled = true
timeout = "1m"

[properties]

[session]
session_id = "none"
state = "off"
''')

        tasks_dir = runner_dir / "tasks"
        tasks_dir.mkdir()

        mock_proc = AsyncMock()
        mock_proc.wait.return_value = 0
        mock_subprocess.return_value = mock_proc

        proc = RunnerProcess(runner_dir, "test-session", tmp_dir / ".tmp")
        proc.shutting_down = True

        await proc.shutdown()


class TestRunnerProcessTerminate:
    def test_terminate(self, tmp_dir: Path) -> None:
        runner_dir = tmp_dir / "runner"
        runner_dir.mkdir()
        (runner_dir / "metadata.toml").write_text(RUNNER_METADATA)

        proc = RunnerProcess(runner_dir, "test-session", tmp_dir / ".tmp")
        proc.terminate()
