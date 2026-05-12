from __future__ import annotations

from pathlib import Path

import pytest

from termux_tasker.task_validator import TaskValidator, TaskValidatorException


RUNNER_METADATA = """\
[general]
id = "test-runner"
name = "Test Runner"
version = "0.1.0"
url = "https://github.com/user/test-runner"
app_min_version = ">=0.1.0"

[exec]
task-exec = "echo {task_dir}"
"""

VALID_TASK_METADATA = """\
[general]
id = "test-task"
name = "Test Task"
description = "A test task"
version = "0.1.0"
url = "https://github.com/user/test-task"
runner_id = "test-runner"
runner_min_version = ">=0.1.0"
default_timeout = "1h"
"""

VALID_TASK_METADATA_LOCAL = """\
[general]
id = "test-task-local"
name = "Test Task Local"
version = "1.0"
runner_id = "test-runner"
runner_min_version = ">=0.0.1"
default_timeout = "30m"
"""


class TestTaskValidatorMetadataExisted:
    def test_metadata_exists(self, tmp_dir: Path) -> None:
        runner_dir = tmp_dir / "runner"
        runner_dir.mkdir()
        (runner_dir / "metadata.toml").write_text(RUNNER_METADATA)

        task_dir = tmp_dir / "task"
        task_dir.mkdir()
        (task_dir / "metadata.toml").write_text(VALID_TASK_METADATA)

        validator = TaskValidator(runner_dir, task_dir, tmp_dir / ".tmp")
        validator.validate_metadata_existed()

    def test_metadata_not_exists(self, tmp_dir: Path) -> None:
        runner_dir = tmp_dir / "runner"
        runner_dir.mkdir()
        (runner_dir / "metadata.toml").write_text(RUNNER_METADATA)

        task_dir = tmp_dir / "task"
        task_dir.mkdir()

        validator = TaskValidator(runner_dir, task_dir, tmp_dir / ".tmp")
        with pytest.raises(TaskValidatorException, match="metadata.toml not found"):
            validator.validate_metadata_existed()


class TestTaskValidatorMetadataStructure:
    def test_valid_metadata_local(self, tmp_dir: Path) -> None:
        runner_dir = tmp_dir / "runner"
        runner_dir.mkdir()
        (runner_dir / "metadata.toml").write_text(RUNNER_METADATA)

        task_dir = tmp_dir / "task"
        task_dir.mkdir()
        (task_dir / "metadata.toml").write_text(VALID_TASK_METADATA_LOCAL)

        validator = TaskValidator(runner_dir, task_dir, tmp_dir / ".tmp")
        validator.validate_metadata_structure()

    def test_missing_id(self, tmp_dir: Path) -> None:
        runner_dir = tmp_dir / "runner"
        runner_dir.mkdir()
        (runner_dir / "metadata.toml").write_text(RUNNER_METADATA)

        task_dir = tmp_dir / "task"
        task_dir.mkdir()
        content = VALID_TASK_METADATA.replace('id = "test-task"', '')
        (task_dir / "metadata.toml").write_text(content)

        validator = TaskValidator(runner_dir, task_dir, tmp_dir / ".tmp")
        with pytest.raises(TaskValidatorException, match="id is required"):
            validator.validate_metadata_structure()

    def test_missing_runner_id(self, tmp_dir: Path) -> None:
        runner_dir = tmp_dir / "runner"
        runner_dir.mkdir()
        (runner_dir / "metadata.toml").write_text(RUNNER_METADATA)

        task_dir = tmp_dir / "task"
        task_dir.mkdir()
        content = VALID_TASK_METADATA.replace('runner_id = "test-runner"', '')
        (task_dir / "metadata.toml").write_text(content)

        validator = TaskValidator(runner_dir, task_dir, tmp_dir / ".tmp")
        with pytest.raises(TaskValidatorException, match="runner_id is required"):
            validator.validate_metadata_structure()

    def test_missing_default_timeout(self, tmp_dir: Path) -> None:
        runner_dir = tmp_dir / "runner"
        runner_dir.mkdir()
        (runner_dir / "metadata.toml").write_text(RUNNER_METADATA)

        task_dir = tmp_dir / "task"
        task_dir.mkdir()
        content = VALID_TASK_METADATA.replace('default_timeout = "1h"', '')
        (task_dir / "metadata.toml").write_text(content)

        validator = TaskValidator(runner_dir, task_dir, tmp_dir / ".tmp")
        with pytest.raises(TaskValidatorException, match="default_timeout is required"):
            validator.validate_metadata_structure()

    def test_invalid_timeout_format(self, tmp_dir: Path) -> None:
        runner_dir = tmp_dir / "runner"
        runner_dir.mkdir()
        (runner_dir / "metadata.toml").write_text(RUNNER_METADATA)

        task_dir = tmp_dir / "task"
        task_dir.mkdir()
        content = VALID_TASK_METADATA.replace('default_timeout = "1h"', 'default_timeout = "1x"')
        (task_dir / "metadata.toml").write_text(content)

        validator = TaskValidator(runner_dir, task_dir, tmp_dir / ".tmp")
        with pytest.raises(TaskValidatorException, match="must be in format"):
            validator.validate_metadata_structure()


class TestTaskValidatorRunnerCompatibility:
    def test_compatible(self, tmp_dir: Path) -> None:
        runner_dir = tmp_dir / "runner"
        runner_dir.mkdir()
        (runner_dir / "metadata.toml").write_text(RUNNER_METADATA)

        task_dir = tmp_dir / "task"
        task_dir.mkdir()
        (task_dir / "metadata.toml").write_text(VALID_TASK_METADATA)

        validator = TaskValidator(runner_dir, task_dir, tmp_dir / ".tmp")
        validator.validate_metadata_structure()
        validator.check_runner_compatibility()

    def test_runner_id_mismatch(self, tmp_dir: Path) -> None:
        runner_dir = tmp_dir / "runner"
        runner_dir.mkdir()
        (runner_dir / "metadata.toml").write_text(RUNNER_METADATA)

        task_dir = tmp_dir / "task"
        task_dir.mkdir()
        content = VALID_TASK_METADATA.replace('runner_id = "test-runner"', 'runner_id = "other-runner"')
        (task_dir / "metadata.toml").write_text(content)

        validator = TaskValidator(runner_dir, task_dir, tmp_dir / ".tmp")
        validator.validate_metadata_structure()
        with pytest.raises(TaskValidatorException, match="does not match"):
            validator.check_runner_compatibility()

    def test_runner_version_incompatible(self, tmp_dir: Path) -> None:
        runner_dir = tmp_dir / "runner"
        runner_dir.mkdir()
        (runner_dir / "metadata.toml").write_text(RUNNER_METADATA)

        task_dir = tmp_dir / "task"
        task_dir.mkdir()
        content = VALID_TASK_METADATA.replace('runner_min_version = ">=0.1.0"', 'runner_min_version = ">=2.0.0"')
        (task_dir / "metadata.toml").write_text(content)

        validator = TaskValidator(runner_dir, task_dir, tmp_dir / ".tmp")
        validator.validate_metadata_structure()
        with pytest.raises(TaskValidatorException, match="does not satisfy"):
            validator.check_runner_compatibility()
