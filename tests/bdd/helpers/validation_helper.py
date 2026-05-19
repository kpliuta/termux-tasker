from __future__ import annotations

from pathlib import Path

import pytest

from termux_tasker.runner_validator import RunnerValidator, RunnerValidatorException
from termux_tasker.task_validator import TaskValidator, TaskValidatorException

_STORE: dict = {}


def store(key: str, value: object) -> None:
    _STORE[key] = value


def retrieve(key: str) -> object:
    return _STORE.get(key)


def create_runner_validator(
    runner_dir: Path, app_version: str = "0.1.0",
) -> RunnerValidator:
    return RunnerValidator(runner_dir, app_version=app_version)


def validate_runner(
    runner_dir: Path, app_version: str = "0.1.0",
) -> None:
    validator = create_runner_validator(runner_dir, app_version)
    validator.validate()


def validate_runner_expect_fail(
    runner_dir: Path, app_version: str = "0.1.0",
    match: str | None = None,
) -> None:
    validator = create_runner_validator(runner_dir, app_version)
    with pytest.raises(RunnerValidatorException, match=match):
        validator.validate()


def create_task_validator(
    runner_dir: Path, task_dir: Path, tmp_dir: Path,
) -> TaskValidator:
    return TaskValidator(runner_dir, task_dir, tmp_dir)


def validate_task(
    runner_dir: Path, task_dir: Path, tmp_dir: Path,
) -> TaskValidator:
    validator = create_task_validator(runner_dir, task_dir, tmp_dir)
    validator.validate()
    return validator


def validate_task_expect_fail(
    runner_dir: Path, task_dir: Path, tmp_dir: Path,
    match: str | None = None,
) -> TaskValidator:
    validator = create_task_validator(runner_dir, task_dir, tmp_dir)
    with pytest.raises(TaskValidatorException, match=match):
        validator.validate()
    return validator
