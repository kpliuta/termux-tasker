from __future__ import annotations

import pytest
from textual.app import App, ComposeResult
from textual.content import Content
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
                if str(r.render()).startswith(StateWidget._ACTIVE_MARKER)   # noqa
            ]
            assert len(marked) == 1
            assert "running" in str(marked[0].render()) # noqa

    @pytest.mark.asyncio
    async def test_state_suffix_appended_to_row(self) -> None:
        widget = StateWidget(
            key_value_entries=(KeyValueEntry("Version", "1.2.3"),),
            current_state="before-exec",
            states_entries=(
                StateEntry("before-exec", "before-exec"),
                StateEntry("after-exec", "after-exec"),
            ),
            state_suffixes={
                "before-exec": Content.assemble(("[01:33][31]", "$foreground-disabled")),
                "after-exec": Content.assemble(("[n/a]", "$foreground-disabled")),
            },
        )
        async with _MountApp(widget).run_test() as pilot:
            await pilot.pause()
            rows = [str(r.render()) for r in pilot.app.screen.query(".state-row")]  # noqa
            assert any("before-exec [01:33][31]" in row for row in rows)
            assert any("after-exec [n/a]" in row for row in rows)

    @pytest.mark.asyncio
    async def test_watch_state_suffixes_updates_rows_in_place(self) -> None:
        widget = StateWidget(
            key_value_entries=(KeyValueEntry("Version", "1.2.3"),),
            current_state="idle",
            states_entries=(StateEntry("idle", "idle", color="$text-warning"),),
        )
        async with _MountApp(widget).run_test() as pilot:
            rows_before = list(pilot.app.screen.query(".state-row"))
            widget.state_suffixes = {
                "idle": Content.assemble(("[01:45]", "bold $text-warning"))
            }
            await pilot.pause()
            rows_after = list(pilot.app.screen.query(".state-row"))
            assert [r.id for r in rows_after] == [r.id for r in rows_before]
            assert any("[01:45]" in str(r.render()) for r in rows_after)    # noqa


class TestRenderStateCell:
    def test_active_cell_is_content_with_theme_var(self) -> None:
        cell = StateWidget._render_state_cell(
            StateEntry("idle", "idle", color="$text-warning"), is_active=True
        )
        assert isinstance(cell, Content)
        assert cell.plain == "▶ idle"
        assert ("▶ idle", "bold $text-warning") in [
            (cell.plain[span.start : span.end], span.style) for span in cell.spans
        ]

    def test_suffix_brackets_stay_literal(self) -> None:
        cell = StateWidget._render_state_cell(
            StateEntry("task-exec", "├─ task-exec"),
            is_active=True,
            suffix=Content.assemble(("[2]", "$foreground-disabled")),
        )
        assert isinstance(cell, Content)
        assert cell.plain == "▶ ├─ task-exec [2]"


class TestMountedRenderSmoke:
    """Guard: every Static in a mounted description renders under the app console."""

    @pytest.mark.asyncio
    async def test_state_widget_with_suffixes_renders(self) -> None:
        widget = StateWidget(
            key_value_entries=(
                KeyValueEntry("Version", "1.1.0"),
                KeyValueEntry("Enabled", "True"),
                KeyValueEntry("PID", "n/a"),
                KeyValueEntry("RSS", "n/a"),
                KeyValueEntry("Last Run", "n/a"),
            ),
            current_state="idle",
            states_entries=(
                StateEntry("off", "off", color="$text-error"),
                StateEntry("initialization", "initialization"),
                StateEntry("idle", "idle", color="$text-warning"),
                StateEntry("termination", "termination", color="$text-error"),
            ),
            state_suffixes={
                "initialization": Content.assemble(("[1]", "$foreground-disabled")),
                "idle": Content.assemble(("[01:00]", "bold $text-warning")),
                "termination": Content.assemble(("[n/a]", "$foreground-disabled")),
            },
        )
        async with _MountApp(widget).run_test() as pilot:
            await pilot.pause()
            rendered = [str(item.render()) for item in widget.query(Static)]    # noqa
            assert any("idle" in line for line in rendered)
            assert any("[01:00]" in line for line in rendered)

    @pytest.mark.asyncio
    async def test_key_value_values_align_in_columns(self) -> None:
        widget = KeyValueWidget(
            key_value_entries=(
                KeyValueEntry("Version", "1.1.0"),
                KeyValueEntry("Session ID", "abc"),
            )
        )
        async with _MountApp(widget).run_test() as pilot:
            await pilot.pause()
            table = widget.query_one("#key-value-table", Static)
            lines = _table_text(table.render()).splitlines()
            value_lines = [line for line in lines if "1.1.0" in line or "abc" in line]
            assert len(value_lines) == 2
            assert value_lines[0].index("1.1.0") == value_lines[1].index("abc")


class TestThemeVarContent:
    """Characterization: Content with $var spans renders under the app theme.

    This is the mechanism the suffix refactor relies on (Rich Text spans
    with $vars raise MissingStyle; Content spans resolve via the widget theme).
    """

    @pytest.mark.asyncio
    async def test_content_with_theme_var_spans_renders(self) -> None:
        from textual.content import Content

        content = Content.assemble(
            ("  idle", ""),
            (" ", ""),
            ("[01:00]", "$text-warning"),
            ("[27]", "bold $text-success"),
            ("[1/2]", "$foreground-disabled"),
        )
        assert "[01:00]" in content.plain
        assert "[1/2]" in content.plain
        widget = Static(content, id="theme-var-probe")
        async with _MountApp(widget).run_test() as pilot:
            await pilot.pause()
            probe = pilot.app.screen.query_one("#theme-var-probe", Static)
            assert "[01:00]" in str(probe.render()) # noqa
            assert "[1/2]" in str(probe.render())   # noqa
