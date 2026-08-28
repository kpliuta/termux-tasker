from __future__ import annotations

import pytest
from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from termux_tasker.ui.screens.widgets.description import (
    KeyValueEntry,
    KeyValueWidget,
    StateEntry,
    StateWidget,
)


class TestKeyValueEntry:
    def test_fields(self) -> None:
        row = KeyValueEntry(key="Version", value="1.0.0")
        assert row.key == "Version"
        assert row.value == "1.0.0"


class TestStateEntry:
    def test_defaults(self) -> None:
        e = StateEntry(id="idle", label="idle")
        assert e.color is None
        assert e.children == ()

    def test_with_color(self) -> None:
        e = StateEntry(id="off", label="off", color="red")
        assert e.color == "red"

    def test_with_children(self) -> None:
        e = StateEntry(id="exec", label="exec", children=("task-exec",))
        assert e.children == ("task-exec",)


class _MountApp(App):
    """Minimal app that mounts a single widget for testing."""

    def __init__(self, widget: Widget) -> None:
        super().__init__()
        self._widget = widget

    def compose(self) -> ComposeResult:
        yield self._widget


class TestKeyValueWidget:
    @pytest.mark.asyncio
    async def test_renders_info_table(self) -> None:
        widget = KeyValueWidget(
            key_value_entries=(
                KeyValueEntry("App Version", "1.2.3"),
                KeyValueEntry("Session ID", "abc"),
            )
        )
        async with _MountApp(widget).run_test() as pilot:
            table = pilot.app.screen.query_one("#key-value-table", Static)
            content = _table_text(table.render())
            assert "App Version" in content
            assert "Session ID" in content
            assert "1.2.3" in content
            assert "abc" in content
            # Both rows share a single aligned table, not separate groups.
            assert len(pilot.app.screen.query("#key-value-table")) == 1

    @pytest.mark.asyncio
    async def test_watch_key_value_entries_updates_in_place(self) -> None:
        widget = KeyValueWidget(
            key_value_entries=(KeyValueEntry("App Version", "1.0.0"),)
        )
        async with _MountApp(widget).run_test() as pilot:
            table_before = widget.query_one("#key-value-table", Static)
            widget.key_value_entries = (KeyValueEntry("App Version", "2.0.0"),)
            await pilot.pause()
            table_after = widget.query_one("#key-value-table", Static)
            assert table_after is table_before
            assert "2.0.0" in _table_text(table_after.render())


def _table_text(rendered: object) -> str:
    """Extract text from a Static's rendered Table (wrapped in RichVisual)."""
    from rich.console import Console

    renderable = getattr(rendered, "_renderable", rendered)
    console = Console(width=80, legacy_windows=False)
    with console.capture() as capture:
        console.print(renderable)
    return capture.get()


class TestStateWidget:
    @pytest.mark.asyncio
    async def test_renders_hr_without_state_rows(self) -> None:
        widget = StateWidget(
            key_value_entries=(KeyValueEntry("App Version", "1.2.3"),),
        )
        async with _MountApp(widget).run_test() as pilot:
            assert len(pilot.app.screen.query("#key-value-table")) == 1
            assert len(pilot.app.screen.query(".hr")) == 1
            assert len(pilot.app.screen.query(".state-row")) == 0

    @pytest.mark.asyncio
    async def test_renders_hr_and_state_when_states_present(self) -> None:
        widget = StateWidget(
            key_value_entries=(KeyValueEntry("Version", "1.2.3"),),
            current_state="running",
            states_entries=(
                StateEntry("stopped", "stopped", color="$text-error"),
                StateEntry("running", "running"),
            ),
        )
        async with _MountApp(widget).run_test() as pilot:
            assert len(pilot.app.screen.query(".hr")) == 1
            state_rows = pilot.app.screen.query(".state-row")
            assert len(state_rows) == 2
            # The active state is rendered with the active marker.
            assert any(
                str(r.render()).startswith(StateWidget._ACTIVE_MARKER)
                for r in state_rows
            )

    @pytest.mark.asyncio
    async def test_current_state_ignored_without_states(self) -> None:
        widget = StateWidget(
            key_value_entries=(KeyValueEntry("Version", "1.2.3"),),
            current_state="running",
        )
        async with _MountApp(widget).run_test() as pilot:
            # With no states_entries the current_state must not produce
            # any state rows; the rule is still rendered.
            assert len(pilot.app.screen.query(".state-row")) == 0
            assert len(pilot.app.screen.query(".hr")) == 1

    @pytest.mark.asyncio
    async def test_watch_current_state_updates_rows(self) -> None:
        widget = StateWidget(
            key_value_entries=(KeyValueEntry("Version", "1.2.3"),),
            current_state="stopped",
            states_entries=(
                StateEntry("stopped", "stopped", color="$text-error"),
                StateEntry("running", "running"),
            ),
        )
        async with _MountApp(widget).run_test() as pilot:
            widget.current_state = "running"
            await pilot.pause()
            state_rows = pilot.app.screen.query(".state-row")
            marked = [
                r
                for r in state_rows
                if str(r.render()).startswith(StateWidget._ACTIVE_MARKER)
            ]
            assert len(marked) == 1
            assert "running" in str(marked[0].render())
