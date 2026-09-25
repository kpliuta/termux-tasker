from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from rich.text import Text
from textual.app import App, ComposeResult
from textual.content import Content
from textual.css.scalar import Unit
from textual.widgets import Rule, Static

from termux_tasker.config import RunnerSettings, TaskSettings
from termux_tasker.proc_stats import TreeStats
from termux_tasker.ui.base import ButtonLayout
from termux_tasker.ui.screens.dashboard import (
    _DashboardDescription,  # noqa
    _make_bar,              # noqa
    _make_bars,             # noqa
    _make_pid_line,         # noqa
    _opaque_hex,            # noqa
    DashboardScreen,
)


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

EMPTY_HEX = "#555555"


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
    app.state.runners = {}
    return app


def _bar_cells(text: Text) -> list[tuple[str, str | None]]:
    """Map every ■ char in a bar Text to its style."""
    cells: list[tuple[str, str | None]] = []
    for span in text.spans:
        for offset in range(span.start, span.end):
            char = text.plain[offset]
            if char == "■":
                style = span.style if isinstance(span.style, str) else str(span.style)
                cells.append((char, style))
    return cells


class TestDashboardInit:
    def test_column_count(self) -> None:
        screen = DashboardScreen()
        assert screen._column_count == 3

    def test_description_widget(self) -> None:
        screen = DashboardScreen()
        assert screen.description is None
        assert isinstance(screen._description_widget, _DashboardDescription)

    def test_description_max_height(self) -> None:
        screen = DashboardScreen()
        assert screen._description_max_height == "100%"

    def test_title(self) -> None:
        screen = DashboardScreen()
        assert screen.title == "Dashboard"

    def test_description_min_height(self) -> None:
        screen = DashboardScreen()
        assert screen._description_min_height == "100%"

    def test_menu_items_bottom_layout(self) -> None:
        screen = DashboardScreen()
        assert [item.id for item in screen.menu_items] == ["help", "settings", "runners"]
        for item in screen.menu_items:
            assert item.layout == ButtonLayout.BOTTOM

    def test_help_button_label(self) -> None:
        screen = DashboardScreen()
        help_item = next(item for item in screen.menu_items if item.id == "help")
        assert help_item.label == "❓"

    def test_settings_button_label(self) -> None:
        screen = DashboardScreen()
        settings_item = next(item for item in screen.menu_items if item.id == "settings")
        assert settings_item.label == "🔧"
        assert settings_item.title == ""


class TestOpaqueHex:
    def test_opaque_passthrough(self) -> None:
        assert _opaque_hex("#8AD4A1", (0, 0, 0), "#000000") == "#8ad4a1"

    def test_translucent_blends_over_background(self) -> None:
        assert _opaque_hex("#E0E0E060", (0x1E, 0x1E, 0x1E), "#000000") == "#676767"

    def test_translucent_stays_dimmer_than_default_text(self) -> None:
        blended = _opaque_hex("#E0E0E060", (0x1E, 0x1E, 0x1E), "#000000")
        assert blended != "#e0e0e0"

    def test_garbage_falls_back(self) -> None:
        assert _opaque_hex("not-a-color", (0, 0, 0), "#6b7280") == "#6b7280"
        assert _opaque_hex("#12345", (0, 0, 0), "#6b7280") == "#6b7280"


class TestMakeBars:
    def test_cpu_and_mem_labels(self) -> None:
        bars = _make_bars(11.0, 1024, 2048, 40, EMPTY_HEX)
        assert "CPU" in bars.plain
        assert "MEM" in bars.plain
        assert "11%" in bars.plain

    def test_bar_width_adapts_to_screen(self) -> None:
        narrow = _make_bars(50.0, 1024, 2048, 40, EMPTY_HEX)
        wide = _make_bars(50.0, 1024, 2048, 80, EMPTY_HEX)
        assert wide.plain.count("■") > narrow.plain.count("■")

    def test_cpu_unknown_renders_empty_bar(self) -> None:
        bars = _make_bars(None, 1024, 2048, 40, EMPTY_HEX)
        assert "n/a" in bars.plain
        cpu_line = bars.plain.split("\n")[0]
        assert "■" in cpu_line

    def test_mem_unknown_renders_na(self) -> None:
        bars = _make_bars(11.0, None, None, 40, EMPTY_HEX)
        assert "n/a" in bars.plain.split("\n")[1]

    def test_mem_units_adapt(self) -> None:
        used = int(13.2 * 1024**2)
        total = int(31.3 * 1024**3)
        bars = _make_bars(11.0, used, total, 60, EMPTY_HEX)
        assert "13.2 MiB/31.3 GiB" in bars.plain

    def test_mem_shared_unit_collapses(self) -> None:
        used = int(18.6 * 1024**3)
        total = int(31.3 * 1024**3)
        bars = _make_bars(11.0, used, total, 60, EMPTY_HEX)
        assert "18.6/31.3 GiB" in bars.plain

    def test_bar_lines_never_exceed_width(self) -> None:
        for width in (20, 40, 80):
            bars = _make_bars(11.0, int(18.6 * 1024**3), int(31.3 * 1024**3), width, EMPTY_HEX)
            for line in bars.plain.split("\n"):
                assert len(line) <= width
                assert line.startswith(" ")

    def test_filled_cells_carry_gradient_not_gray(self) -> None:
        bar = _make_bar("CPU", 0.5, 40, "#7f1d1d", "#ff4545", "50%", EMPTY_HEX)
        cells = _bar_cells(bar)
        filled_styles = {style for _, style in cells if style != EMPTY_HEX}
        assert len(cells) > 0
        assert len(filled_styles) > 1

    def test_empty_fraction_has_no_gradient(self) -> None:
        bar = _make_bar("CPU", None, 40, "#7f1d1d", "#ff4545", "n/a", EMPTY_HEX)
        cells = _bar_cells(bar)
        assert len(cells) > 0
        assert {style for _, style in cells} == {EMPTY_HEX}


class TestMakePidLine:
    def test_hidden_when_no_roots(self) -> None:
        tree = TreeStats(pids=(), num_procs=0, rss_total=0)
        assert _make_pid_line([], tree) is None

    def test_hidden_when_tree_empty(self) -> None:
        tree = TreeStats(pids=(), num_procs=0, rss_total=0)
        assert _make_pid_line([4242], tree) is None

    def test_shows_pid_plus_children_and_rss(self) -> None:
        tree = TreeStats(pids=(4242, 4243), num_procs=2, rss_total=30 * 1024 * 1024)
        line = _make_pid_line([4242], tree)
        assert line is not None
        assert line.plain == "   │  PID 4242+1 RSS 30.0 MiB"

    def test_single_proc_omits_plus(self) -> None:
        tree = TreeStats(pids=(4242,), num_procs=1, rss_total=10 * 1024 * 1024)
        line = _make_pid_line([4242], tree)
        assert line is not None
        assert "PID 4242 RSS 10.0 MiB" in line.plain
        assert "+" not in line.plain

    def test_pid_uses_theme_warning_var(self) -> None:
        tree = TreeStats(pids=(4242, 4243), num_procs=2, rss_total=30 * 1024 * 1024)
        line = _make_pid_line([4242], tree)
        assert line is not None
        pid_offset = line.plain.index("PID")
        assert any(
            span.start <= pid_offset < span.end and span.style == "$text-warning"
            for span in line.spans
        )

    def test_recycled_root_falls_back_to_tree_pid(self) -> None:
        tree = TreeStats(pids=(9999,), num_procs=1, rss_total=1024)
        line = _make_pid_line([4242], tree)
        assert line is not None
        assert "PID 9999" in line.plain


class TestDashboardRunnerLines:
    def test_no_runners(self, tmp_path: Path) -> None:
        screen = DashboardScreen()
        runners_path = tmp_path / "runners"
        runners_path.mkdir()
        result = screen._build_runner_lines(runners_path)
        assert "No runners installed" in result.plain

    def test_runners_path_not_exists(self, tmp_path: Path) -> None:
        screen = DashboardScreen()
        runners_path = tmp_path / "nonexistent"
        result = screen._build_runner_lines(runners_path)
        assert "No runners installed" in result.plain

    def test_one_runner_no_tasks(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        _write_runner(runners_path / "sh_runner", SH_RUNNER_METADATA, enabled=False, state="off")

        screen = DashboardScreen()
        result = screen._build_runner_lines(runners_path)
        assert "Simple sh runner" in result.plain
        assert "[off]" in result.plain

    def test_runner_with_tasks(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        runner_dir = runners_path / "sh_runner"
        _write_runner(runner_dir, SH_RUNNER_METADATA, enabled=True, state="idle")
        _write_task(runner_dir / "tasks" / "sh_task", SH_TASK_METADATA, enabled=True, state="running")

        screen = DashboardScreen()
        result = screen._build_runner_lines(runners_path)
        assert "Simple sh runner" in result.plain
        assert "[idle]" in result.plain
        assert "Simple task" in result.plain
        assert "[running]" in result.plain

    def test_tree_prefix_last_task(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        runner_dir = runners_path / "sh_runner"
        _write_runner(runner_dir, SH_RUNNER_METADATA, enabled=True, state="idle")

        task1_meta = SH_TASK_METADATA.replace('"sh_task"', '"task_a"').replace('"Simple task"', '"Task A"')
        task2_meta = SH_TASK_METADATA.replace('"sh_task"', '"task_b"').replace('"Simple task"', '"Task B"')
        _write_task(runner_dir / "tasks" / "task_a", task1_meta, enabled=True, state="running")
        _write_task(runner_dir / "tasks" / "task_b", task2_meta, enabled=False, state="stopped")

        screen = DashboardScreen()
        result = screen._build_runner_lines(runners_path)
        lines = result.plain.split("\n")
        task_lines = [line for line in lines if "Task" in line and ("running" in line or "stopped" in line or "disabled" in line)]
        assert len(task_lines) == 2
        assert "├─" in task_lines[0]
        assert "└─" in task_lines[1]

    def test_disabled_runner_shows_red_emoji(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        _write_runner(runners_path / "sh_runner", SH_RUNNER_METADATA, enabled=False, state="off")

        screen = DashboardScreen()
        result = screen._build_runner_lines(runners_path)
        assert "\U0001f534" in result.plain

    def test_idle_runner_shows_yellow_emoji(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        _write_runner(runners_path / "sh_runner", SH_RUNNER_METADATA, enabled=True, state="idle")

        screen = DashboardScreen()
        result = screen._build_runner_lines(runners_path)
        assert "\U0001f7e1" in result.plain

    def test_working_runner_shows_green_emoji(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        _write_runner(runners_path / "sh_runner", SH_RUNNER_METADATA, enabled=True, state="task-exec")

        screen = DashboardScreen()
        result = screen._build_runner_lines(runners_path)
        assert "\U0001f7e2" in result.plain

    def test_multiple_runners_sorted(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        meta_b = SH_RUNNER_METADATA.replace('"sh_runner"', '"b_runner"').replace('"Simple sh runner"', '"B Runner"')
        meta_a = SH_RUNNER_METADATA.replace('"sh_runner"', '"a_runner"').replace('"Simple sh runner"', '"A Runner"')
        _write_runner(runners_path / "b_runner", meta_b, enabled=True, state="idle")
        _write_runner(runners_path / "a_runner", meta_a, enabled=True, state="idle")

        screen = DashboardScreen()
        result = screen._build_runner_lines(runners_path)
        lines = result.plain.split("\n")
        runner_lines = [line for line in lines if "Runner" in line and "[idle]" in line]
        assert len(runner_lines) == 2
        assert "A Runner" in runner_lines[0]
        assert "B Runner" in runner_lines[1]

    def test_stopped_runner_hides_pid_line(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        _write_runner(runners_path / "sh_runner", SH_RUNNER_METADATA, enabled=False, state="off")

        screen = DashboardScreen()
        result = screen._build_runner_lines(runners_path, {}, {})
        assert "PID" not in result.plain

    def test_list_lines_have_left_pad(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        runner_dir = runners_path / "sh_runner"
        _write_runner(runner_dir, SH_RUNNER_METADATA, enabled=True, state="task-exec")
        _write_task(runner_dir / "tasks" / "sh_task", SH_TASK_METADATA, enabled=True, state="running")
        tree = TreeStats(pids=(4242,), num_procs=1, rss_total=10 * 1024 * 1024)

        screen = DashboardScreen()
        result = screen._build_runner_lines(runners_path, {"sh_runner": [4242]}, {"sh_runner": tree})
        lines = result.plain.split("\n")
        assert len(lines) == 3
        for line in lines:
            assert line.startswith(" ")

    def test_live_runner_shows_pid_line(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        _write_runner(runners_path / "sh_runner", SH_RUNNER_METADATA, enabled=True, state="task-exec")
        tree = TreeStats(pids=(4242, 4243), num_procs=2, rss_total=30 * 1024 * 1024)

        screen = DashboardScreen()
        result = screen._build_runner_lines(runners_path, {"sh_runner": [4242]}, {"sh_runner": tree})
        assert "PID 4242+1 RSS 30.0 MiB" in result.plain

    def test_pid_line_aligns_with_task_tree(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        runner_dir = runners_path / "sh_runner"
        _write_runner(runner_dir, SH_RUNNER_METADATA, enabled=True, state="task-exec")
        _write_task(runner_dir / "tasks" / "sh_task", SH_TASK_METADATA, enabled=True, state="running")
        tree = TreeStats(pids=(4242, 4243), num_procs=2, rss_total=30 * 1024 * 1024)

        screen = DashboardScreen()
        result = screen._build_runner_lines(runners_path, {"sh_runner": [4242]}, {"sh_runner": tree})
        lines = result.plain.split("\n")
        pid_line = next(line for line in lines if "PID" in line)
        task_line = next(line for line in lines if "├─" in line or "└─" in line)
        pid_col = pid_line.index("│")
        tree_col = task_line.index("├") if "├" in task_line else task_line.index("└")
        assert pid_col == tree_col

    def test_live_pids_without_visible_tree_hide_pid_line(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        _write_runner(runners_path / "sh_runner", SH_RUNNER_METADATA, enabled=True, state="task-exec")

        screen = DashboardScreen()
        result = screen._build_runner_lines(runners_path, {"sh_runner": [4242]}, {})
        assert "PID" not in result.plain

    def test_idle_runner_with_live_proc_shows_countdown(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        _write_runner(runners_path / "sh_runner", SH_RUNNER_METADATA, enabled=True, state="idle")
        proc = MagicMock()
        proc.state_elapsed.return_value = 15

        screen = DashboardScreen()
        result = screen._build_runner_lines(runners_path, procs={"sh_runner": proc})
        assert "[idle][45]" in result.plain

    def test_idle_countdown_uses_compact_format(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        _write_runner(runners_path / "sh_runner", SH_RUNNER_METADATA, enabled=True, state="idle")
        proc = MagicMock()
        proc.state_elapsed.return_value = 0

        screen = DashboardScreen()
        result = screen._build_runner_lines(runners_path, procs={"sh_runner": proc})
        assert "[idle][01:00]" in result.plain

    def test_idle_countdown_clamps_at_zero(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        _write_runner(runners_path / "sh_runner", SH_RUNNER_METADATA, enabled=True, state="idle")
        proc = MagicMock()
        proc.state_elapsed.return_value = 999

        screen = DashboardScreen()
        result = screen._build_runner_lines(runners_path, procs={"sh_runner": proc})
        assert "[idle][0]" in result.plain

    def test_idle_runner_without_proc_hides_countdown(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        _write_runner(runners_path / "sh_runner", SH_RUNNER_METADATA, enabled=True, state="idle")

        screen = DashboardScreen()
        result = screen._build_runner_lines(runners_path)
        assert "[idle]" in result.plain
        assert "[idle][" not in result.plain

    def test_non_idle_runner_with_proc_hides_countdown(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        _write_runner(runners_path / "sh_runner", SH_RUNNER_METADATA, enabled=True, state="task-exec")
        proc = MagicMock()
        proc.state_elapsed.return_value = 15

        screen = DashboardScreen()
        result = screen._build_runner_lines(runners_path, procs={"sh_runner": proc})
        assert "[task-exec]" in result.plain
        assert "[task-exec][" not in result.plain


class TestDashboardDescriptionWidget:
    def test_pending_updates_apply_on_mount(self) -> None:
        widget = _DashboardDescription()
        widget.update_bars(Text("CPU bars"))
        widget.update_runners(Content("runner list"))
        assert widget._pending_bars is not None
        assert widget._pending_runners is not None

    @pytest.mark.asyncio
    async def test_runner_list_wraps_in_scroll_container(self) -> None:
        from textual.containers import VerticalScroll

        widget = _DashboardDescription()

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield widget

        async with TestApp().run_test(size=(80, 24)) as pilot:
            await pilot.pause(0.3)
            scroller = widget.query_one("#dash-list-scroll", VerticalScroll)
            assert widget.query_one("#dash-list", Static) is not None
            widget.update_runners(Content("\n".join(f"line {idx}" for idx in range(3))))
            await pilot.pause(0.3)
            assert scroller.max_scroll_y == 0

    @pytest.mark.asyncio
    async def test_runner_list_scrolls_on_overflow(self) -> None:
        from textual.containers import VerticalScroll

        widget = _DashboardDescription()

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield widget

        async with TestApp().run_test(size=(80, 24)) as pilot:
            await pilot.pause(0.3)
            widget.update_bars(Text("CPU line\nMEM line"))
            widget.update_runners(Content("\n".join(f"line {idx}" for idx in range(50))))
            await pilot.pause(0.3)
            scroller = widget.query_one("#dash-list-scroll", VerticalScroll)
            assert scroller.max_scroll_y > 0
            bars = widget.query_one("#dash-bars", Static)
            assert bars.outer_size.height == 2


class TestDashboardCompose:
    @pytest.mark.asyncio
    async def test_renders_description_widget(self, tmp_path: Path) -> None:
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
                widget = screen.query_one("#description-widget")
                assert isinstance(widget, _DashboardDescription)
                assert widget.query_one("#dash-bars", Static) is not None
                assert widget.query_one("#dash-list", Static) is not None

    @pytest.mark.asyncio
    async def test_rule_separates_bars_and_runners(self, tmp_path: Path) -> None:
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
                widget = screen.query_one("#description-widget")
                rules = widget.query(Rule)
                assert len(rules) == 1
                assert "hr" in rules[0].classes

    @pytest.mark.asyncio
    async def test_bars_show_live_resources(self, tmp_path: Path) -> None:
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
                bars = screen.query_one("#dash-bars", Static)
                rendered = bars.render()
                plain = rendered.plain if hasattr(rendered, "plain") else str(rendered)
                assert "CPU" in plain
                assert "MEM" in plain

    @pytest.mark.asyncio
    async def test_first_paint_bars_fit_layout(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        runners_path.mkdir()
        mock_app = _make_mock_app(runners_path)

        with patch("termux_tasker.ui.screens.dashboard.termux_app", return_value=mock_app):
            class TestApp(App):
                def on_mount(self) -> None:
                    self.push_screen(DashboardScreen())

            async with TestApp().run_test(size=(100, 40)) as pilot:
                screen = pilot.app.screen
                assert isinstance(screen, DashboardScreen)
                await pilot.pause(0.3)
                bars = screen.query_one("#dash-bars", Static)
                available = bars.content_size.width or bars.size.width
                assert available > 0
                rendered = bars.render()
                plain = rendered.plain if hasattr(rendered, "plain") else str(rendered)
                assert len(plain.split("\n")) == 2
                for line in plain.split("\n"):
                    assert len(line) <= available

    @pytest.mark.asyncio
    async def test_three_column_layout(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        runners_path.mkdir()
        mock_app = _make_mock_app(runners_path)

        with patch("termux_tasker.ui.screens.dashboard.termux_app", return_value=mock_app):
            class TestApp(App):
                def on_mount(self) -> None:
                    self.push_screen(DashboardScreen())

            async with TestApp().run_test() as pilot:
                from textual.containers import Horizontal
                bottom = pilot.app.screen.query_one("#bottom-container")
                rows = bottom.query(".button-row")
                assert len(rows) >= 1
                first_row = rows[0]
                assert isinstance(first_row, Horizontal)
                buttons_in_row = first_row.query("Button")
                assert len(buttons_in_row) == 3
                assert [btn.id for btn in buttons_in_row] == ["help", "settings", "runners"]

    @pytest.mark.asyncio
    async def test_action_buttons_in_bottom_bar(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        runners_path.mkdir()
        mock_app = _make_mock_app(runners_path)

        with patch("termux_tasker.ui.screens.dashboard.termux_app", return_value=mock_app):
            class TestApp(App):
                def on_mount(self) -> None:
                    self.push_screen(DashboardScreen())

            async with TestApp().run_test() as pilot:
                bottom = pilot.app.screen.query_one("#bottom-container")
                for button_id in ("#help", "#settings", "#runners"):
                    assert bottom.query_one(button_id) is not None

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

    @pytest.mark.asyncio
    async def test_description_fills_free_height(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        runners_path.mkdir()
        mock_app = _make_mock_app(runners_path)

        with patch("termux_tasker.ui.screens.dashboard.termux_app", return_value=mock_app):
            class TestApp(App):
                def on_mount(self) -> None:
                    self.push_screen(DashboardScreen())

            async with TestApp().run_test(size=(80, 24)) as pilot:
                await pilot.pause(0.3)
                screen = pilot.app.screen
                scroll = screen.query_one("#description-scroll")
                assert scroll.styles.min_height.value == 100
                assert scroll.styles.min_height.unit == Unit.HEIGHT
                widget = screen.query_one("#description-widget")
                assert f"{widget.styles.height}" == "1fr"
                top = screen.query_one("#top-container")
                assert top.outer_size.height - scroll.outer_size.height <= 2

    @pytest.mark.asyncio
    async def test_buttons_fit_narrow_screen(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        runners_path.mkdir()
        mock_app = _make_mock_app(runners_path)

        with patch("termux_tasker.ui.screens.dashboard.termux_app", return_value=mock_app):
            class TestApp(App):
                def on_mount(self) -> None:
                    self.push_screen(DashboardScreen())

            async with TestApp().run_test(size=(50, 14)) as pilot:
                await pilot.pause(0.3)
                screen = pilot.app.screen
                for button in screen.query("#bottom-container Button"):
                    assert button.region.right <= screen.size.width
                labels = [str(button.label).strip() for button in screen.query(".button-row Button")]
                assert labels == ["❓", "🔧", "Runners"]

    @pytest.mark.asyncio
    async def test_styles_do_not_leak_to_other_screens(self, tmp_path: Path) -> None:
        from termux_tasker.ui.screens.settings_screen import SettingsScreen

        runners_path = tmp_path / "runners"
        runners_path.mkdir()
        mock_app = _make_mock_app(runners_path)

        with patch("termux_tasker.ui.screens.dashboard.termux_app", return_value=mock_app):
            class TestApp(App):
                def on_mount(self) -> None:
                    self.push_screen(DashboardScreen())

            async with TestApp().run_test(size=(80, 24)) as pilot:
                await pilot.pause(0.3)
                pilot.app.push_screen(SettingsScreen("0.1.0", "test-session", True))
                await pilot.pause(0.3)
                settings = pilot.app.screen
                assert isinstance(settings, SettingsScreen)
                assert f"{settings.query_one('#description-scroll').styles.height}" == "auto"
