from __future__ import annotations

from textual.content import Content

from termux_tasker.config import RunnerMetadata, RunnerSettings
from termux_tasker.ui.screens.runner_menu import (
    _session_durations,  # noqa
    build_key_value_entries,
    build_state_suffixes,
)


def _settings(
    last_run: str = "none",
    init: int | None = None,
    before: int | None = None,
    exec_dur: int | None = None,
    after: int | None = None,
    termination: int | None = None,
) -> RunnerSettings:
    settings = RunnerSettings()
    settings.session.last_run = last_run
    settings.session.last_run_init_duration = init
    settings.session.last_run_before_duration = before
    settings.session.last_run_exec_duration = exec_dur
    settings.session.last_run_after_duration = after
    settings.session.last_run_termination_duration = termination
    return settings


def _meta() -> RunnerMetadata:
    meta = RunnerMetadata()
    meta.general.version = "1.1.0"
    return meta


def _last_durations(settings: RunnerSettings) -> dict[str, int | None]:
    return _session_durations(
        settings.session,
        {
            "initialization": "last_run_init_duration",
            "before-exec": "last_run_before_duration",
            "after-exec": "last_run_after_duration",
            "termination": "last_run_termination_duration",
        },
    )


def _span_styles(suffix: Content) -> list[str]:
    """Style strings of every span; theme vars must survive to render time."""
    return [str(style) for _, _, style in suffix._spans if isinstance(style, str)]  # noqa


class TestBuildKeyValueEntries:
    def test_rows_in_order(self) -> None:
        entries = build_key_value_entries(_meta(), _settings(), "n/a", "n/a")
        assert [entry.key for entry in entries] == [
            "Version",
            "Enabled",
            "PID",
            "RSS",
            "Last Run",
        ]

    def test_live_values_pass_through(self) -> None:
        settings = _settings(last_run="2026-09-04 20:18:45")
        entries = build_key_value_entries(_meta(), settings, "1944238+1", "13.2 MiB")
        values = {entry.key: entry.value for entry in entries}
        assert values["Version"] == "1.1.0"
        assert values["PID"] == "1944238+1"
        assert values["RSS"] == "13.2 MiB"
        assert values["Last Run"] == "2026-09-04 20:18:45"

    def test_never_run_shows_na(self) -> None:
        entries = build_key_value_entries(_meta(), _settings(), "n/a", "n/a")
        values = {entry.key: entry.value for entry in entries}
        assert values["PID"] == "n/a"
        assert values["RSS"] == "n/a"
        assert values["Last Run"] == "n/a"


class TestBuildStateSuffixes:
    def test_inactive_rows_show_prev_only(self) -> None:
        settings = _settings(init=1, before=93, after=5, termination=2)
        suffixes = build_state_suffixes(
            current_state="off",
            last_durations=_last_durations(settings),
            task_last_durations=None,
            elapsed_sec=None,
            exec_progress=None,
            idle_remaining=None,
        )
        assert suffixes["initialization"].plain == "[1]"
        assert suffixes["before-exec"].plain == "[01:33]"
        assert suffixes["after-exec"].plain == "[5]"
        assert suffixes["termination"].plain == "[2]"
        assert "before-task" not in suffixes
        assert "exec" not in suffixes
        assert "idle" not in suffixes

    def test_never_run_prev_shows_na(self) -> None:
        suffixes = build_state_suffixes(
            current_state="off",
            last_durations=_last_durations(_settings()),
            task_last_durations=None,
            elapsed_sec=None,
            exec_progress=None,
            idle_remaining=None,
        )
        assert suffixes["initialization"].plain == "[n/a]"
        assert suffixes["termination"].plain == "[n/a]"

    def test_active_row_appends_elapsed(self) -> None:
        settings = _settings(before=93)
        suffixes = build_state_suffixes(
            current_state="before-exec",
            last_durations=_last_durations(settings),
            task_last_durations=None,
            elapsed_sec=31,
            exec_progress=None,
            idle_remaining=None,
        )
        assert suffixes["before-exec"].plain == "[01:33][31]"
        assert suffixes["after-exec"].plain == "[n/a]"

    def test_task_rows_absent_without_running_task(self) -> None:
        settings = _settings(init=1)
        suffixes = build_state_suffixes(
            current_state="task-exec",
            last_durations=_last_durations(settings),
            task_last_durations=None,
            elapsed_sec=7,
            exec_progress=(1, 2),
            idle_remaining=None,
        )
        assert "before-task" not in suffixes
        assert "task-exec" not in suffixes
        assert "after-task" not in suffixes

    def test_task_rows_use_running_task_durations(self) -> None:
        settings = _settings()
        suffixes = build_state_suffixes(
            current_state="task-exec",
            last_durations=_last_durations(settings),
            task_last_durations={
                "before-task": 2,
                "task-exec": 65,
                "after-task": None,
            },
            elapsed_sec=9,
            exec_progress=(1, 2),
            idle_remaining=None,
        )
        assert suffixes["before-task"].plain == "[2]"
        assert suffixes["task-exec"].plain == "[01:05][9]"
        assert suffixes["after-task"].plain == "[n/a]"

    def test_exec_progress_only_when_task_state_active(self) -> None:
        settings = _settings()
        active = build_state_suffixes(
            current_state="task-exec",
            last_durations=_last_durations(settings),
            task_last_durations={},
            elapsed_sec=1,
            exec_progress=(1, 2),
            idle_remaining=None,
        )
        assert active["exec"].plain == "[1/2]"
        idle = build_state_suffixes(
            current_state="idle",
            last_durations=_last_durations(settings),
            task_last_durations=None,
            elapsed_sec=3,
            exec_progress=(1, 2),
            idle_remaining=105,
        )
        assert "exec" not in idle

    def test_idle_countdown_only_when_idle(self) -> None:
        settings = _settings()
        idle = build_state_suffixes(
            current_state="idle",
            last_durations=_last_durations(settings),
            task_last_durations=None,
            elapsed_sec=15,
            exec_progress=None,
            idle_remaining=105,
        )
        assert idle["idle"].plain == "[01:45]"
        running = build_state_suffixes(
            current_state="before-exec",
            last_durations=_last_durations(settings),
            task_last_durations=None,
            elapsed_sec=15,
            exec_progress=None,
            idle_remaining=None,
        )
        assert "idle" not in running

    def test_hour_durations_use_full_format(self) -> None:
        settings = _settings(init=3721)
        suffixes = build_state_suffixes(
            current_state="initialization",
            last_durations=_last_durations(settings),
            task_last_durations=None,
            elapsed_sec=3721,
            exec_progress=None,
            idle_remaining=None,
        )
        assert suffixes["initialization"].plain == "[01:02:01][01:02:01]"

    def test_positional_args_allowed(self) -> None:
        settings = _settings(before=93)
        suffixes = build_state_suffixes(
            "before-exec",
            _last_durations(settings),
            None,
            31,
            None,
            None,
        )
        assert suffixes["before-exec"].plain == "[01:33][31]"

    def test_span_styles_keep_theme_vars(self) -> None:
        """Content spans resolve $vars at render; they must not be pre-resolved."""
        settings = _settings(init=1)
        suffixes = build_state_suffixes(
            current_state="initialization",
            last_durations=_last_durations(settings),
            task_last_durations={"before-task": 2, "task-exec": 3, "after-task": 4},
            elapsed_sec=5,
            exec_progress=(1, 2),
            idle_remaining=None,
        )
        assert _span_styles(suffixes["initialization"]) == [
            "$foreground-disabled",
            "bold $text-success",
        ]
        assert _span_styles(suffixes["before-task"]) == ["$foreground-disabled"]
        progress = build_state_suffixes(
            current_state="task-exec",
            last_durations=_last_durations(settings),
            task_last_durations={"before-task": 2, "task-exec": 3, "after-task": 4},
            elapsed_sec=5,
            exec_progress=(1, 2),
            idle_remaining=None,
        )
        assert _span_styles(progress["exec"]) == ["$text-success"]


class TestSessionDurations:
    def test_picks_attrs(self) -> None:
        settings = RunnerSettings()
        settings.session.last_run_before_duration = 5
        durations = _session_durations(
            settings.session, {"before-exec": "last_run_before_duration"}
        )
        assert durations == {"before-exec": 5}

    def test_missing_is_none(self) -> None:
        settings = RunnerSettings()
        durations = _session_durations(
            settings.session, {"before-exec": "last_run_before_duration"}
        )
        assert durations == {"before-exec": None}
