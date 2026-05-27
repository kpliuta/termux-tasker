from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

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
initialization = "echo {runner_path}"
task-exec = "echo {task_path}"
termination = "echo {runner_path}"
"""

SETTINGS = """\
[general]
enabled = true
timeout = "1m"

[properties]

[session]
session_id = "none"
state = "off"
"""

TASK_METADATA = """\
[general]
id = "test-task"
name = "Test Task"
version = "1"
runner_id = "test-runner"
runner_min_version = ">=0.1.0"
default_timeout = "1m"
"""

TASK_SETTINGS = """\
[general]
enabled = true
timeout = "1m"

[properties]

[session]
session_id = "none"
state = "stopped"
"""


def _mock_proc(return_code: int = 0) -> AsyncMock:
    mock_proc = AsyncMock()
    mock_proc.wait.return_value = return_code
    mock_proc.stdout = AsyncMock()
    mock_proc.stdout.readline = AsyncMock(return_value=b"")
    return mock_proc


def _write_runner(tmp_dir: Path) -> Path:
    runner_path = tmp_dir / "runner"
    runner_path.mkdir()
    (runner_path / "metadata.toml").write_text(RUNNER_METADATA)
    (runner_path / "settings.toml").write_text(SETTINGS)
    (runner_path / "tasks").mkdir()
    return runner_path


def _write_task(runner_path: Path) -> Path:
    task_path = runner_path / "tasks" / "test-task"
    task_path.mkdir()
    (task_path / "metadata.toml").write_text(TASK_METADATA)
    (task_path / "settings.toml").write_text(TASK_SETTINGS)
    return task_path


def _create_proc(runner_path: Path, tmp_dir: Path) -> RunnerProcess:
    proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
    proc.shutting_down = True
    proc._run_lock = False
    return proc


def _assert_placeholder_substituted(
    cmd: str, runner_path: Path, task_path: Path | None = None,
    task_dir_name: str | None = None,
    expect_runner_path: bool = True,
) -> None:
    if expect_runner_path:
        assert str(runner_path) in cmd
        assert "{runner_path}" not in cmd
    if task_path:
        assert str(task_path) in cmd
        assert "{task_path}" not in cmd
    if task_dir_name:
        assert task_dir_name in cmd
        assert "{task_dir_name}" not in cmd


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
        runner_path = _write_runner(tmp_dir)

        proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
        assert proc.runner_path == runner_path
        assert proc.session_id == "test-session"
        assert proc.shutting_down is False


@pytest.mark.asyncio
class TestRunnerProcessRun:
    @patch("termux_tasker.runner_process.asyncio.create_subprocess_exec")
    async def test_run_with_error(self, mock_subprocess: AsyncMock, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        mock_subprocess.return_value = _mock_proc(return_code=1)

        proc = _create_proc(runner_path, tmp_dir)
        await proc._run_loop()

        assert proc.settings.session.state == "off"


class TestRunnerProcessShutdown:
    @patch("termux_tasker.runner_process.asyncio.create_subprocess_exec")
    async def test_shutdown(self, mock_subprocess: AsyncMock, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        mock_subprocess.return_value = _mock_proc()

        proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
        proc.shutting_down = True

        await proc.shutdown()


class TestRunnerProcessRunLock:
    def test_run_lock_prevents_concurrent_starts(self, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
        proc._run_lock = True
        result = proc.run()
        assert result is False


class TestRunnerProcessTerminate:
    def test_terminate_calls_on_all_tracked_subprocesses(self, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
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


@pytest.mark.asyncio
class TestOutputDir:
    @patch("termux_tasker.runner_process.asyncio.create_subprocess_exec")
    async def test_output_dir_created_before_task_exec(self, mock_subprocess: AsyncMock, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        task_path = _write_task(runner_path)
        mock_subprocess.return_value = _mock_proc()

        proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
        proc.shutting_down = False
        proc._run_lock = False
        loop_task = asyncio.create_task(proc._run_loop())
        await asyncio.sleep(0.05)
        proc.shutting_down = True
        await loop_task

        output_dir = task_path / "output"
        assert output_dir.exists()
        assert output_dir.is_dir()

    @patch("termux_tasker.runner_process.asyncio.create_subprocess_exec")
    async def test_output_dir_env_var_set_when_task_path_provided(self, mock_subprocess: AsyncMock, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        task_path = _write_task(runner_path)
        mock_subprocess.return_value = _mock_proc()

        proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
        await proc._run_task_cmd("echo test", task_path)

        env = mock_subprocess.call_args.kwargs["env"]
        assert "OUTPUT_DIR" in env
        assert env["OUTPUT_DIR"] == str(task_path / "output")

    @patch("termux_tasker.runner_process.asyncio.create_subprocess_exec")
    async def test_output_dir_env_var_not_set_without_task_path(self, mock_subprocess: AsyncMock, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        mock_subprocess.return_value = _mock_proc()

        proc = _create_proc(runner_path, tmp_dir)
        await proc._run_loop()

        for call in mock_subprocess.call_args_list:
            env = call.kwargs["env"]
            assert "OUTPUT_DIR" not in env, f"OUTPUT_DIR was set in env for call: {call}"


@pytest.mark.asyncio
class TestPlaceholderSubstitution:
    @patch("termux_tasker.runner_process.asyncio.create_subprocess_exec")
    async def test_runner_path_in_initialization(self, mock_subprocess: AsyncMock, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        mock_subprocess.return_value = _mock_proc()

        proc = _create_proc(runner_path, tmp_dir)
        await proc._run_loop()

        _assert_placeholder_substituted(mock_subprocess.call_args_list[0].args[2], runner_path)

    @patch("termux_tasker.runner_process.asyncio.create_subprocess_exec")
    async def test_runner_path_in_termination(self, mock_subprocess: AsyncMock, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        mock_subprocess.return_value = _mock_proc()

        proc = _create_proc(runner_path, tmp_dir)
        await proc._run_loop()

        _assert_placeholder_substituted(mock_subprocess.call_args_list[1].args[2], runner_path)

    @patch("termux_tasker.runner_process.asyncio.create_subprocess_exec")
    async def test_task_path_in_task_exec(self, mock_subprocess: AsyncMock, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        task_path = _write_task(runner_path)
        mock_subprocess.return_value = _mock_proc()

        proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
        await proc._run_task_cmd("echo {task_path}", task_path)

        _assert_placeholder_substituted(
            mock_subprocess.call_args.args[2], runner_path, task_path,
            expect_runner_path=False,
        )

    @patch("termux_tasker.runner_process.asyncio.create_subprocess_exec")
    async def test_task_dir_name_in_task_exec(self, mock_subprocess: AsyncMock, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        task_path = _write_task(runner_path)
        mock_subprocess.return_value = _mock_proc()

        proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
        await proc._run_task_cmd("echo {task_path} {task_dir_name}", task_path)

        _assert_placeholder_substituted(
            mock_subprocess.call_args.args[2], runner_path, task_path,
            task_dir_name=task_path.name,
            expect_runner_path=False,
        )

    @patch("termux_tasker.runner_process.asyncio.create_subprocess_exec")
    async def test_runner_path_not_resolved_in_task_exec(self, mock_subprocess: AsyncMock, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        task_path = _write_task(runner_path)
        mock_subprocess.return_value = _mock_proc()

        proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
        await proc._run_task_cmd("echo {runner_path}", task_path)

        cmd = mock_subprocess.call_args.args[2]
        assert "{runner_path}" in cmd
        assert str(runner_path) not in cmd
