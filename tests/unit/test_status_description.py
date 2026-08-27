from __future__ import annotations

from rich.text import Text

from termux_tasker.ui.screens.widgets.status_description import (
    ACTIVE_MARKER,
    DEFAULT_ACTIVE_COLOR,
    INACTIVE_MARKER,
    InfoRow,
    StateEntry,
    render_state_cell,
)


class TestInfoRow:
    def test_fields(self) -> None:
        row = InfoRow(key="Version", value="1.0.0")
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


class TestRenderStateCell:
    def test_inactive_returns_plain(self) -> None:
        e = StateEntry(id="idle", label="idle")
        result = render_state_cell(e, is_active=False)
        assert isinstance(result, Text)
        plain = result.plain
        assert plain.startswith(INACTIVE_MARKER)
        assert "idle" in plain

    def test_active_default_green_bold(self) -> None:
        e = StateEntry(id="idle", label="idle")
        result = render_state_cell(e, is_active=True)
        plain = result.plain
        assert plain.startswith(ACTIVE_MARKER)
        assert "idle" in plain
        assert "bold" in str(result.style)
        assert DEFAULT_ACTIVE_COLOR in str(result.style)

    def test_active_with_explicit_color(self) -> None:
        e = StateEntry(id="off", label="off", color="red")
        result = render_state_cell(e, is_active=True)
        assert "bold" in str(result.style)
        assert "red" in str(result.style)

    def test_active_yellow_for_idle(self) -> None:
        e = StateEntry(id="idle", label="idle", color="yellow")
        result = render_state_cell(e, is_active=True)
        assert "bold" in str(result.style)
        assert "yellow" in str(result.style)

    def test_parent_highlight_bold_color_no_marker(self) -> None:
        e = StateEntry(id="exec", label="exec", children=("task-exec",))
        result = render_state_cell(e, is_active=False, is_parent_highlight=True)
        plain = result.plain
        assert plain.startswith(INACTIVE_MARKER)
        assert "exec" in plain
        assert ACTIVE_MARKER not in plain
        assert "bold" in str(result.style)
        assert DEFAULT_ACTIVE_COLOR in str(result.style)

    def test_parent_highlight_overrides_plain(self) -> None:
        e = StateEntry(
            id="exec", label="exec", color="red", children=("task-exec",)
        )
        result = render_state_cell(e, is_active=False, is_parent_highlight=True)
        assert "bold" in str(result.style)
        assert "red" in str(result.style)

    def test_active_takes_precedence_over_parent(self) -> None:
        e = StateEntry(id="task-exec", label="task-exec", children=("exec",))
        result = render_state_cell(e, is_active=True, is_parent_highlight=True)
        assert result.plain.startswith(ACTIVE_MARKER)
        assert "bold" in str(result.style)

    def test_inactive_no_bold(self) -> None:
        e = StateEntry(id="idle", label="idle")
        result = render_state_cell(e, is_active=False)
        assert result.style is None or "bold" not in str(result.style)

