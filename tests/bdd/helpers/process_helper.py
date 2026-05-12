from __future__ import annotations

from pathlib import Path

from termux_tasker.runner_process import RunnerProcess


class ProcessHelper:
    """Encapsulates RunnerProcess creation and manipulation for BDD steps."""

    @staticmethod
    def create_process(
        runner_dir: Path, session_id: str = "test-session", tmp_dir: Path | None = None,
    ) -> RunnerProcess:
        if tmp_dir is None:
            tmp_dir = runner_dir.parent.parent / ".tmp"
        return RunnerProcess(runner_dir, session_id, tmp_dir)

    @staticmethod
    def create_and_start(
        runner_dir: Path, session_id: str = "test-session",
        tmp_dir: Path | None = None,
    ) -> RunnerProcess:
        proc = ProcessHelper.create_process(runner_dir, session_id, tmp_dir)
        proc._run_lock = True
        proc.run()
        return proc
