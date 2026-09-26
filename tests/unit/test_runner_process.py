from __future__ import annotations

import asyncio
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from termux_tasker.config import RunnerSettings, TaskSettings
from termux_tasker.runner_process import (
    RunnerProcess,
    _to_env_key, # noqa
)
from termux_tasker.app_state import AppState

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
        assert _to_env_key("property-1") == "VAR_PROPERTY_1"
        assert _to_env_key("my property") == "VAR_MY_PROPERTY"
        assert _to_env_key("prop.name") == "VAR_PROP_NAME"


class TestAppSessionId:
    def test_unique_session_id_is_generated(self) -> None:
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
        )

    @patch("termux_tasker.runner_process.asyncio.create_subprocess_exec")
    async def test_runner_path_resolved_in_task_exec(self, mock_subprocess: AsyncMock, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        task_path = _write_task(runner_path)
        mock_subprocess.return_value = _mock_proc()

        proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
        await proc._run_task_cmd("echo {runner_path}", task_path)

        cmd = mock_subprocess.call_args.args[2]
        assert "{runner_path}" not in cmd
        assert str(runner_path) in cmd


def _load_runner_settings_fresh(runner_path: Path) -> RunnerSettings:
    RunnerSettings.clear_cache(runner_path / "settings.toml")
    return RunnerSettings.load(runner_path / "settings.toml")


def _load_task_settings_fresh(task_path: Path) -> TaskSettings:
    TaskSettings.clear_cache(task_path / "settings.toml")
    return TaskSettings.load(task_path / "settings.toml")


@pytest.mark.asyncio
class TestRunnerLastRun:
    async def _run_until_last_run(
        self, proc: RunnerProcess, runner_path: Path
    ) -> RunnerSettings:
        proc.shutting_down = False
        loop_task = asyncio.create_task(proc._run_loop())
        deadline = asyncio.get_event_loop().time() + 5.0
        last_settings = _load_runner_settings_fresh(runner_path)
        while last_settings.session.last_run == "none":
            if asyncio.get_event_loop().time() > deadline:
                proc.shutting_down = True
                await loop_task
                raise AssertionError("runner last_run was never written")
            await asyncio.sleep(0.05)
            last_settings = _load_runner_settings_fresh(runner_path)
        proc.shutting_down = True
        await loop_task
        return _load_runner_settings_fresh(runner_path)

    async def test_last_run_written_after_cycle(self, tmp_dir: Path) -> None:
        with patch(
            "termux_tasker.runner_process.asyncio.create_subprocess_exec",
            return_value=_mock_proc(),
        ):
            runner_path = _write_runner(tmp_dir)
            proc = _create_proc(runner_path, tmp_dir)
            settings = await self._run_until_last_run(proc, runner_path)
            assert settings.session.last_run != "none"

    async def test_last_run_format_matches_task_format(self, tmp_dir: Path) -> None:
        with patch(
            "termux_tasker.runner_process.asyncio.create_subprocess_exec",
            return_value=_mock_proc(),
        ):
            runner_path = _write_runner(tmp_dir)
            proc = _create_proc(runner_path, tmp_dir)
            settings = await self._run_until_last_run(proc, runner_path)
            assert re.match(
                r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$",
                settings.session.last_run,
            )
            datetime.strptime(settings.session.last_run, "%Y-%m-%d %H:%M:%S")

    async def test_last_run_updates_session_id(self, tmp_dir: Path) -> None:
        with patch(
            "termux_tasker.runner_process.asyncio.create_subprocess_exec",
            return_value=_mock_proc(),
        ):
            runner_path = _write_runner(tmp_dir)
            proc = _create_proc(runner_path, tmp_dir)
            settings = await self._run_until_last_run(proc, runner_path)
            assert settings.session.session_id == "test-session"

    async def test_last_run_status_untouched(self, tmp_dir: Path) -> None:
        with patch(
            "termux_tasker.runner_process.asyncio.create_subprocess_exec",
            return_value=_mock_proc(),
        ):
            runner_path = _write_runner(tmp_dir)
            proc = _create_proc(runner_path, tmp_dir)
            settings = await self._run_until_last_run(proc, runner_path)
            assert not hasattr(settings.session, "last_run_status")

    async def test_last_run_preserved_after_shutdown(self, tmp_dir: Path) -> None:
        with patch(
            "termux_tasker.runner_process.asyncio.create_subprocess_exec",
            return_value=_mock_proc(),
        ):
            runner_path = _write_runner(tmp_dir)
            proc = _create_proc(runner_path, tmp_dir)
            settings = await self._run_until_last_run(proc, runner_path)
            assert settings.session.state == "off"
            assert settings.session.last_run != "none"

    async def test_last_run_written_with_tasks_present(self, tmp_dir: Path) -> None:
        with patch(
            "termux_tasker.runner_process.asyncio.create_subprocess_exec",
            return_value=_mock_proc(),
        ):
            runner_path = _write_runner(tmp_dir)
            task_path = _write_task(runner_path)
            proc = _create_proc(runner_path, tmp_dir)
            runner_settings = await self._run_until_last_run(proc, runner_path)
            task_settings = _load_task_settings_fresh(task_path)
            assert runner_settings.session.last_run != "none"
            assert task_settings.session.last_run != "none"

    async def test_no_last_run_when_cycle_never_completes(
        self, tmp_dir: Path
    ) -> None:
        with patch(
            "termux_tasker.runner_process.asyncio.create_subprocess_exec",
            return_value=_mock_proc(return_code=1),
        ):
            runner_path = _write_runner(tmp_dir)
            proc = _create_proc(runner_path, tmp_dir)
            await proc._run_loop()

            settings = _load_runner_settings_fresh(runner_path)
            assert settings.session.last_run == "none"


FULL_PHASES_METADATA = """\
[general]
id = "test-runner"
name = "Test Runner"
version = "0.1.0"
app_min_version = ">=0.1.0"

[exec]
initialization = "echo init"
before-exec = "echo before-exec"
before-task = "echo before-task"
task-exec = "echo task-exec"
after-task = "echo after-task"
after-exec = "echo after-exec"
termination = "echo termination"
"""


def _write_full_runner(tmp_dir: Path) -> Path:
    runner_path = tmp_dir / "runner"
    runner_path.mkdir()
    (runner_path / "metadata.toml").write_text(FULL_PHASES_METADATA)
    (runner_path / "settings.toml").write_text(SETTINGS)
    (runner_path / "tasks").mkdir()
    return runner_path


class TestSessionDurationsConfig:
    def test_defaults_are_none(self) -> None:
        s = TaskSettings()
        assert s.session.last_run_before_duration is None
        assert s.session.last_run_exec_duration is None
        assert s.session.last_run_after_duration is None
        r = RunnerSettings()
        assert r.session.last_run_init_duration is None
        assert r.session.last_run_before_duration is None
        assert r.session.last_run_exec_duration is None
        assert r.session.last_run_after_duration is None

    def test_omitted_from_file_when_never_run(self, tmp_dir: Path) -> None:
        path = tmp_dir / "settings.toml"
        TaskSettings().save(path)
        content = path.read_text()
        assert "last_run_init_duration" not in content
        assert "last_run_before_duration" not in content
        assert "last_run_exec_duration" not in content
        assert "last_run_after_duration" not in content
        RunnerSettings().save(path)
        content = path.read_text()
        assert "last_run_init_duration" not in content
        assert "last_run_before_duration" not in content
        assert "last_run_exec_duration" not in content
        assert "last_run_after_duration" not in content

    def test_round_trip_int_values(self, tmp_dir: Path) -> None:
        path = tmp_dir / "settings.toml"
        s = TaskSettings()
        s.session.last_run_before_duration = 1
        s.session.last_run_exec_duration = 2
        s.session.last_run_after_duration = 3
        s.save(path)
        loaded = _load_task_settings_fresh(path.parent)
        assert loaded.session.last_run_before_duration == 1
        assert loaded.session.last_run_exec_duration == 2
        assert loaded.session.last_run_after_duration == 3

    def test_runner_round_trip_init_value(self, tmp_dir: Path) -> None:
        path = tmp_dir / "settings.toml"
        s = RunnerSettings()
        s.session.last_run_init_duration = 4
        s.save(path)
        loaded = _load_runner_settings_fresh(path.parent)
        assert loaded.session.last_run_init_duration == 4

    def test_malformed_values_load_as_none(self, tmp_dir: Path) -> None:
        path = tmp_dir / "settings.toml"
        path.write_text(
            "[general]\nenabled = true\ntimeout = \"1m\"\n"
            "[properties]\n[log]\nsoft_wrap = false\n"
            "auto_scroll = false\noffset = 0\n"
            "[session]\nsession_id = \"none\"\nstate = \"off\"\n"
            "last_run_before_duration = \"oops\"\n"
            "last_run_exec_duration = \"oops\"\n"
            "last_run_after_duration = \"oops\"\n"
        )
        loaded = _load_task_settings_fresh(path.parent)
        assert loaded.session.last_run_before_duration is None
        assert loaded.session.last_run_exec_duration is None
        assert loaded.session.last_run_after_duration is None

    def test_malformed_init_loads_as_none(self, tmp_dir: Path) -> None:
        path = tmp_dir / "settings.toml"
        path.write_text(
            "[general]\nenabled = true\ntimeout = \"1m\"\n"
            "[properties]\n[log]\nsoft_wrap = false\n"
            "auto_scroll = false\noffset = 0\n"
            "[session]\nsession_id = \"none\"\nstate = \"off\"\n"
            "last_run_init_duration = \"oops\"\n"
        )
        loaded = _load_runner_settings_fresh(path.parent)
        assert loaded.session.last_run_init_duration is None


class TestSettingsSplit:
    def test_task_has_no_init_duration(self) -> None:
        assert not hasattr(TaskSettings().session, "last_run_init_duration")

    def test_runner_has_no_last_run_status(self) -> None:
        assert not hasattr(RunnerSettings().session, "last_run_status")

    def test_caches_are_independent(self, tmp_dir: Path) -> None:
        runner_file = tmp_dir / "runner.toml"
        task_file = tmp_dir / "task.toml"
        RunnerSettings().save(runner_file)
        TaskSettings().save(task_file)
        RunnerSettings.clear_cache(runner_file)
        assert task_file in TaskSettings._instances  # noqa
        assert runner_file not in RunnerSettings._instances  # noqa

    def test_task_ignores_runner_only_keys(self, tmp_dir: Path) -> None:
        path = tmp_dir / "settings.toml"
        path.write_text(
            "[general]\nenabled = true\ntimeout = \"1m\"\n"
            "[properties]\n[log]\nsoft_wrap = false\n"
            "auto_scroll = false\noffset = 0\n"
            "[session]\nsession_id = \"none\"\nstate = \"stopped\"\n"
            "last_run_status = \"success\"\n"
            "last_run_init_duration = 7\n"
        )
        loaded = _load_task_settings_fresh(path.parent)
        assert loaded.session.last_run_status == "success"
        assert not hasattr(loaded.session, "last_run_init_duration")

    def test_runner_ignores_task_only_keys(self, tmp_dir: Path) -> None:
        path = tmp_dir / "settings.toml"
        path.write_text(
            "[general]\nenabled = true\ntimeout = \"1m\"\n"
            "[properties]\n[log]\nsoft_wrap = false\n"
            "auto_scroll = false\noffset = 0\n"
            "[session]\nsession_id = \"none\"\nstate = \"off\"\n"
            "last_run_status = \"success\"\n"
            "last_run_init_duration = 7\n"
        )
        loaded = _load_runner_settings_fresh(path.parent)
        assert loaded.session.last_run_init_duration == 7
        assert not hasattr(loaded.session, "last_run_status")


@pytest.mark.asyncio
class TestTaskLastRunDurations:
    async def _run_until_task_durations(
        self, proc: RunnerProcess, task_path: Path
    ) -> TaskSettings:
        proc.shutting_down = False
        loop_task = asyncio.create_task(proc._run_loop())
        deadline = asyncio.get_event_loop().time() + 5.0
        last_settings = _load_task_settings_fresh(task_path)
        while last_settings.session.last_run_exec_duration is None:
            if asyncio.get_event_loop().time() > deadline:
                proc.shutting_down = True
                await loop_task
                raise AssertionError("task durations were never written")
            await asyncio.sleep(0.05)
            last_settings = _load_task_settings_fresh(task_path)
        proc.shutting_down = True
        await loop_task
        return _load_task_settings_fresh(task_path)

    async def test_durations_written_after_task_cycle(self, tmp_dir: Path) -> None:
        with patch(
            "termux_tasker.runner_process.asyncio.create_subprocess_exec",
            return_value=_mock_proc(),
        ):
            runner_path = _write_full_runner(tmp_dir)
            task_path = _write_task(runner_path)
            proc = _create_proc(runner_path, tmp_dir)
            settings = await self._run_until_task_durations(proc, task_path)
            assert isinstance(settings.session.last_run_before_duration, int)
            assert isinstance(settings.session.last_run_exec_duration, int)
            assert isinstance(settings.session.last_run_after_duration, int)
            assert settings.session.last_run_before_duration >= 0
            assert settings.session.last_run_exec_duration >= 0
            assert settings.session.last_run_after_duration >= 0
            assert settings.session.last_run != "none"

    async def test_skipped_phases_record_zero(self, tmp_dir: Path) -> None:
        with patch(
            "termux_tasker.runner_process.asyncio.create_subprocess_exec",
            return_value=_mock_proc(),
        ):
            runner_path = _write_runner(tmp_dir)
            task_path = _write_task(runner_path)
            proc = _create_proc(runner_path, tmp_dir)
            settings = await self._run_until_task_durations(proc, task_path)
            assert settings.session.last_run_before_duration == 0
            assert settings.session.last_run_after_duration == 0
            assert isinstance(settings.session.last_run_exec_duration, int)

    async def test_durations_written_on_task_failure(self, tmp_dir: Path) -> None:
        calls = {"count": 0}

        async def _fail_task_exec(*args: object, **kwargs: object) -> AsyncMock:
            calls["count"] += 1
            # Call order with full phases: init, before-exec, before-task,
            # task-exec, after-task, after-exec, termination, ...
            # Fail only the first task-exec attempt.
            if calls["count"] == 4:
                return _mock_proc(return_code=1)
            return _mock_proc()

        with patch(
            "termux_tasker.runner_process.asyncio.create_subprocess_exec",
            side_effect=_fail_task_exec,
        ):
            runner_path = _write_full_runner(tmp_dir)
            task_path = _write_task(runner_path)
            proc = _create_proc(runner_path, tmp_dir)
            settings = await self._run_until_task_durations(proc, task_path)
            assert settings.session.last_run_status == "fail"
            assert isinstance(settings.session.last_run_exec_duration, int)
            assert settings.session.last_run_exec_duration >= 0
            assert isinstance(settings.session.last_run_before_duration, int)
            assert isinstance(settings.session.last_run_after_duration, int)

    async def test_no_durations_when_task_never_runs(self, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        task_path = _write_task(runner_path)
        settings = _load_task_settings_fresh(task_path)
        assert settings.session.last_run_before_duration is None
        assert settings.session.last_run_exec_duration is None
        assert settings.session.last_run_after_duration is None
        content = (task_path / "settings.toml").read_text()
        assert "last_run_before_duration" not in content
        assert "last_run_exec_duration" not in content
        assert "last_run_after_duration" not in content


@pytest.mark.asyncio
class TestRunnerLastRunDurations:
    async def _run_until_runner_durations(
        self, proc: RunnerProcess, runner_path: Path
    ) -> RunnerSettings:
        proc.shutting_down = False
        loop_task = asyncio.create_task(proc._run_loop())
        deadline = asyncio.get_event_loop().time() + 5.0
        last_settings = _load_runner_settings_fresh(runner_path)
        while last_settings.session.last_run_before_duration is None:
            if asyncio.get_event_loop().time() > deadline:
                proc.shutting_down = True
                await loop_task
                raise AssertionError("runner durations were never written")
            await asyncio.sleep(0.05)
            last_settings = _load_runner_settings_fresh(runner_path)
        proc.shutting_down = True
        await loop_task
        return _load_runner_settings_fresh(runner_path)

    async def test_durations_written_after_cycle(self, tmp_dir: Path) -> None:
        with patch(
            "termux_tasker.runner_process.asyncio.create_subprocess_exec",
            return_value=_mock_proc(),
        ):
            runner_path = _write_full_runner(tmp_dir)
            _write_task(runner_path)
            proc = _create_proc(runner_path, tmp_dir)
            settings = await self._run_until_runner_durations(proc, runner_path)
            assert settings.session.last_run != "none"
            for duration in (
                settings.session.last_run_init_duration,
                settings.session.last_run_before_duration,
                settings.session.last_run_exec_duration,
                settings.session.last_run_after_duration,
            ):
                assert isinstance(duration, int)
                assert duration >= 0

    async def test_skipped_phases_record_zero(self, tmp_dir: Path) -> None:
        with patch(
            "termux_tasker.runner_process.asyncio.create_subprocess_exec",
            return_value=_mock_proc(),
        ):
            runner_path = _write_runner(tmp_dir)
            proc = _create_proc(runner_path, tmp_dir)
            settings = await self._run_until_runner_durations(proc, runner_path)
            assert isinstance(settings.session.last_run_init_duration, int)
            assert isinstance(settings.session.last_run_exec_duration, int)
            assert settings.session.last_run_before_duration == 0
            assert settings.session.last_run_after_duration == 0

    async def test_init_duration_persists_after_shutdown(self, tmp_dir: Path) -> None:
        with patch(
            "termux_tasker.runner_process.asyncio.create_subprocess_exec",
            return_value=_mock_proc(),
        ):
            runner_path = _write_full_runner(tmp_dir)
            proc = _create_proc(runner_path, tmp_dir)
            settings = await self._run_until_runner_durations(proc, runner_path)
            assert settings.session.state == "off"
            assert isinstance(settings.session.last_run_init_duration, int)

    async def test_before_exec_failure_persists_durations(
        self, tmp_dir: Path
    ) -> None:
        calls = {"count": 0}

        async def _fail_before_exec(*args: object, **kwargs: object) -> AsyncMock:
            calls["count"] += 1
            # Call order: init, before-exec, ... — fail before-exec only.
            if calls["count"] == 2:
                return _mock_proc(return_code=1)
            return _mock_proc()

        with patch(
            "termux_tasker.runner_process.asyncio.create_subprocess_exec",
            side_effect=_fail_before_exec,
        ):
            runner_path = _write_full_runner(tmp_dir)
            proc = _create_proc(runner_path, tmp_dir)
            proc.shutting_down = False
            await asyncio.wait_for(proc._run_loop(), timeout=10)

            settings = _load_runner_settings_fresh(runner_path)
            assert settings.session.last_run != "none"
            assert isinstance(settings.session.last_run_init_duration, int)
            assert settings.session.last_run_init_duration >= 0
            assert isinstance(settings.session.last_run_before_duration, int)
            assert settings.session.last_run_before_duration >= 0

    async def test_no_durations_when_never_run(self, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        settings = _load_runner_settings_fresh(runner_path)
        assert settings.session.last_run_init_duration is None
        assert settings.session.last_run_before_duration is None
        assert settings.session.last_run_exec_duration is None
        assert settings.session.last_run_after_duration is None
        content = (runner_path / "settings.toml").read_text()
        assert "last_run_init_duration" not in content
        assert "last_run_before_duration" not in content
        assert "last_run_exec_duration" not in content
        assert "last_run_after_duration" not in content


NO_TERMINATION_METADATA = """\
[general]
id = "test-runner"
name = "Test Runner"
version = "0.1.0"
app_min_version = ">=0.1.0"

[exec]
initialization = "echo init"
"""


@pytest.mark.asyncio
class TestTerminationDuration:
    async def test_termination_duration_written(self, tmp_dir: Path) -> None:
        with patch(
            "termux_tasker.runner_process.asyncio.create_subprocess_exec",
            return_value=_mock_proc(),
        ):
            runner_path = _write_runner(tmp_dir)
            proc = _create_proc(runner_path, tmp_dir)
            await proc._run_loop()

            settings = _load_runner_settings_fresh(runner_path)
            assert isinstance(settings.session.last_run_termination_duration, int)
            assert settings.session.last_run_termination_duration >= 0

    async def test_undefined_termination_records_zero(self, tmp_dir: Path) -> None:
        with patch(
            "termux_tasker.runner_process.asyncio.create_subprocess_exec",
            return_value=_mock_proc(),
        ):
            runner_path = tmp_dir / "runner"
            runner_path.mkdir()
            (runner_path / "metadata.toml").write_text(NO_TERMINATION_METADATA)
            (runner_path / "settings.toml").write_text(SETTINGS)
            (runner_path / "tasks").mkdir()
            proc = _create_proc(runner_path, tmp_dir)
            await proc._run_loop()

            settings = _load_runner_settings_fresh(runner_path)
            assert settings.session.last_run_termination_duration == 0

    async def test_termination_omitted_when_never_run(self, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        settings = _load_runner_settings_fresh(runner_path)
        assert settings.session.last_run_termination_duration is None
        assert "last_run_termination_duration" not in (
            runner_path / "settings.toml"
        ).read_text()

    async def test_termination_round_trip(self, tmp_dir: Path) -> None:
        path = tmp_dir / "settings.toml"
        settings = RunnerSettings()
        settings.session.last_run_termination_duration = 7
        settings.save(path)
        loaded = _load_runner_settings_fresh(path.parent)
        assert loaded.session.last_run_termination_duration == 7

    async def test_malformed_termination_loads_as_none(self, tmp_dir: Path) -> None:
        path = tmp_dir / "settings.toml"
        path.write_text(
            "[general]\nenabled = true\ntimeout = \"1m\"\n"
            "[properties]\n[log]\nsoft_wrap = false\n"
            "auto_scroll = false\noffset = 0\n"
            "[session]\nsession_id = \"none\"\nstate = \"off\"\n"
            "last_run_termination_duration = \"oops\"\n"
        )
        loaded = _load_runner_settings_fresh(path.parent)
        assert loaded.session.last_run_termination_duration is None


class TestLiveTracking:
    def test_state_elapsed_counts_from_state_entry(self, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
        assert proc.state_elapsed(now=proc.state_started_monotonic) == 0
        assert proc.state_elapsed(now=proc.state_started_monotonic + 31) == 31

    def test_change_state_resets_elapsed(self, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
        proc._change_runner_state("idle")
        assert proc.state_elapsed(now=proc.state_started_monotonic + 105) == 105

    def test_count_runnable_tasks(self, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        proc = _create_proc(runner_path, tmp_dir)
        assert proc._count_runnable_tasks() == 0
        _write_task(runner_path)
        assert proc._count_runnable_tasks() == 1

    def test_disabled_tasks_excluded_from_count(self, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        task_path = _write_task(runner_path)
        task_settings = _load_task_settings_fresh(task_path)
        task_settings.general.enabled = False
        task_settings.save(task_path / "settings.toml")
        proc = _create_proc(runner_path, tmp_dir)
        assert proc._count_runnable_tasks() == 0

    def test_current_task_cleared_after_loop(self, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        proc = _create_proc(runner_path, tmp_dir)
        assert proc.current_task_path is None
        assert proc.exec_total == 0
        assert proc.exec_index == 0


def _blocking_task_exec_mock(release: asyncio.Event) -> AsyncMock:
    """Subprocess factory mock that parks inside task-exec until released."""
    created = _mock_proc()

    async def _create(*args: object, **kwargs: object) -> AsyncMock:
        cmd = str(args[2]) if len(args) > 2 else ""
        if "task-exec" in cmd:
            proc = _mock_proc()

            async def _wait_blocked() -> int:
                await release.wait()
                return 0

            proc.wait = _wait_blocked  # type: ignore[method-assign]
            return proc
        return created

    return _create  # type: ignore[return-value]


@pytest.mark.asyncio
class TestStartStampedSession:
    async def test_task_session_adopted_while_running(self, tmp_dir: Path) -> None:
        release = asyncio.Event()
        with patch(
            "termux_tasker.runner_process.asyncio.create_subprocess_exec",
            side_effect=_blocking_task_exec_mock(release),
        ):
            runner_path = _write_full_runner(tmp_dir)
            task_path = _write_task(runner_path)
            proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
            proc.shutting_down = False
            loop_task = asyncio.create_task(proc._run_loop())
            try:
                deadline = asyncio.get_event_loop().time() + 5.0
                while True:
                    task_settings = _load_task_settings_fresh(task_path)
                    if task_settings.session.state == "running":
                        break
                    if asyncio.get_event_loop().time() > deadline:
                        raise AssertionError("task never reached running state")
                    await asyncio.sleep(0.05)
                assert task_settings.session.session_id == "test-session"
                assert task_settings.session.last_run != "none"
                assert re.match(
                    r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$",
                    task_settings.session.last_run,
                )
                runner_settings = _load_runner_settings_fresh(runner_path)
                assert runner_settings.session.session_id == "test-session"
                assert runner_settings.session.last_run != "none"
            finally:
                release.set()
                proc.shutting_down = True
                await asyncio.wait_for(loop_task, timeout=10)
            final_settings = _load_task_settings_fresh(task_path)
            assert final_settings.session.state == "stopped"
            assert final_settings.session.last_run_status == "success"

    async def test_last_run_records_start_not_end(self, tmp_dir: Path) -> None:
        stamps = ["2026-03-01 10:00:00", "2026-03-01 10:00:01", "2026-03-01 10:00:02"]
        with (
            patch(
                "termux_tasker.runner_process.asyncio.create_subprocess_exec",
                return_value=_mock_proc(),
            ),
            patch(
                "termux_tasker.runner_process._now_timestamp", side_effect=stamps
            ),
        ):
            runner_path = _write_full_runner(tmp_dir)
            task_path = _write_task(runner_path)
            proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
            proc.shutting_down = False
            loop_task = asyncio.create_task(proc._run_loop())
            deadline = asyncio.get_event_loop().time() + 5.0
            while True:
                runner_settings = _load_runner_settings_fresh(runner_path)
                if runner_settings.session.state == "idle":
                    break
                if asyncio.get_event_loop().time() > deadline:
                    raise AssertionError("runner never reached idle state")
                await asyncio.sleep(0.05)
            proc.shutting_down = True
            await asyncio.wait_for(loop_task, timeout=10)
            runner_settings = _load_runner_settings_fresh(runner_path)
            task_settings = _load_task_settings_fresh(task_path)
            assert runner_settings.session.last_run == stamps[0]
            assert task_settings.session.last_run == stamps[1]


@pytest.mark.asyncio
class TestWholeBlockTaskStatus:
    async def _run_failing_phase(
        self, tmp_dir: Path, phase_cmd: str
    ) -> tuple[RunnerSettings, TaskSettings]:
        async def _fail_phase(*args: object, **kwargs: object) -> AsyncMock:
            cmd = str(args[2]) if len(args) > 2 else ""
            if phase_cmd in cmd:
                return _mock_proc(return_code=1)
            return _mock_proc()

        with patch(
            "termux_tasker.runner_process.asyncio.create_subprocess_exec",
            side_effect=_fail_phase,
        ):
            runner_path = _write_full_runner(tmp_dir)
            task_path = _write_task(runner_path)
            proc = RunnerProcess(runner_path, "test-session", tmp_dir / ".tmp")
            proc.shutting_down = False
            await asyncio.wait_for(proc._run_loop(), timeout=10)
            return (
                _load_runner_settings_fresh(runner_path),
                _load_task_settings_fresh(task_path),
            )

    async def test_before_task_failure_marks_task_failed(self, tmp_dir: Path) -> None:
        _, task_settings = await self._run_failing_phase(tmp_dir, "before-task")
        assert task_settings.session.last_run != "none"
        assert task_settings.session.last_run_status == "fail"
        assert task_settings.session.state == "stopped"

    async def test_after_task_failure_marks_task_failed(self, tmp_dir: Path) -> None:
        _, task_settings = await self._run_failing_phase(tmp_dir, "after-task")
        assert task_settings.session.last_run != "none"
        assert task_settings.session.last_run_status == "fail"
        assert task_settings.session.state == "stopped"

    async def test_failed_cycle_still_stamps_runner_start(self, tmp_dir: Path) -> None:
        runner_settings, _ = await self._run_failing_phase(tmp_dir, "before-exec")
        assert runner_settings.session.session_id == "test-session"
        assert runner_settings.session.last_run != "none"


class TestSkipUsesUtc:
    def test_recent_run_is_skipped(self, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        task_path = _write_task(runner_path)
        proc = _create_proc(runner_path, tmp_dir)
        task_settings = _load_task_settings_fresh(task_path)
        task_settings.session.session_id = "test-session"
        task_settings.session.last_run = (
            datetime.now(timezone.utc) - timedelta(seconds=30)
        ).strftime("%Y-%m-%d %H:%M:%S")
        assert proc._should_skip_task(task_settings) is True
        task_settings.session.last_run = (
            datetime.now(timezone.utc) - timedelta(seconds=90)
        ).strftime("%Y-%m-%d %H:%M:%S")
        assert proc._should_skip_task(task_settings) is False

    @pytest.mark.skipif(not hasattr(time, "tzset"), reason="POSIX-only TZ override")
    def test_skip_is_timezone_independent(self, tmp_dir: Path) -> None:
        runner_path = _write_runner(tmp_dir)
        task_path = _write_task(runner_path)
        proc = _create_proc(runner_path, tmp_dir)
        task_settings = _load_task_settings_fresh(task_path)
        task_settings.session.session_id = "test-session"
        task_settings.session.last_run = (
            datetime.now(timezone.utc) - timedelta(seconds=30)
        ).strftime("%Y-%m-%d %H:%M:%S")
        previous_tz = os.environ.get("TZ")
        os.environ["TZ"] = "Pacific/Kiritimati"
        time.tzset()
        try:
            assert proc._should_skip_task(task_settings) is True
        finally:
            if previous_tz is None:
                del os.environ["TZ"]
            else:
                os.environ["TZ"] = previous_tz
            time.tzset()
