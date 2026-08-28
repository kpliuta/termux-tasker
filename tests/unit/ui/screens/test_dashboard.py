from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from textual.app import App
from textual.widgets import Static

from termux_tasker.config import RunnerSettings, TaskSettings
from termux_tasker.ui.screens.dashboard import DashboardScreen


SH_RUNNER_METADATA = """\
[general]
id = "sh_runner"
name = "Simple sh runner"
description = "A simple shell-based runner."
version = "1.1.0"
app_min_version = ">=0.1.0"

[exec]
"""

SH_TASK_METADATA = """\
[general]
id = "sh_task"
name = "Simple task"
description = "A simple task."
version = "1.0.0"
runner_id = "sh_runner"
runner_min_version = ">=1.0.0"
"""


def _write_runner(path: Path, metadata: str, enabled: bool = False, state: str = "off") -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "metadata.toml").write_text(metadata)
    settings = RunnerSettings()
    settings.general.enabled = enabled
    settings.session.session_id = "test-session"
    settings.session.state = state
    settings.save(path / "settings.toml")


def _write_task(path: Path, metadata: str, enabled: bool = False, state: str = "stopped") -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "metadata.toml").write_text(metadata)
    settings = TaskSettings()
    settings.general.enabled = enabled
    settings.session.session_id = "test-session"
    settings.session.state = state
    settings.save(path / "settings.toml")


def _make_mock_app(runners_path: Path) -> Any:
    app = MagicMock()
    app.state.runners_path = runners_path
    return app


class TestDashboardInit:
    def test_column_count(self) -> None:
        screen = DashboardScreen()
        assert screen._column_count == 2

    def test_description(self) -> None:
        screen = DashboardScreen()
        assert screen.description == "[b]Overview[/b]"

    def test_description_max_height(self) -> None:
        screen = DashboardScreen()
        assert screen._description_max_height == "50%"

    def test_title(self) -> None:
        screen = DashboardScreen()
        assert screen.title == "Dashboard"


class TestDashboardOverview:
    def test_no_runners(self, tmp_path: Path) -> None:
        screen = DashboardScreen()
        runners_path = tmp_path / "runners"
        runners_path.mkdir()
        result = screen._build_overview(runners_path)
        assert "Overview" in result
        assert "No runners installed" in result

    def test_runners_path_not_exists(self, tmp_path: Path) -> None:
        screen = DashboardScreen()
        runners_path = tmp_path / "nonexistent"
        result = screen._build_overview(runners_path)
        assert "No runners installed" in result

    def test_one_runner_no_tasks(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        _write_runner(runners_path / "sh_runner", SH_RUNNER_METADATA, enabled=False, state="off")

        screen = DashboardScreen()
        result = screen._build_overview(runners_path)
        assert "Simple sh runner" in result
        assert "[off]" in result

    def test_runner_with_tasks(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        runner_dir = runners_path / "sh_runner"
        _write_runner(runner_dir, SH_RUNNER_METADATA, enabled=True, state="idle")
        _write_task(runner_dir / "tasks" / "sh_task", SH_TASK_METADATA, enabled=True, state="running")

        screen = DashboardScreen()
        result = screen._build_overview(runners_path)
        assert "Simple sh runner" in result
        assert "[idle]" in result
        assert "Simple task" in result
        assert "[running]" in result

    def test_tree_prefix_last_task(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        runner_dir = runners_path / "sh_runner"
        _write_runner(runner_dir, SH_RUNNER_METADATA, enabled=True, state="idle")

        task1_meta = SH_TASK_METADATA.replace('"sh_task"', '"task_a"').replace('"Simple task"', '"Task A"')
        task2_meta = SH_TASK_METADATA.replace('"sh_task"', '"task_b"').replace('"Simple task"', '"Task B"')
        _write_task(runner_dir / "tasks" / "task_a", task1_meta, enabled=True, state="running")
        _write_task(runner_dir / "tasks" / "task_b", task2_meta, enabled=False, state="stopped")

        screen = DashboardScreen()
        result = screen._build_overview(runners_path)
        lines = result.split("\n")
        task_lines = [l for l in lines if "Task" in l and ("running" in l or "stopped" in l)]
        assert len(task_lines) == 2
        assert "\u251c\u2500" in task_lines[0]
        assert "\u2514\u2500" in task_lines[1]

    def test_disabled_runner_shows_red_emoji(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        _write_runner(runners_path / "sh_runner", SH_RUNNER_METADATA, enabled=False, state="off")

        screen = DashboardScreen()
        result = screen._build_overview(runners_path)
        assert "\U0001f534" in result

    def test_idle_runner_shows_yellow_emoji(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        _write_runner(runners_path / "sh_runner", SH_RUNNER_METADATA, enabled=True, state="idle")

        screen = DashboardScreen()
        result = screen._build_overview(runners_path)
        assert "\U0001f7e1" in result

    def test_working_runner_shows_green_emoji(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        _write_runner(runners_path / "sh_runner", SH_RUNNER_METADATA, enabled=True, state="task-exec")

        screen = DashboardScreen()
        result = screen._build_overview(runners_path)
        assert "\U0001f7e2" in result

    def test_multiple_runners_sorted(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        meta_b = SH_RUNNER_METADATA.replace('"sh_runner"', '"b_runner"').replace('"Simple sh runner"', '"B Runner"')
        meta_a = SH_RUNNER_METADATA.replace('"sh_runner"', '"a_runner"').replace('"Simple sh runner"', '"A Runner"')
        _write_runner(runners_path / "b_runner", meta_b, enabled=True, state="idle")
        _write_runner(runners_path / "a_runner", meta_a, enabled=True, state="idle")

        screen = DashboardScreen()
        result = screen._build_overview(runners_path)
        lines = result.split("\n")
        runner_lines = [l for l in lines if "Runner" in l and "[idle]" in l]
        assert len(runner_lines) == 2
        assert "A Runner" in runner_lines[0]
        assert "B Runner" in runner_lines[1]


class TestDashboardCompose:
    @pytest.mark.asyncio
    async def test_renders_overview(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        runners_path.mkdir()
        mock_app = _make_mock_app(runners_path)

        with patch("termux_tasker.ui.screens.dashboard.termux_app", return_value=mock_app):
            class TestApp(App):
                def on_mount(self) -> None:
                    self.push_screen(DashboardScreen())

            async with TestApp().run_test() as pilot:
                screen = pilot.app.screen
                assert isinstance(screen, DashboardScreen)
                desc = screen.query_one("#description", Static)
                assert "Overview" in str(desc.render())     # noqa

    @pytest.mark.asyncio
    async def test_two_column_layout(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        runners_path.mkdir()
        mock_app = _make_mock_app(runners_path)

        with patch("termux_tasker.ui.screens.dashboard.termux_app", return_value=mock_app):
            class TestApp(App):
                def on_mount(self) -> None:
                    self.push_screen(DashboardScreen())

            async with TestApp().run_test() as pilot:
                from textual.containers import Horizontal
                rows = pilot.app.screen.query(".button-row")
                assert len(rows) >= 1
                first_row = rows[0]
                assert isinstance(first_row, Horizontal)
                buttons_in_row = first_row.query("Button")
                assert len(buttons_in_row) == 2

    @pytest.mark.asyncio
    async def test_exit_button_in_bottom_bar(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        runners_path.mkdir()
        mock_app = _make_mock_app(runners_path)

        with patch("termux_tasker.ui.screens.dashboard.termux_app", return_value=mock_app):
            class TestApp(App):
                def on_mount(self) -> None:
                    self.push_screen(DashboardScreen())

            async with TestApp().run_test() as pilot:
                bottom = pilot.app.screen.query_one("#bottom-container")
                exit_btn = bottom.query_one("#exit")
                assert exit_btn is not None
