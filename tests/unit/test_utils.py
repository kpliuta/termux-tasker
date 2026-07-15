from __future__ import annotations

from pathlib import Path
from subprocess import SubprocessError
from unittest.mock import patch, MagicMock

import pytest

from termux_tasker.ui.screens._utils import (
    fetch_git_tags,
    get_installed_runner_versions,
    get_installed_task_versions,
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


# --- get_installed_runner_versions ---

class TestGetInstalledRunnerVersions:
    def test_returns_versions_from_matching_runners(
        self, tmp_dir: Path
    ) -> None:
        runners_path = tmp_dir / "runners"
        for version in ("1.0.0", "2.0.0"):
            runner_dir = runners_path / f"runner_{version}"
            runner_dir.mkdir(parents=True)
            (runner_dir / "metadata.toml").write_text(
                f'[general]\nid = "test"\nname = "Test"\n'
                f'version = "{version}"\napp_min_version = ">=0.1.0"\n'
            )
        result = get_installed_runner_versions(runners_path, "test")
        assert result == {"1.0.0", "2.0.0"}

    def test_ignores_different_runner_id(self, tmp_dir: Path) -> None:
        runners_path = tmp_dir / "runners"
        runner_dir = runners_path / "other"
        runner_dir.mkdir(parents=True)
        (runner_dir / "metadata.toml").write_text(
            '[general]\nid = "other"\nname = "Other"\n'
            'version = "1.0.0"\napp_min_version = ">=0.1.0"\n'
        )
        result = get_installed_runner_versions(runners_path, "test")
        assert result == set()

    def test_returns_empty_when_no_runners_path(self, tmp_dir: Path) -> None:
        result = get_installed_runner_versions(tmp_dir / "nonexistent", "test")
        assert result == set()

    def test_ignores_files_not_directories(self, tmp_dir: Path) -> None:
        runners_path = tmp_dir / "runners"
        runners_path.mkdir()
        (runners_path / "metadata.toml").write_text("not a dir")
        result = get_installed_runner_versions(runners_path, "test")
        assert result == set()

    def test_ignores_dirs_without_metadata(self, tmp_dir: Path) -> None:
        runners_path = tmp_dir / "runners"
        runner_dir = runners_path / "no_meta"
        runner_dir.mkdir(parents=True)
        result = get_installed_runner_versions(runners_path, "test")
        assert result == set()


# --- get_installed_task_versions ---

class TestGetInstalledTaskVersions:
    def test_returns_versions_from_matching_tasks(
        self, tmp_dir: Path
    ) -> None:
        tasks_path = tmp_dir / "tasks"
        for version in ("1.0.0", "3.0.0"):
            task_dir = tasks_path / f"task_{version}"
            task_dir.mkdir(parents=True)
            (task_dir / "metadata.toml").write_text(
                f'[general]\nid = "my_task"\nname = "My Task"\n'
                f'version = "{version}"\nrunner_id = "r"\n'
                f'runner_min_version = ">=0.1.0"\ndefault_timeout = "1h"\n'
            )
        result = get_installed_task_versions(tasks_path, "my_task")
        assert result == {"1.0.0", "3.0.0"}

    def test_ignores_different_task_id(self, tmp_dir: Path) -> None:
        tasks_path = tmp_dir / "tasks"
        task_dir = tasks_path / "other"
        task_dir.mkdir(parents=True)
        (task_dir / "metadata.toml").write_text(
            '[general]\nid = "other_task"\nname = "Other"\n'
            'version = "1.0.0"\nrunner_id = "r"\n'
            'runner_min_version = ">=0.1.0"\ndefault_timeout = "1h"\n'
        )
        result = get_installed_task_versions(tasks_path, "my_task")
        assert result == set()

    def test_returns_empty_when_no_tasks_path(self, tmp_dir: Path) -> None:
        result = get_installed_task_versions(tmp_dir / "nonexistent", "task")
        assert result == set()
