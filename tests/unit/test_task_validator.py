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
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_METADATA)

        task_path = tmp_dir / "task"
        task_path.mkdir()
        (task_path / "metadata.toml").write_text(VALID_TASK_METADATA)

        validator = TaskValidator(runner_path, task_path, tmp_dir / ".tmp")
        validator.validate_metadata_existed()

    def test_metadata_not_exists(self, tmp_dir: Path) -> None:
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_METADATA)

        task_path = tmp_dir / "task"
        task_path.mkdir()

        validator = TaskValidator(runner_path, task_path, tmp_dir / ".tmp")
        with pytest.raises(TaskValidatorException, match="metadata.toml not found"):
            validator.validate_metadata_existed()


class TestTaskValidatorMetadataStructure:
    def test_valid_metadata_local(self, tmp_dir: Path) -> None:
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_METADATA)

        task_path = tmp_dir / "task"
        task_path.mkdir()
        (task_path / "metadata.toml").write_text(VALID_TASK_METADATA_LOCAL)

        validator = TaskValidator(runner_path, task_path, tmp_dir / ".tmp")
        validator.validate_metadata_structure()

    def test_missing_id(self, tmp_dir: Path) -> None:
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_METADATA)

        task_path = tmp_dir / "task"
        task_path.mkdir()
        content = VALID_TASK_METADATA.replace('id = "test-task"', '')
        (task_path / "metadata.toml").write_text(content)

        validator = TaskValidator(runner_path, task_path, tmp_dir / ".tmp")
        with pytest.raises(TaskValidatorException, match="id is required"):
            validator.validate_metadata_structure()

    def test_missing_runner_id(self, tmp_dir: Path) -> None:
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_METADATA)

        task_path = tmp_dir / "task"
        task_path.mkdir()
        content = VALID_TASK_METADATA.replace('runner_id = "test-runner"', '')
        (task_path / "metadata.toml").write_text(content)

        validator = TaskValidator(runner_path, task_path, tmp_dir / ".tmp")
        with pytest.raises(TaskValidatorException, match="runner_id is required"):
            validator.validate_metadata_structure()

    def test_missing_default_timeout(self, tmp_dir: Path) -> None:
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_METADATA)

        task_path = tmp_dir / "task"
        task_path.mkdir()
        content = VALID_TASK_METADATA.replace('default_timeout = "1h"', '')
        (task_path / "metadata.toml").write_text(content)

        validator = TaskValidator(runner_path, task_path, tmp_dir / ".tmp")
        with pytest.raises(TaskValidatorException, match="default_timeout is required"):
            validator.validate_metadata_structure()

    def test_invalid_timeout_format(self, tmp_dir: Path) -> None:
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_METADATA)

        task_path = tmp_dir / "task"
        task_path.mkdir()
        content = VALID_TASK_METADATA.replace('default_timeout = "1h"', 'default_timeout = "1x"')
        (task_path / "metadata.toml").write_text(content)

        validator = TaskValidator(runner_path, task_path, tmp_dir / ".tmp")
        with pytest.raises(TaskValidatorException, match="must be in format"):
            validator.validate_metadata_structure()


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


class TestTaskValidatorRunnerCompatibility:
    def test_compatible(self, tmp_dir: Path) -> None:
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_METADATA)

        task_path = tmp_dir / "task"
        task_path.mkdir()
        (task_path / "metadata.toml").write_text(VALID_TASK_METADATA)

        validator = TaskValidator(runner_path, task_path, tmp_dir / ".tmp")
        validator.validate_metadata_structure()
        validator.check_runner_compatibility()

    def test_runner_id_mismatch(self, tmp_dir: Path) -> None:
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_METADATA)

        task_path = tmp_dir / "task"
        task_path.mkdir()
        content = VALID_TASK_METADATA.replace('runner_id = "test-runner"', 'runner_id = "other-runner"')
        (task_path / "metadata.toml").write_text(content)

        validator = TaskValidator(runner_path, task_path, tmp_dir / ".tmp")
        validator.validate_metadata_structure()
        with pytest.raises(TaskValidatorException, match="does not match"):
            validator.check_runner_compatibility()

    def test_runner_version_incompatible(self, tmp_dir: Path) -> None:
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_METADATA)

        task_path = tmp_dir / "task"
        task_path.mkdir()
        content = VALID_TASK_METADATA.replace('runner_min_version = ">=0.1.0"', 'runner_min_version = ">=2.0.0"')
        (task_path / "metadata.toml").write_text(content)

        validator = TaskValidator(runner_path, task_path, tmp_dir / ".tmp")
        validator.validate_metadata_structure()
        with pytest.raises(TaskValidatorException, match="does not satisfy"):
            validator.check_runner_compatibility()

    def test_runner_version_compatible_with_spec(self, tmp_dir: Path) -> None:
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_METADATA)

        task_path = tmp_dir / "task"
        task_path.mkdir()
        content = VALID_TASK_METADATA.replace('runner_min_version = ">=0.1.0"', 'runner_min_version = ">=0.1.0,<2.0.0"')
        (task_path / "metadata.toml").write_text(content)

        validator = TaskValidator(runner_path, task_path, tmp_dir / ".tmp")
        validator.validate_metadata_structure()
        validator.check_runner_compatibility()


class TestTaskValidatorRunnerValidators:
    def test_missing_required_file_fails_validation(self, tmp_dir: Path) -> None:
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_WITH_VALIDATOR)

        task_path = tmp_dir / "task"
        task_path.mkdir()
        (task_path / "metadata.toml").write_text(VALID_TASK_METADATA)

        validator = TaskValidator(runner_path, task_path, tmp_dir / ".tmp")
        validator.validate_metadata_existed()
        validator.validate_metadata_structure()
        validator.check_runner_compatibility()
        with pytest.raises(TaskValidatorException, match="Task validator command failed"):
            validator.execute_runner_validators()

    def test_required_file_present_passes_validation(self, tmp_dir: Path) -> None:
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_WITH_VALIDATOR)

        task_path = tmp_dir / "task"
        task_path.mkdir()
        (task_path / "metadata.toml").write_text(VALID_TASK_METADATA)
        (task_path / "required_file").write_text("content")

        validator = TaskValidator(runner_path, task_path, tmp_dir / ".tmp")
        validator.validate_metadata_existed()
        validator.validate_metadata_structure()
        validator.check_runner_compatibility()
        validator.execute_runner_validators()

    def test_task_dir_name_substituted_in_validator(self, tmp_dir: Path) -> None:
        runner_path = tmp_dir / "runner"
        runner_path.mkdir()
        (runner_path / "metadata.toml").write_text(RUNNER_WITH_TASK_DIR_NAME_VALIDATOR)
        (runner_path / "tasks").mkdir()

        task_path = runner_path / "tasks" / "test-task"
        task_path.mkdir(parents=True)
        (task_path / "metadata.toml").write_text(VALID_TASK_METADATA)

        validator = TaskValidator(runner_path, task_path, tmp_dir / ".tmp")
        validator.validate_metadata_existed()
        validator.validate_metadata_structure()
        validator.check_runner_compatibility()
        validator.execute_runner_validators()
