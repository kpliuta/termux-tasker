from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from textual.app import App, ComposeResult
from textual.content import Content
from textual.widgets import Static

from termux_tasker.config import RunnerSettings, TaskMetadata, TaskSettings
from termux_tasker.ui.screens.task_menu import (
    TaskMenuScreen,
    build_task_key_value_entries,
    build_task_suffixes,
    task_phase_durations,
)


def _settings(
    last_run: str = "none",
    last_status: str = "none",
    before: int | None = None,
    exec_dur: int | None = None,
    after: int | None = None,
) -> TaskSettings:
    settings = TaskSettings()
    settings.session.last_run = last_run
    settings.session.last_run_status = last_status
    settings.session.last_run_before_duration = before
    settings.session.last_run_exec_duration = exec_dur
    settings.session.last_run_after_duration = after
    return settings


def _meta() -> TaskMetadata:
    meta = TaskMetadata()
    meta.general.version = "1.0.0"
    return meta


class TestBuildTaskKeyValueEntries:
    def test_rows_in_order(self) -> None:
        entries = build_task_key_value_entries(_meta(), _settings())
        assert [entry.key for entry in entries] == [
            "Version",
            "Enabled",
            "Timeout",
            "Last Run",
            "Last Status",
        ]

    def test_never_run_shows_na(self) -> None:
        entries = build_task_key_value_entries(_meta(), _settings())
        values = {entry.key: entry.value for entry in entries}
        assert values["Last Run"] == "n/a"
        assert values["Last Status"] == "n/a"

    def test_run_values_pass_through(self) -> None:
        settings = _settings(last_run="2026-09-04 20:18:45", last_status="success")
        entries = build_task_key_value_entries(_meta(), settings)
        values = {entry.key: entry.value for entry in entries}
        assert values["Last Run"] == "2026-09-04 20:18:45"
        assert values["Last Status"] == "success"

    def test_fail_status_passes_through(self) -> None:
        entries = build_task_key_value_entries(
            _meta(), _settings(last_status="fail")
        )
        values = {entry.key: entry.value for entry in entries}
        assert values["Last Status"] == "fail"


class TestBuildTaskSuffixes:
    def test_stopped_without_idle_has_no_suffix(self) -> None:
        suffixes = build_task_suffixes(
            current_state="stopped",
            phase_durations=(2, 65, 4),
            elapsed_sec=None,
            idle_remaining=None,
        )
        assert suffixes == {}

    def test_stopped_with_idle_shows_countdown(self) -> None:
        suffixes = build_task_suffixes(
            current_state="stopped",
            phase_durations=(2, 65, 4),
            elapsed_sec=None,
            idle_remaining=45,
        )
        assert suffixes["stopped"].plain == "[45]"
        assert "running" not in suffixes

    def test_running_shows_aggregate_plus_elapsed(self) -> None:
        suffixes = build_task_suffixes(
            current_state="running",
            phase_durations=(2, 65, 3600),
            elapsed_sec=27,
            idle_remaining=None,
        )
        assert suffixes["running"].plain == "[01:01:07][27]"
        assert "stopped" not in suffixes

    def test_running_without_proc_shows_aggregate_only(self) -> None:
        suffixes = build_task_suffixes(
            current_state="running",
            phase_durations=(2, 65, 4),
            elapsed_sec=None,
            idle_remaining=None,
        )
        assert suffixes["running"].plain == "[01:11]"

    def test_running_missing_phases_count_as_zero(self) -> None:
        suffixes = build_task_suffixes(
            current_state="running",
            phase_durations=(None, None, None),
            elapsed_sec=None,
            idle_remaining=None,
        )
        assert suffixes["running"].plain == "[0]"

    def test_span_styles_keep_theme_vars(self) -> None:
        suffixes = build_task_suffixes(
            current_state="running",
            phase_durations=(2, 65, 4),
            elapsed_sec=27,
            idle_remaining=None,
        )
        idle = build_task_suffixes(
            current_state="stopped",
            phase_durations=(2, 65, 4),
            elapsed_sec=None,
            idle_remaining=45,
        )
        running_styles = [
            str(style)
            for _, _, style in suffixes["running"]._spans  # noqa
            if isinstance(style, str)
        ]
        assert running_styles == ["$foreground-disabled", "bold $text-success"]
        idle_styles = [
            str(style)
            for _, _, style in idle["stopped"]._spans  # noqa
            if isinstance(style, str)
        ]
        assert idle_styles == ["bold $text-warning"]
        for suffix in list(suffixes.values()) + list(idle.values()):
            assert isinstance(suffix, Content)


class TestTaskPhaseDurations:
    def test_picks_phases_in_order(self) -> None:
        settings = _settings(before=2, exec_dur=65, after=4)
        assert task_phase_durations(settings) == (2, 65, 4)

    def test_missing_is_none(self) -> None:
        assert task_phase_durations(_settings()) == (None, None, None)


SH_RUNNER_METADATA = """\
[general]
id = "sh_runner"
name = "Simple sh runner"
version = "1.1.0"
app_min_version = ">=0.1.0"

[exec]
"""

SH_TASK_METADATA = """\
[general]
id = "sh_task"
name = "Simple task"
version = "1.0.0"
runner_id = "sh_runner"
runner_min_version = ">=1.0.0"
"""


def _write_runner_dir(path: Path, *, state: str = "idle") -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "metadata.toml").write_text(SH_RUNNER_METADATA)
    settings = RunnerSettings()
    settings.general.enabled = True
    settings.session.session_id = "test-session"
    settings.session.state = state
    settings.save(path / "settings.toml")
    return path


def _write_task_dir(path: Path, *, enabled: bool, state: str = "stopped") -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "metadata.toml").write_text(SH_TASK_METADATA)
    settings = TaskSettings()
    settings.general.enabled = enabled
    settings.session.session_id = "test-session"
    settings.session.state = state
    settings.save(path / "settings.toml")
    return path


class _TaskMenuTestApp(App[None]):
    def __init__(self) -> None:
        super().__init__()
        self.state: Any = SimpleNamespace(session_id="test-session", runners={})

    def compose(self) -> ComposeResult:
        yield Static()


class TestStoppedIdleSuffixEnabledGate:
    @pytest.mark.asyncio
    async def test_idle_countdown_shown_when_task_enabled(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        runner_dir = _write_runner_dir(tmp_path / "sh_runner")
        task_path = _write_task_dir(runner_dir / "tasks" / "sh_task", enabled=True)
        proc = MagicMock()
        proc.state_elapsed.return_value = 15
        proc.current_task_path = None
        async with _TaskMenuTestApp().run_test() as pilot:
            screen = TaskMenuScreen(task_path)
            await pilot.app.push_screen(screen)
            monkeypatch.setattr(screen, "_live_runner_proc", lambda: proc)
            settings = TaskSettings.load(task_path / "settings.toml")
            suffixes = screen._build_suffixes(settings)
            assert suffixes["stopped"].plain == "[45]"

    @pytest.mark.asyncio
    async def test_idle_countdown_hidden_when_task_disabled(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        runner_dir = _write_runner_dir(tmp_path / "sh_runner")
        task_path = _write_task_dir(runner_dir / "tasks" / "sh_task", enabled=False)
        proc = MagicMock()
        proc.state_elapsed.return_value = 15
        proc.current_task_path = None
        async with _TaskMenuTestApp().run_test() as pilot:
            screen = TaskMenuScreen(task_path)
            await pilot.app.push_screen(screen)
            monkeypatch.setattr(screen, "_live_runner_proc", lambda: proc)
            settings = TaskSettings.load(task_path / "settings.toml")
            suffixes = screen._build_suffixes(settings)
            assert "stopped" not in suffixes
