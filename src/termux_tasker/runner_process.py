from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from termux_tasker._parse import parse_timeout
from termux_tasker.config import (
    RunnerMetadata,
    RunnerSettings,
    TaskMetadata,
    TaskSettings,
)


class RunnerException(Exception):
    pass


class TaskException(Exception):
    pass


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _to_env_key(name: str) -> str:
    return "VAR_" + "".join(c if c.isalnum() else "_" for c in name).upper()


class RunnerProcess:
    """Manages a single runner's asyncio execution lifecycle.

    The runner follows the state machine:
        initialization -> (before-exec -> [per-task: before-task -> task-exec -> after-task] -> after-exec -> idle)* -> termination -> off

    The lifecycle repeats until shutdown() is called.  During idle, the
    shutting_down flag is checked every second for responsive shutdown.
    """

    def __init__(self, runner_path: Path, session_id: str, tmp_dir: Path) -> None:
        self.runner_path = runner_path
        self.session_id = session_id
        self.tmp_dir = tmp_dir
        self.shutting_down = False
        self._task: Optional[asyncio.Task[None]] = None
        self._processes: list[asyncio.subprocess.Process] = []
        self._run_lock = False
        self.state_started_monotonic: float = time.monotonic()
        self.current_task_path: Path | None = None
        self.exec_total: int = 0
        self.exec_index: int = 0

        self._stdout_path = runner_path / "stdout"
        self._metadata_path = runner_path / "metadata.toml"
        self._settings_path = runner_path / "settings.toml"
        self._tasks_path = runner_path / "tasks"

        self.metadata: RunnerMetadata = RunnerMetadata.load(self._metadata_path)
        self.settings: RunnerSettings = RunnerSettings.load(self._settings_path)

    @property
    def live_pids(self) -> list[int]:
        """PIDs of currently executing child processes (empty when idle)."""
        return [proc.pid for proc in self._processes if proc.pid is not None]

    def _log(self, msg: str) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {msg}\n"
        self._stdout_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._stdout_path, "a") as f:
            f.write(line)

    def _change_runner_state(self, state: str) -> None:
        self._log(f"Runner state: {state}")
        self.settings.session.state = state
        self.state_started_monotonic = time.monotonic()
        self.settings.save(self._settings_path)

    def _change_task_state(self, task_path: Path, state: str) -> None:
        self._log(f"Task state: {state}")
        task_settings = TaskSettings.load(task_path / "settings.toml")
        task_settings.session.state = state
        task_settings.save(task_path / "settings.toml")

    async def _run_cmd(
            self, cmd: str, error_context: str, task_path: Path | None = None,
            extra_env: dict[str, str] | None = None,
    ) -> None:
        """Execute a shell command and stream its output to the runner's stdout log.

        - Commands are run via ``sh -c``.
        - ``{runner_path}`` is available in all lifecycle steps.
        - ``{task_path}`` and ``{task_dir_name}`` are available in
          task-level steps only (before-task, task-exec, after-task).
        - Environment includes OS env + runner properties as ``VAR_<NAME>`` +
          any extra_env (used for task-specific vars).
        - Subprocess is tracked in self._processes for later termination.
        - Stdout is streamed line-by-line with timestamps to the runner's
          stdout file.
        """
        cmd = cmd.replace("{runner_path}", str(self.runner_path))
        if task_path is not None:
            cmd = cmd.replace("{task_path}", str(task_path))
            cmd = cmd.replace("{task_dir_name}", task_path.name)
        self._log(f"Run: {cmd}")
        env = os.environ.copy()
        for key, val in self.settings.properties.items():
            env[_to_env_key(key)] = val
        if task_path is not None:
            env["OUTPUT_DIR"] = str(task_path / "output")
        if extra_env:
            env.update(extra_env)
        proc = await asyncio.create_subprocess_exec(
            "sh", "-c", cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=self.runner_path,
            env=env,
        )
        self._processes.append(proc)

        assert proc.stdout is not None
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            text = line.decode(errors="replace").strip()
            if text:
                timestamp = datetime.now(timezone.utc).strftime("[%Y-%m-%d %H:%M:%S]")
                self._stdout_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self._stdout_path, "a") as f:
                    f.write(f"{timestamp} {text}\n")

        return_code = await proc.wait()
        self._processes.remove(proc)
        if return_code != 0:
            raise RunnerException(f"Error during command execution {error_context}")

    async def _run_task_cmd(self, cmd: str, task_path: Path) -> None:
        """Run a task-level command, injecting task properties as env vars.

        Wraps _run_cmd with task-specific environment and converts errors
        to TaskException (caught by _run_loop as non-fatal).
        """
        cmd_with_placeholder = cmd.replace("{task_path}", str(task_path)).replace("{task_dir_name}", task_path.name)
        task_settings = TaskSettings.load(task_path / "settings.toml")
        task_env = {_to_env_key(k): v for k, v in task_settings.properties.items()}
        try:
            await self._run_cmd(
                cmd, error_context=cmd_with_placeholder, task_path=task_path,
                extra_env=task_env,
            )
        except Exception as e:
            raise TaskException(str(e)) from e

    def _should_skip_task(self, task_settings: TaskSettings) -> bool:
        """Determine if a task should be skipped during this run cycle.

        A task is skipped if:
        1. It is not enabled, OR
        2. Its session_id matches the current session AND its last_run
           elapsed time is less than its configured timeout (rate-limiting).

        Tasks from a different session are always re-run (no cross-session
        rate limiting).
        """
        if not task_settings.general.enabled:
            return True

        if task_settings.session.session_id == self.session_id:
            if task_settings.session.last_run != "none":
                try:
                    last_run_dt = datetime.strptime(
                        task_settings.session.last_run, "%Y-%m-%d %H:%M:%S"
                    ).replace(tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)
                    elapsed = (now - last_run_dt).total_seconds()
                    timeout_sec = parse_timeout(task_settings.general.timeout)
                    if elapsed < timeout_sec:
                        return True
                except ValueError:
                    pass
        return False

    async def _run_loop(self) -> None:
        """Main execution loop — the runner's lifecycle state machine.

        Phases (each is optional — only runs if defined in metadata.exec):
          initialization
          └─ loop until shutting_down ──────────────────────┐
               ├─ before-exec                               │
               ├─ for each enabled (non-rate-limited) task: │
               │    ├─ before-task                          │
               │    ├─ task-exec  ← runs the actual command │
               │    └─ after-task                           │
               ├─ after-exec                                │
               └─ idle (sleep, check shutting_down each s)──┘
          termination
          off

        Errors in task-exec are non-fatal (task marked "fail").
        The loop always sets state to "off" and releases _run_lock.
        """
        try:
            self._run_lock = True

            self._change_runner_state("initialization")

            if self.metadata.exec.initialization:
                init_start = time.monotonic()
                try:
                    await self._run_cmd(
                        self.metadata.exec.initialization, self.metadata.exec.initialization
                    )
                finally:
                    self.settings.session.last_run_init_duration = int(
                        time.monotonic() - init_start
                    )
                    # Persist immediately: initialization runs once at startup,
                    # so later per-cycle saves just carry this value forward.
                    # The duration survives even if this step fails and aborts the loop.
                    self.settings.save(self._settings_path)
            else:
                self.settings.session.last_run_init_duration = 0
                self.settings.save(self._settings_path)

            while not self.shutting_down:
                # Start of cycle: adopt the session and stamp the start time.
                # _change_runner_state persists both in the same save.
                self.settings.session.session_id = self.session_id
                self.settings.session.last_run = _now_timestamp()
                self._change_runner_state("before-exec")
                if self.metadata.exec.before_exec:
                    runner_before_start = time.monotonic()
                    try:
                        await self._run_cmd(
                            self.metadata.exec.before_exec, self.metadata.exec.before_exec
                        )
                    finally:
                        self.settings.session.last_run_before_duration = int(
                            time.monotonic() - runner_before_start
                        )
                        # Persist partial progress so the duration survives
                        # even if this step fails and aborts the loop.
                        self.settings.save(self._settings_path)
                else:
                    self.settings.session.last_run_before_duration = 0

                # Wall time of the whole per-task iteration block (all tasks,
                # including their before-task / task-exec / after-task steps).
                runner_exec_start = time.monotonic()
                self.exec_total = self._count_runnable_tasks()
                self.exec_index = 0
                self.current_task_path = None
                # Tasks are processed in sorted directory order (by task id)
                for task_path in sorted(self._tasks_path.iterdir()):
                    if not task_path.is_dir():
                        continue
                    task_settings_path = task_path / "settings.toml"
                    if not task_settings_path.exists():
                        continue

                    task_settings = TaskSettings.load(task_settings_path)

                    if self._should_skip_task(task_settings):
                        continue

                    task_meta = TaskMetadata.load(task_path / "metadata.toml")
                    self._log(f"Run task: {task_meta.general.id}")

                    output_dir = task_path / "output"
                    output_dir.mkdir(parents=True, exist_ok=True)

                    self.exec_index += 1
                    self.current_task_path = task_path
                    # Start of task block: adopt the session, stamp the start
                    # time and mark running in a single save, so screens polling
                    # mid-run never see a torn state. The task stays "running"
                    # for the whole block (before-task through after-task).
                    task_settings.session.session_id = self.session_id
                    task_settings.session.last_run = _now_timestamp()
                    self._change_task_state(task_path, "running")
                    task_run_ok = True
                    try:
                        self._change_runner_state("before-task")
                        if self.metadata.exec.before_task:
                            before_start = time.monotonic()
                            try:
                                await self._run_cmd(
                                    self.metadata.exec.before_task,
                                    self.metadata.exec.before_task,
                                    task_path=task_path,
                                )
                            finally:
                                task_settings.session.last_run_before_duration = int(
                                    time.monotonic() - before_start
                                )
                                # Persist partial progress so the duration survives
                                # even if this step fails and aborts the loop.
                                task_settings.save(task_settings_path)
                        else:
                            task_settings.session.last_run_before_duration = 0

                        try:
                            self._change_runner_state("task-exec")
                            if self.metadata.exec.task_exec:
                                exec_start = time.monotonic()
                                try:
                                    await self._run_task_cmd(
                                        self.metadata.exec.task_exec, task_path
                                    )
                                finally:
                                    task_settings.session.last_run_exec_duration = int(
                                        time.monotonic() - exec_start
                                    )
                            else:
                                task_settings.session.last_run_exec_duration = 0
                        except TaskException:
                            # Task failure does not crash the whole runner
                            task_run_ok = False

                        self._change_runner_state("after-task")
                        if self.metadata.exec.after_task:
                            after_start = time.monotonic()
                            try:
                                await self._run_cmd(
                                    self.metadata.exec.after_task,
                                    self.metadata.exec.after_task,
                                    task_path=task_path,
                                )
                            finally:
                                task_settings.session.last_run_after_duration = int(
                                    time.monotonic() - after_start
                                )
                                task_settings.save(task_settings_path)
                        else:
                            task_settings.session.last_run_after_duration = 0
                            task_settings.save(task_settings_path)
                    except (RunnerException, asyncio.CancelledError):
                        task_run_ok = False
                        raise
                    finally:
                        task_settings.session.last_run_status = (
                            "success" if task_run_ok else "fail"
                        )
                        self._change_task_state(task_path, "stopped")

                    self.current_task_path = None

                # The exec duration covers only the per-task iteration block,
                # measured before after-exec runs.
                self.settings.session.last_run_exec_duration = int(
                    time.monotonic() - runner_exec_start
                )

                self._change_runner_state("after-exec")
                if self.metadata.exec.after_exec:
                    runner_after_start = time.monotonic()
                    try:
                        await self._run_cmd(
                            self.metadata.exec.after_exec,
                            self.metadata.exec.after_exec,
                        )
                    finally:
                        self.settings.session.last_run_after_duration = int(
                            time.monotonic() - runner_after_start
                        )
                        # Persist partial progress so the duration survives
                        # even if this step fails and aborts the loop.
                        self.settings.save(self._settings_path)
                else:
                    self.settings.session.last_run_after_duration = 0

                # Persist the exec/zero durations recorded above (session and
                # last_run were already stamped at the top of the cycle).
                self.settings.save(self._settings_path)

                if self.shutting_down:
                    break

                # Idle phase: sleep in 1s increments so shutdown()
                # does not have to wait for the full timeout to elapse
                self._change_runner_state("idle")
                timeout_sec = parse_timeout(self.settings.general.timeout)
                self._log(f"Sleep for {self.settings.general.timeout}")
                for _ in range(timeout_sec):
                    if self.shutting_down:
                        break
                    await asyncio.sleep(1)

            self._change_runner_state("termination")
            if self.metadata.exec.termination:
                termination_start = time.monotonic()
                try:
                    await self._run_cmd(
                        self.metadata.exec.termination,
                        self.metadata.exec.termination,
                    )
                finally:
                    self.settings.session.last_run_termination_duration = int(
                        time.monotonic() - termination_start
                    )
                    self.settings.save(self._settings_path)
            else:
                self.settings.session.last_run_termination_duration = 0
                self.settings.save(self._settings_path)

        except RunnerException as e:
            self._log(str(e))
        except Exception as e:
            self._log(f"Unexpected error: {e}")
        finally:
            self.current_task_path = None
            self._change_runner_state("off")
            self._run_lock = False

    def _count_runnable_tasks(self) -> int:
        """Count enabled, non-rate-limited tasks for the exec progress suffix."""
        if not self._tasks_path.exists():
            return 0
        total = 0
        for task_path in sorted(self._tasks_path.iterdir()):
            if not task_path.is_dir():
                continue
            if not (task_path / "settings.toml").exists():
                continue
            task_settings = TaskSettings.load(task_path / "settings.toml")
            if self._should_skip_task(task_settings):
                continue
            total += 1
        return total

    def state_elapsed(self, now: float | None = None) -> int:
        """Seconds spent in the current runner state (live elapsed timer)."""
        current = time.monotonic() if now is None else now
        return max(0, int(current - self.state_started_monotonic))

    def run(self) -> bool:
        """Start the runner lifecycle as a background asyncio task.

        Guarded by _run_lock — subsequent calls while the runner is
        already starting/started are silently ignored.
        """
        if self._run_lock:
            return False
        task = asyncio.create_task(self._run_loop())
        task.add_done_callback(self._on_run_done)
        self._task = task
        return True

    def _on_run_done(self, task: asyncio.Task[None]) -> None:
        try:
            exc = task.exception()
            if exc:
                self._log(f"Run loop failed: {exc}")
        except asyncio.CancelledError:
            pass

    async def shutdown(self) -> None:
        """Request graceful shutdown and wait until the runner reaches "off".

        Sets the shutting_down flag.  The _run_loop checks this flag
        during the idle sleep loop and between state transitions.
        This call blocks until the runner has fully stopped.
        """
        self.shutting_down = True
        while self.settings.session.state != "off":
            await asyncio.sleep(0.5)

    def terminate(self) -> None:
        """Hard-kill all tracked subprocesses (SIGTERM).

        Does NOT set shutting_down — used as a last-resort cleanup
        rather than a graceful stop.
        """
        for proc in self._processes:
            try:
                proc.terminate()
            except Exception:   # noqa
                pass
        self._processes.clear()
