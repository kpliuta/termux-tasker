from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from termux_tasker.runner_process import (
    RunnerProcess,
    _parse_timeout, # noqa
)


RUNNER_METADATA = """\
[general]
id = "test-runner"
name = "Test Runner"
version = "0.1.0"
app_min_version = ">=0.1.0"

[exec]
task-exec = "echo {task_path}"
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
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_METADATA)

        proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
        assert proc.runner_path == runner_path
        assert proc.session_id == "test-session"
        assert proc.shutting_down is False


@pytest.mark.asyncio
class TestRunnerProcessRun:
    @patch("termux_tasker.runner_process.asyncio.create_subprocess_exec")
    async def test_run_basic(self, mock_subprocess, tmp_dir: Path) -> None:
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_METADATA)
        (runner_path / "settings.toml").write_text('''\
[general]
enabled = true
timeout = "1m"

[properties]

[session]
session_id = "none"
state = "off"
''')

        tasks_path = runner_path / "tasks"
        tasks_path.mkdir()

        mock_proc = AsyncMock()
        mock_proc.wait.return_value = 0
        mock_subprocess.return_value = mock_proc

        proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
        proc.shutting_down = True
        proc._run_lock = False

        await proc._run_loop()

        assert proc.settings.session.state == "off"

    @patch("termux_tasker.runner_process.asyncio.create_subprocess_exec")
    async def test_run_with_error(self, mock_subprocess, tmp_dir: Path) -> None:
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_METADATA)
        (runner_path / "settings.toml").write_text('''\
[general]
enabled = true
timeout = "1m"

[properties]

[session]
session_id = "none"
state = "off"
''')

        tasks_path = runner_path / "tasks"
        tasks_path.mkdir()

        mock_proc = AsyncMock()
        mock_proc.wait.return_value = 1
        mock_subprocess.return_value = mock_proc

        proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
        proc.shutting_down = True
        proc._run_lock = False

        await proc._run_loop()
        assert proc.settings.session.state == "off"


class TestRunnerProcessShutdown:
    @patch("termux_tasker.runner_process.asyncio.create_subprocess_exec")
    async def test_shutdown(self, mock_subprocess, tmp_dir: Path) -> None:
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_METADATA)
        (runner_path / "settings.toml").write_text('''\
[general]
enabled = true
timeout = "1m"

[properties]

[session]
session_id = "none"
state = "off"
''')

        tasks_path = runner_path / "tasks"
        tasks_path.mkdir()

        mock_proc = AsyncMock()
        mock_proc.wait.return_value = 0
        mock_subprocess.return_value = mock_proc

        proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
        proc.shutting_down = True

        await proc.shutdown()


class TestRunnerProcessRunLock:
    def test_run_lock_prevents_concurrent_starts(self, tmp_dir: Path) -> None:
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_METADATA)

        proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
        proc._run_lock = True
        result = proc.run()
        assert result is False


class TestRunnerProcessTerminate:
    def test_terminate(self, tmp_dir: Path) -> None:
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_METADATA)

        proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
        proc.terminate()

    def test_terminate_calls_on_all_tracked_subprocesses(self, tmp_dir: Path) -> None:
        from unittest.mock import MagicMock

        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_METADATA)

        proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
        mock_proc = MagicMock()
        proc._processes = [mock_proc]
        proc.terminate()
        mock_proc.terminate.assert_called_once()


class TestToEnvKey:
    def test_property_name_conversion(self) -> None:
        from termux_tasker.runner_process import _to_env_key    # noqa

        assert _to_env_key("property-1") == "VAR_PROPERTY_1"
        assert _to_env_key("my property") == "VAR_MY_PROPERTY"
        assert _to_env_key("prop.name") == "VAR_PROP_NAME"


class TestAppSessionId:
    def test_unique_session_id_is_generated(self) -> None:
        from termux_tasker.app_state import AppState

        state = AppState("0.1.0")
        assert len(state.session_id) == 36
        assert state.session_id.count("-") == 4
