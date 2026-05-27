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
task-exec = "echo {task_path}"
"""

RUNNER_WITH_VALIDATOR = """\
[general]
id = "test-runner"
name = "Test Runner"
version = "0.1.0"
url = "https://github.com/user/test-runner"
app_min_version = ">=0.1.0"

[exec]
task-exec = "echo {task_path}"

[[task-validator]]
command = "test -f {task_path}/required_file"
"""

RUNNER_WITH_TASK_DIR_NAME_VALIDATOR = """\
[general]
id = "test-runner"
name = "Test Runner"
version = "0.1.0"
url = "https://github.com/user/test-runner"
app_min_version = ">=0.1.0"

[exec]
task-exec = "echo {task_path}"

[[task-validator]]
command = "test -d tasks/{task_dir_name}"
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


def _make_validator(
    tmp_dir: Path,
    runner_metadata: str = RUNNER_METADATA,
    task_metadata: str | None = VALID_TASK_METADATA,
    task_dir: str = "task",
) -> tuple[Path, Path, TaskValidator]:
    runner_path = tmp_dir / "runner"
    runner_path.mkdir()
    (runner_path / "metadata.toml").write_text(runner_metadata)
    task_path = tmp_dir / task_dir
    task_path.mkdir(parents=True)
    if task_metadata is not None:
        (task_path / "metadata.toml").write_text(task_metadata)
    return runner_path, task_path, TaskValidator(runner_path, task_path, tmp_dir / ".tmp")


class TestTaskValidatorMetadataExisted:
    def test_metadata_exists(self, tmp_dir: Path) -> None:
        _, _, validator = _make_validator(tmp_dir)
        validator.validate_metadata_existed()

    def test_metadata_not_exists(self, tmp_dir: Path) -> None:
        _, _, validator = _make_validator(tmp_dir, task_metadata=None)
        with pytest.raises(TaskValidatorException, match="metadata.toml not found"):
            validator.validate_metadata_existed()


class TestTaskValidatorMetadataStructure:
    def test_valid_metadata_local(self, tmp_dir: Path) -> None:
        _, _, validator = _make_validator(tmp_dir, task_metadata=VALID_TASK_METADATA_LOCAL)
        validator.validate_metadata_structure()

    def test_missing_id(self, tmp_dir: Path) -> None:
        content = VALID_TASK_METADATA.replace('id = "test-task"', '')
        _, _, validator = _make_validator(tmp_dir, task_metadata=content)
        with pytest.raises(TaskValidatorException, match="id is required"):
            validator.validate_metadata_structure()

    def test_missing_runner_id(self, tmp_dir: Path) -> None:
        content = VALID_TASK_METADATA.replace('runner_id = "test-runner"', '')
        _, _, validator = _make_validator(tmp_dir, task_metadata=content)
        with pytest.raises(TaskValidatorException, match="runner_id is required"):
            validator.validate_metadata_structure()

    def test_missing_default_timeout(self, tmp_dir: Path) -> None:
        content = VALID_TASK_METADATA.replace('default_timeout = "1h"', '')
        _, _, validator = _make_validator(tmp_dir, task_metadata=content)
        with pytest.raises(TaskValidatorException, match="default_timeout is required"):
            validator.validate_metadata_structure()

    def test_invalid_timeout_format(self, tmp_dir: Path) -> None:
        content = VALID_TASK_METADATA.replace('default_timeout = "1h"', 'default_timeout = "1x"')
        _, _, validator = _make_validator(tmp_dir, task_metadata=content)
        with pytest.raises(TaskValidatorException, match="must be in format"):
            validator.validate_metadata_structure()


class TestTaskValidatorRunnerCompatibility:
    def test_compatible(self, tmp_dir: Path) -> None:
        _, _, validator = _make_validator(tmp_dir)
        validator.validate_metadata_structure()
        validator.check_runner_compatibility()

    def test_runner_id_mismatch(self, tmp_dir: Path) -> None:
        content = VALID_TASK_METADATA.replace('runner_id = "test-runner"', 'runner_id = "other-runner"')
        _, _, validator = _make_validator(tmp_dir, task_metadata=content)
        validator.validate_metadata_structure()
        with pytest.raises(TaskValidatorException, match="does not match"):
            validator.check_runner_compatibility()

    def test_runner_version_incompatible(self, tmp_dir: Path) -> None:
        content = VALID_TASK_METADATA.replace('runner_min_version = ">=0.1.0"', 'runner_min_version = ">=2.0.0"')
        _, _, validator = _make_validator(tmp_dir, task_metadata=content)
        validator.validate_metadata_structure()
        with pytest.raises(TaskValidatorException, match="does not satisfy"):
            validator.check_runner_compatibility()

    def test_runner_version_compatible_with_spec(self, tmp_dir: Path) -> None:
        content = VALID_TASK_METADATA.replace('runner_min_version = ">=0.1.0"', 'runner_min_version = ">=0.1.0,<2.0.0"')
        _, _, validator = _make_validator(tmp_dir, task_metadata=content)
        validator.validate_metadata_structure()
        validator.check_runner_compatibility()


class TestTaskValidatorRunnerValidators:
    def test_missing_required_file_fails_validation(self, tmp_dir: Path) -> None:
        _, _, validator = _make_validator(tmp_dir, runner_metadata=RUNNER_WITH_VALIDATOR)
        validator.validate_metadata_existed()
        validator.validate_metadata_structure()
        validator.check_runner_compatibility()
        with pytest.raises(TaskValidatorException, match="Task validator command failed"):
            validator.execute_runner_validators()

    def test_required_file_present_passes_validation(self, tmp_dir: Path) -> None:
        _, task_path, validator = _make_validator(tmp_dir, runner_metadata=RUNNER_WITH_VALIDATOR)
        (task_path / "required_file").write_text("content")
        validator.validate_metadata_existed()
        validator.validate_metadata_structure()
        validator.check_runner_compatibility()
        validator.execute_runner_validators()

    def test_task_dir_name_substituted_in_validator(self, tmp_dir: Path) -> None:
        _, _, validator = _make_validator(
            tmp_dir,
            runner_metadata=RUNNER_WITH_TASK_DIR_NAME_VALIDATOR,
            task_dir="runner/tasks/test-task",
        )
        validator.validate_metadata_existed()
        validator.validate_metadata_structure()
        validator.check_runner_compatibility()
        validator.execute_runner_validators()
