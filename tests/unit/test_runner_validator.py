from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from termux_tasker.runner_validator import RunnerValidator, RunnerValidatorException


VALID_METADATA = """\
[general]
id = "test-runner"
name = "Test Runner"
description = "A test runner"
version = "0.1.0"
url = "https://github.com/user/test-runner"
app_min_version = ">=0.1.0"

[exec]
task-exec = "echo {task_dir}"
"""

VALID_METADATA_LOCAL = """\
[general]
id = "test-runner-local"
name = "Test Runner Local"
version = "1.0"
app_min_version = ">=0.0.1"

[exec]
task-exec = "echo {task_dir}"
"""

INVALID_METADATA_NO_TASK_EXEC = """\
[general]
id = "test-runner"
name = "Test Runner"
version = "0.1.0"
app_min_version = ">=0.1.0"

[exec]
"""


class TestRunnerValidatorMetadataExisted:
    def test_metadata_exists(self, tmp_dir: Path) -> None:
        (tmp_dir / "metadata.toml").write_text(VALID_METADATA)
        validator = RunnerValidator(tmp_dir)
        validator.validate_metadata_existed()

    def test_metadata_not_exists(self, tmp_dir: Path) -> None:
        validator = RunnerValidator(tmp_dir)
        with pytest.raises(RunnerValidatorException, match="metadata.toml not found"):
            validator.validate_metadata_existed()


class TestRunnerValidatorMetadataStructure:
    def test_valid_metadata_local(self, tmp_dir: Path) -> None:
        (tmp_dir / "metadata.toml").write_text(VALID_METADATA_LOCAL)
        validator = RunnerValidator(tmp_dir, app_version="1.0")
        validator.validate_metadata_structure()

    def test_missing_id(self, tmp_dir: Path) -> None:
        content = VALID_METADATA.replace('id = "test-runner"', '')
        (tmp_dir / "metadata.toml").write_text(content)
        validator = RunnerValidator(tmp_dir)
        with pytest.raises(RunnerValidatorException, match="id is required"):
            validator.validate_metadata_structure()

    def test_invalid_id_chars(self, tmp_dir: Path) -> None:
        content = VALID_METADATA.replace('id = "test-runner"', 'id = "test runner!"')
        (tmp_dir / "metadata.toml").write_text(content)
        validator = RunnerValidator(tmp_dir)
        with pytest.raises(RunnerValidatorException, match="id.*must consist"):
            validator.validate_metadata_structure()

    def test_missing_name(self, tmp_dir: Path) -> None:
        content = VALID_METADATA.replace('name = "Test Runner"', '')
        (tmp_dir / "metadata.toml").write_text(content)
        validator = RunnerValidator(tmp_dir)
        with pytest.raises(RunnerValidatorException, match="name is required"):
            validator.validate_metadata_structure()

    def test_missing_version(self, tmp_dir: Path) -> None:
        content = VALID_METADATA.replace('version = "0.1.0"', '')
        (tmp_dir / "metadata.toml").write_text(content)
        validator = RunnerValidator(tmp_dir)
        with pytest.raises(RunnerValidatorException, match="version is required"):
            validator.validate_metadata_structure()

    def test_missing_app_min_version(self, tmp_dir: Path) -> None:
        content = VALID_METADATA.replace('app_min_version = ">=0.1.0"', '')
        (tmp_dir / "metadata.toml").write_text(content)
        validator = RunnerValidator(tmp_dir)
        with pytest.raises(RunnerValidatorException, match="app_min_version is required"):
            validator.validate_metadata_structure()

    def test_missing_task_exec(self, tmp_dir: Path) -> None:
        (tmp_dir / "metadata.toml").write_text(INVALID_METADATA_NO_TASK_EXEC)
        validator = RunnerValidator(tmp_dir)
        with pytest.raises(RunnerValidatorException, match="task-exec is required"):
            validator.validate_metadata_structure()

    def test_invalid_task_exec_no_placeholder(self, tmp_dir: Path) -> None:
        content = VALID_METADATA.replace('task-exec = "echo {task_dir}"', 'task-exec = "echo hello"')
        (tmp_dir / "metadata.toml").write_text(content)
        validator = RunnerValidator(tmp_dir)
        with pytest.raises(RunnerValidatorException, match="task_dir"):
            validator.validate_metadata_structure()

    def test_invalid_url(self, tmp_dir: Path) -> None:
        content = VALID_METADATA.replace(
            'url = "https://github.com/user/test-runner"',
            'url = "https://gitlab.com/user/repo"'
        )
        (tmp_dir / "metadata.toml").write_text(content)
        (tmp_dir / ".git").mkdir()
        validator = RunnerValidator(tmp_dir)
        with pytest.raises(RunnerValidatorException, match="not a valid GitHub URL"):
            validator.validate_metadata_structure()

    def test_git_repo_url_required(self, tmp_dir: Path) -> None:
        content = VALID_METADATA.replace('url = "https://github.com/user/test-runner"', '')
        (tmp_dir / "metadata.toml").write_text(content)
        (tmp_dir / ".git").mkdir()
        validator = RunnerValidator(tmp_dir)
        with pytest.raises(RunnerValidatorException, match="url is required for git"):
            validator.validate_metadata_structure()

    def test_valid_properties(self, tmp_dir: Path) -> None:
        content = VALID_METADATA + """
[[property]]
name = "api-key"
description = "API key for service"
input-type = "text"
optional = false

[[property]]
name = "mode"
input-type = "radio"
optional = true
options = ["fast", "slow"]
default = "fast"
"""
        (tmp_dir / "metadata.toml").write_text(content)
        validator = RunnerValidator(tmp_dir)
        validator.validate_metadata_structure()

    def test_invalid_property_name(self, tmp_dir: Path) -> None:
        content = VALID_METADATA + """
[[property]]
name = "invalid name!"
input-type = "text"
optional = false
"""
        (tmp_dir / "metadata.toml").write_text(content)
        validator = RunnerValidator(tmp_dir)
        with pytest.raises(RunnerValidatorException, match="not a valid TOML key"):
            validator.validate_metadata_structure()

    def test_invalid_property_input_type(self, tmp_dir: Path) -> None:
        content = VALID_METADATA + """
[[property]]
name = "my-prop"
input-type = "invalid"
optional = false
"""
        (tmp_dir / "metadata.toml").write_text(content)
        validator = RunnerValidator(tmp_dir)
        with pytest.raises(RunnerValidatorException, match="input-type"):
            validator.validate_metadata_structure()

    def test_radio_missing_options(self, tmp_dir: Path) -> None:
        content = VALID_METADATA + """
[[property]]
name = "my-prop"
input-type = "radio"
optional = true
"""
        (tmp_dir / "metadata.toml").write_text(content)
        validator = RunnerValidator(tmp_dir)
        with pytest.raises(RunnerValidatorException, match="options is required"):
            validator.validate_metadata_structure()

    def test_default_not_in_options(self, tmp_dir: Path) -> None:
        content = VALID_METADATA + """
[[property]]
name = "my-prop"
input-type = "radio"
optional = true
options = ["a", "b"]
default = "c"
"""
        (tmp_dir / "metadata.toml").write_text(content)
        validator = RunnerValidator(tmp_dir)
        with pytest.raises(RunnerValidatorException, match="default.*must be one of options"):
            validator.validate_metadata_structure()


class TestRunnerValidatorGitVersion:
    def test_git_version_matches_tag(self, tmp_dir: Path) -> None:
        (tmp_dir / "metadata.toml").write_text(VALID_METADATA)
        (tmp_dir / ".git").mkdir()

        with patch.object(RunnerValidator, '_get_git_tag', return_value='0.1.0'):
            validator = RunnerValidator(tmp_dir)
            validator.validate_metadata_structure()

    def test_git_version_mismatches_tag(self, tmp_dir: Path) -> None:
        (tmp_dir / "metadata.toml").write_text(VALID_METADATA)
        (tmp_dir / ".git").mkdir()

        with patch.object(RunnerValidator, '_get_git_tag', return_value='0.2.0'):
            validator = RunnerValidator(tmp_dir)
            with pytest.raises(RunnerValidatorException, match="does not match git tag"):
                validator.validate_metadata_structure()


class TestRunnerValidatorBundled:
    def test_no_bundled_file(self, tmp_dir: Path) -> None:
        (tmp_dir / "metadata.toml").write_text(VALID_METADATA)
        validator = RunnerValidator(tmp_dir)
        validator.validate_bundled_structure()

    def test_valid_bundled(self, tmp_dir: Path) -> None:
        (tmp_dir / "metadata.toml").write_text(VALID_METADATA)
        (tmp_dir / "bundled.toml").write_text("""\
[[tasks]]
url = "https://github.com/user/task1"
""")
        validator = RunnerValidator(tmp_dir)
        validator.validate_bundled_structure()

    def test_invalid_bundled_url(self, tmp_dir: Path) -> None:
        (tmp_dir / "metadata.toml").write_text(VALID_METADATA)
        (tmp_dir / "bundled.toml").write_text("""\
[[tasks]]
url = "https://gitlab.com/user/task1"
""")
        validator = RunnerValidator(tmp_dir)
        with pytest.raises(RunnerValidatorException, match="not a valid GitHub URL"):
            validator.validate_bundled_structure()


class TestRunnerValidatorAppCompatibility:
    def test_compatible(self, tmp_dir: Path) -> None:
        (tmp_dir / "metadata.toml").write_text(VALID_METADATA)
        validator = RunnerValidator(tmp_dir, app_version="0.2.0")
        validator.validate_metadata_structure()
        validator.check_app_compatibility()

    def test_incompatible(self, tmp_dir: Path) -> None:
        (tmp_dir / "metadata.toml").write_text(VALID_METADATA)
        validator = RunnerValidator(tmp_dir, app_version="0.0.1")
        validator.validate_metadata_structure()
        with pytest.raises(RunnerValidatorException, match="does not satisfy"):
            validator.check_app_compatibility()


class TestRunnerValidatorValidate:
    def test_validate_passes(self, tmp_dir: Path) -> None:
        (tmp_dir / "metadata.toml").write_text(VALID_METADATA)
        validator = RunnerValidator(tmp_dir, app_version="0.2.0")
        validator.validate()

    def test_validate_fails_no_metadata(self, tmp_dir: Path) -> None:
        validator = RunnerValidator(tmp_dir)
        with pytest.raises(RunnerValidatorException):
            validator.validate()
