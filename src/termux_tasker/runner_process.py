from __future__ import annotations

import asyncio
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

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


def _parse_timeout(timeout_str: str) -> int:
    if timeout_str.endswith("h"):
        return int(timeout_str[:-1]) * 3600
    elif timeout_str.endswith("m"):
        return int(timeout_str[:-1]) * 60
    elif timeout_str.endswith("s"):
        return int(timeout_str[:-1])
    return 60


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _to_env_key(name: str) -> str:
    return "VAR_" + "".join(c if c.isalnum() else "_" for c in name).upper()


class RunnerProcess:
    def __init__(self, runner_dir: Path, session_id: str, tmp_dir: Path) -> None:
        self.runner_dir = runner_dir
        self.session_id = session_id
        self.tmp_dir = tmp_dir
        self.shutting_down = False
        self._task: Optional[asyncio.Task] = None
        self._processes: list[subprocess.Popen] = []
        self._run_lock = False

        self._stdout_path = runner_dir / "stdout"
        self._metadata_path = runner_dir / "metadata.toml"
        self._settings_path = runner_dir / "settings.toml"
        self._tasks_dir = runner_dir / "tasks"

        self.metadata: RunnerMetadata = RunnerMetadata.load(self._metadata_path)
        self.settings: RunnerSettings = RunnerSettings.load(self._settings_path)

    def _log(self, msg: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {msg}\n"
        self._stdout_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._stdout_path, "a") as f:
            f.write(line)

    def _change_runner_state(self, state: str) -> None:
        self._log(f"Runner state: {state}")
        self.settings.session.state = state
        self.settings.save(self._settings_path)

    def _change_task_state(self, task_dir: Path, state: str) -> None:
        self._log(f"Task state: {state}")
        task_settings = TaskSettings.load(task_dir / "settings.toml")
        task_settings.session.state = state
        task_settings.save(task_dir / "settings.toml")

    async def _run_cmd(
            self, cmd: str, error_context: str, task_dir: Path | None = None,
            extra_env: dict[str, str] | None = None,
    ) -> None:
        if task_dir is not None:
            cmd = cmd.replace("{task_dir}", str(task_dir))
        self._log(f"Run: {cmd}")
        env = os.environ.copy()
        for key, val in self.settings.properties.items():
            env[_to_env_key(key)] = val
        if extra_env:
            env.update(extra_env)
        proc = await asyncio.create_subprocess_exec(
            "sh", "-c", cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=self.runner_dir,
            env=env,
        )
        self._processes.append(proc)
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
            self._stdout_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._stdout_path, "a") as f:
                f.write(f"{timestamp} {line.decode(errors='replace').rstrip()}\n")
        returncode = await proc.wait()
        self._processes.remove(proc)
        if returncode != 0:
            raise RunnerException(f"Error during command execution {error_context}")

    async def _run_task_cmd(self, cmd: str, task_dir: Path) -> None:
        cmd_with_placeholder = cmd.replace("{task_dir}", str(task_dir))
        task_settings = TaskSettings.load(task_dir / "settings.toml")
        task_env = {_to_env_key(k): v for k, v in task_settings.properties.items()}
        try:
            await self._run_cmd(
                cmd, error_context=cmd_with_placeholder, task_dir=task_dir,
                extra_env=task_env,
            )
        except Exception as e:
            raise TaskException(str(e)) from e

    def _should_skip_task(self, task_settings: TaskSettings) -> bool:
        if not task_settings.general.enabled:
            return True

        if task_settings.session.session_id == self.session_id:
            if task_settings.session.last_run != "none":
                try:
                    last_run_dt = datetime.strptime(
                        task_settings.session.last_run, "%Y-%m-%d %H:%M:%S"
                    )
                    now = datetime.now()
                    elapsed = (now - last_run_dt).total_seconds()
                    timeout_sec = _parse_timeout(task_settings.general.timeout)
                    if elapsed < timeout_sec:
                        return True
                except ValueError:
                    pass
        return False

    async def _run_loop(self) -> None:
        try:
            self._run_lock = True

            self._change_runner_state("initialization")

            if self.metadata.exec.initialization:
                await self._run_cmd(
                    self.metadata.exec.initialization, self.metadata.exec.initialization
                )

            while not self.shutting_down:
                self._change_runner_state("before-exec")
                if self.metadata.exec.before_exec:
                    await self._run_cmd(
                        self.metadata.exec.before_exec, self.metadata.exec.before_exec
                    )

                for task_dir in sorted(self._tasks_dir.iterdir()):
                    if not task_dir.is_dir():
                        continue
                    task_settings_path = task_dir / "settings.toml"
                    if not task_settings_path.exists():
                        continue

                    task_settings = TaskSettings.load(task_settings_path)

                    if self._should_skip_task(task_settings):
                        continue

                    task_meta = TaskMetadata.load(task_dir / "metadata.toml")
                    self._log(f"Run task: {task_meta.general.id}")

                    self._change_runner_state("before-task")
                    if self.metadata.exec.before_task:
                        await self._run_cmd(
                            self.metadata.exec.before_task,
                            self.metadata.exec.before_task,
                            task_dir=task_dir,
                        )

                    try:
                        self._change_runner_state("task-exec")
                        self._change_task_state(task_dir, "running")
                        if self.metadata.exec.task_exec:
                            await self._run_task_cmd(
                                self.metadata.exec.task_exec, task_dir
                            )
                        task_settings.session.last_run_status = "success"
                    except TaskException:
                        task_settings.session.last_run_status = "fail"
                    finally:
                        task_settings.session.session_id = self.session_id
                        task_settings.session.last_run = _now_timestamp()
                        task_settings.save(task_settings_path)
                        self._change_task_state(task_dir, "stopped")

                    self._change_runner_state("after-task")
                    if self.metadata.exec.after_task:
                        await self._run_cmd(
                            self.metadata.exec.after_task,
                            self.metadata.exec.after_task,
                            task_dir=task_dir,
                        )

                self._change_runner_state("after-exec")
                if self.metadata.exec.after_exec:
                    await self._run_cmd(
                        self.metadata.exec.after_exec,
                        self.metadata.exec.after_exec,
                    )

                if self.shutting_down:
                    break

                self._change_runner_state("idle")
                timeout_sec = _parse_timeout(self.settings.general.timeout)
                self._log(f"Sleep for {self.settings.general.timeout}")
                for _ in range(timeout_sec):
                    if self.shutting_down:
                        break
                    await asyncio.sleep(1)

            self._change_runner_state("termination")
            if self.metadata.exec.termination:
                await self._run_cmd(
                    self.metadata.exec.termination,
                    self.metadata.exec.termination,
                )

        except RunnerException as e:
            self._log(str(e))
        except Exception as e:
            self._log(f"Unexpected error: {e}")
        finally:
            self._change_runner_state("off")
            self._run_lock = False

    def run(self) -> None:
        if self._run_lock:
            return
        self._task = asyncio.create_task(self._run_loop())
        self._task.add_done_callback(self._on_run_done)

    def _on_run_done(self, task: asyncio.Task) -> None:
        try:
            exc = task.exception()
            if exc:
                self._log(f"Run loop failed: {exc}")
        except asyncio.CancelledError:
            pass

    async def shutdown(self) -> None:
        self.shutting_down = True
        while self.settings.session.state != "off":
            await asyncio.sleep(0.5)

    def terminate(self) -> None:
        for proc in self._processes:
            try:
                proc.terminate()
            except Exception:
                pass
        self._processes.clear()
