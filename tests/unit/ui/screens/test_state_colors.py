from __future__ import annotations

import pytest

from termux_tasker.config import RunnerSettings, TaskSettings
from termux_tasker.ui.screens._state_colors import (    # noqa
    DISABLED_COLOR,
    EMOJI_GREEN,
    EMOJI_RED,
    EMOJI_YELLOW,
    ENABLED_COLOR,
    RUNNER_STATE_COLORS,
    TASK_STATE_COLORS,
    runner_emoji,
    runner_state_color,
    task_state_color,
)


class TestRunnerStateColor:
    @pytest.mark.parametrize(
        "state,expected",
        [
            ("off", "$text-error"),
            ("initialization", "$text-success"),
            ("before-exec", "$text-success"),
            ("exec", "$text-success"),
            ("before-task", "$text-success"),
            ("task-exec", "$text-success"),
            ("after-task", "$text-success"),
            ("after-exec", "$text-success"),
            ("idle", "$text-warning"),
            ("termination", "$text-error"),
        ],
    )
    def test_runner_state_color_enabled(self, state: str, expected: str) -> None:
        settings = RunnerSettings()
        settings.general.enabled = True
        settings.session.state = state
        assert runner_state_color(settings) == expected

    def test_runner_state_color_disabled(self) -> None:
        settings = RunnerSettings()
        settings.general.enabled = False
        settings.session.state = "idle"
        assert runner_state_color(settings) == DISABLED_COLOR

    def test_runner_state_color_unknown_state(self) -> None:
        settings = RunnerSettings()
        settings.general.enabled = True
        settings.session.state = "unknown"
        assert runner_state_color(settings) == ENABLED_COLOR


class TestTaskStateColor:
    @pytest.mark.parametrize(
        "state,expected",
        [
            ("running", "$text-success"),
            ("stopped", "$text-error"),
        ],
    )
    def test_task_state_color_enabled(self, state: str, expected: str) -> None:
        settings = TaskSettings()
        settings.general.enabled = True
        settings.session.state = state
        assert task_state_color(settings) == expected

    def test_task_state_color_disabled(self) -> None:
        settings = TaskSettings()
        settings.general.enabled = False
        settings.session.state = "running"
        assert task_state_color(settings) == DISABLED_COLOR

    def test_task_state_color_unknown_state(self) -> None:
        settings = TaskSettings()
        settings.general.enabled = True
        settings.session.state = "unknown"
        assert task_state_color(settings) == ENABLED_COLOR


class TestRunnerEmoji:
    def test_enabled_working_state(self) -> None:
        settings = RunnerSettings()
        settings.general.enabled = True
        settings.session.state = "task-exec"
        assert runner_emoji(settings) == EMOJI_GREEN

    def test_enabled_initialization(self) -> None:
        settings = RunnerSettings()
        settings.general.enabled = True
        settings.session.state = "initialization"
        assert runner_emoji(settings) == EMOJI_GREEN

    def test_enabled_exec(self) -> None:
        settings = RunnerSettings()
        settings.general.enabled = True
        settings.session.state = "exec"
        assert runner_emoji(settings) == EMOJI_GREEN

    def test_enabled_idle(self) -> None:
        settings = RunnerSettings()
        settings.general.enabled = True
        settings.session.state = "idle"
        assert runner_emoji(settings) == EMOJI_YELLOW

    def test_disabled(self) -> None:
        settings = RunnerSettings()
        settings.general.enabled = False
        settings.session.state = "off"
        assert runner_emoji(settings) == EMOJI_RED

    def test_enabled_off(self) -> None:
        settings = RunnerSettings()
        settings.general.enabled = True
        settings.session.state = "off"
        assert runner_emoji(settings) == EMOJI_RED

    def test_enabled_termination(self) -> None:
        settings = RunnerSettings()
        settings.general.enabled = True
        settings.session.state = "termination"
        assert runner_emoji(settings) == EMOJI_RED

    def test_disabled_any_state(self) -> None:
        settings = RunnerSettings()
        settings.general.enabled = False
        settings.session.state = "idle"
        assert runner_emoji(settings) == EMOJI_RED


class TestConstants:
    def test_runner_state_colors_keys(self) -> None:
        expected_states = {
            "off", "initialization", "before-exec", "exec",
            "before-task", "task-exec", "after-task", "after-exec",
            "idle", "termination",
        }
        assert set(RUNNER_STATE_COLORS.keys()) == expected_states

    def test_task_state_colors_keys(self) -> None:
        assert set(TASK_STATE_COLORS.keys()) == {"running", "stopped"}

    def test_emoji_values(self) -> None:
        assert EMOJI_GREEN == "\U0001f7e2"
        assert EMOJI_YELLOW == "\U0001f7e1"
        assert EMOJI_RED == "\U0001f534"
