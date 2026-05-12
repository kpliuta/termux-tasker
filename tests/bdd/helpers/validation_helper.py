from __future__ import annotations

from pathlib import Path

import pytest

from termux_tasker.runner_validator import RunnerValidator, RunnerValidatorException
from termux_tasker.task_validator import TaskValidator, TaskValidatorException


class ValidationHelper:
    """Encapsulates runner and task validation logic used in BDD steps."""

    _STORE: dict = {}

    @staticmethod
    def store(key: str, value: object) -> None:
        ValidationHelper._STORE[key] = value

    @staticmethod
    def retrieve(key: str) -> object:
        return ValidationHelper._STORE.get(key)

    # ── Runner validation ───────────────────────────────────────────────

    @staticmethod
    def create_runner_validator(
        runner_dir: Path, app_version: str = "0.1.0",
    ) -> RunnerValidator:
        return RunnerValidator(runner_dir, app_version=app_version)

    @staticmethod
    def validate_runner(
        runner_dir: Path, app_version: str = "0.1.0",
    ) -> None:
        validator = ValidationHelper.create_runner_validator(runner_dir, app_version)
        validator.validate()

    @staticmethod
    def validate_runner_expect_fail(
        runner_dir: Path, app_version: str = "0.1.0",
        match: str | None = None,
    ) -> None:
        validator = ValidationHelper.create_runner_validator(runner_dir, app_version)
        with pytest.raises(RunnerValidatorException, match=match):
            validator.validate()

    # ── Task validation ─────────────────────────────────────────────────

    @staticmethod
    def create_task_validator(
        runner_dir: Path, task_dir: Path, tmp_dir: Path,
    ) -> TaskValidator:
        return TaskValidator(runner_dir, task_dir, tmp_dir)

    @staticmethod
    def validate_task(
        runner_dir: Path, task_dir: Path, tmp_dir: Path,
    ) -> TaskValidator:
        validator = ValidationHelper.create_task_validator(
            runner_dir, task_dir, tmp_dir,
        )
        validator.validate()
        return validator

    @staticmethod
    def validate_task_expect_fail(
        runner_dir: Path, task_dir: Path, tmp_dir: Path,
        match: str | None = None,
    ) -> TaskValidator:
        validator = ValidationHelper.create_task_validator(
            runner_dir, task_dir, tmp_dir,
        )
        with pytest.raises(TaskValidatorException, match=match):
            validator.validate()
        return validator
