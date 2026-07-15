from __future__ import annotations

from pathlib import Path
from subprocess import SubprocessError
from unittest.mock import patch, MagicMock

import pytest

from termux_tasker.ui.screens._utils import (
    fetch_git_tags,
    get_installed_runner_version,
    get_installed_task_version,
    sanitize_id,
)
from termux_tasker.config import RunnerMetadata, RunnerSettings, TaskMetadata


# --- sanitize_id ---

class TestSanitizeId:
    def test_valid_name_unchanged(self) -> None:
        assert sanitize_id("my_tag-1") == "my_tag-1"

    def test_leading_digit_gets_underscore(self) -> None:
        assert sanitize_id("1_0_0") == "_1_0_0"

    def test_dots_replaced(self) -> None:
        assert sanitize_id("1.0.0") == "_1_0_0"

    def test_spaces_replaced(self) -> None:
        assert sanitize_id("my tag") == "my_tag"

    def test_special_chars_replaced(self) -> None:
        assert sanitize_id("tag@v1!") == "tag_v1_"

    def test_empty_string(self) -> None:
        assert sanitize_id("") == "_"

    def test_leading_underscore_preserved(self) -> None:
        assert sanitize_id("_private") == "_private"

    def test_only_special_chars(self) -> None:
        assert sanitize_id("!@#") == "___"


# --- fetch_git_tags ---

class TestFetchGitTags:
    def test_returns_tags(self, tmp_dir: Path) -> None:
        mock_result = MagicMock(returncode=0, stdout="1.0.0\n2.0.0\n")
        with patch("subprocess.run", return_value=mock_result):
            tags = fetch_git_tags(tmp_dir)
        assert tags == ["1.0.0", "2.0.0"]

    def test_returns_empty_when_no_tags(self, tmp_dir: Path) -> None:
        mock_result = MagicMock(returncode=0, stdout="\n")
        with patch("subprocess.run", return_value=mock_result):
            tags = fetch_git_tags(tmp_dir)
        assert tags == []

    def test_returns_empty_on_subprocess_error(self, tmp_dir: Path) -> None:
        with patch("subprocess.run", side_effect=SubprocessError):
            tags = fetch_git_tags(tmp_dir)
        assert tags == []

    def test_single_tag(self, tmp_dir: Path) -> None:
        mock_result = MagicMock(returncode=0, stdout="0.1.0\n")
        with patch("subprocess.run", return_value=mock_result):
            tags = fetch_git_tags(tmp_dir)
        assert tags == ["0.1.0"]

    def test_return_type_is_list(self, tmp_dir: Path) -> None:
        mock_result = MagicMock(returncode=0, stdout="1.0.0\n")
        with patch("subprocess.run", return_value=mock_result):
            tags = fetch_git_tags(tmp_dir)
        assert isinstance(tags, list)


# --- get_installed_runner_version ---

class TestGetInstalledRunnerVersion:
    def test_returns_version_from_matching_runner(
        self, tmp_dir: Path
    ) -> None:
        runners_path = tmp_dir / "runners"
        runner_dir = runners_path / "sh_runner"
        runner_dir.mkdir(parents=True)
        (runner_dir / "metadata.toml").write_text(
            '[general]\nid = "sh_runner"\nname = "Test"\n'
            'version = "2.0.0"\napp_min_version = ">=0.1.0"\n'
        )
        result = get_installed_runner_version(runners_path, "sh_runner")
        assert result == "2.0.0"

    def test_returns_none_for_different_runner_id(self, tmp_dir: Path) -> None:
        runners_path = tmp_dir / "runners"
        runner_dir = runners_path / "other"
        runner_dir.mkdir(parents=True)
        (runner_dir / "metadata.toml").write_text(
            '[general]\nid = "other"\nname = "Other"\n'
            'version = "1.0.0"\napp_min_version = ">=0.1.0"\n'
        )
        result = get_installed_runner_version(runners_path, "test")
        assert result is None

    def test_returns_none_when_no_runners_path(self, tmp_dir: Path) -> None:
        result = get_installed_runner_version(tmp_dir / "nonexistent", "test")
        assert result is None

    def test_returns_none_when_no_metadata(self, tmp_dir: Path) -> None:
        runners_path = tmp_dir / "runners"
        runner_dir = runners_path / "no_meta"
        runner_dir.mkdir(parents=True)
        result = get_installed_runner_version(runners_path, "no_meta")
        assert result is None


# --- get_installed_task_version ---

class TestGetInstalledTaskVersion:
    def test_returns_version_from_matching_task(
        self, tmp_dir: Path
    ) -> None:
        tasks_path = tmp_dir / "tasks"
        task_dir = tasks_path / "my_task"
        task_dir.mkdir(parents=True)
        (task_dir / "metadata.toml").write_text(
            '[general]\nid = "my_task"\nname = "My Task"\n'
            'version = "3.0.0"\nrunner_id = "r"\n'
            'runner_min_version = ">=0.1.0"\ndefault_timeout = "1h"\n'
        )
        result = get_installed_task_version(tasks_path, "my_task")
        assert result == "3.0.0"

    def test_returns_none_for_different_task_id(self, tmp_dir: Path) -> None:
        tasks_path = tmp_dir / "tasks"
        task_dir = tasks_path / "other"
        task_dir.mkdir(parents=True)
        (task_dir / "metadata.toml").write_text(
            '[general]\nid = "other_task"\nname = "Other"\n'
            'version = "1.0.0"\nrunner_id = "r"\n'
            'runner_min_version = ">=0.1.0"\ndefault_timeout = "1h"\n'
        )
        result = get_installed_task_version(tasks_path, "my_task")
        assert result is None

    def test_returns_none_when_no_tasks_path(self, tmp_dir: Path) -> None:
        result = get_installed_task_version(tmp_dir / "nonexistent", "task")
        assert result is None
