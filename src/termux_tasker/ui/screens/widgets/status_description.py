from __future__ import annotations

from dataclasses import dataclass

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.reactive import reactive
from textual.widgets import Rule, Static
from textual.widget import Widget


@dataclass
class InfoRow:
    """A key/value row for the top section of the widget."""

    key: str
    value: str


@dataclass
class StateEntry:
    """One entry in the state section list.

    ``children`` lists the ids of sub-states that belong to this entry. When
    one of those children is the active state, this entry is rendered as
    highlighted (bold + color) without the active marker.
    """

    id: str
    label: str
    color: str | None = None
    children: tuple[str, ...] = ()


DEFAULT_ACTIVE_COLOR = "$success"

ACTIVE_MARKER = "▶ "
INACTIVE_MARKER = "  "


def render_state_cell(
    entry: StateEntry,
    is_active: bool,
    is_parent_highlight: bool = False,
) -> Text:
    """Render a single state row.

    - exact active state: ▶ marker + bold + color
    - parent of the active state: bold + color, no marker
    - otherwise: plain text
    """
    color = entry.color or DEFAULT_ACTIVE_COLOR
    if is_active:
        return Text(f"{ACTIVE_MARKER}{entry.label}", style=f"bold {color}")
    if is_parent_highlight:
        return Text(f"{INACTIVE_MARKER}{entry.label}", style=f"bold {color}")
    return Text(f"{INACTIVE_MARKER}{entry.label}")


class StatusWidget(Widget):
    """Reusable status widget: info rows + live-cycling state list.

    ``info_rows`` and ``current_state`` are Textual reactives — the
    watchers update child Static widgets in-place so the DOM stays
    stable and focus is preserved.
    """

    DEFAULT_CSS = """\
    StatusWidget {
        width: 1fr;
        height: auto;

        .info-row {
            height: auto;
        }
        .info-key {
            width: 1fr;
            padding: 0 1;
            content-align-horizontal: right;
            text-style: bold;
            color: $text-primary;
        }
        .info-value {
            width: 1fr;
            padding: 0 1;
        }
        .hr {
            color: $primary;
        }
        .state {
            width: 1fr;
            align-horizontal: center;
        }
        .state-rows {
            width: auto;
        }
        .state-row {
            width: auto;
        }
    }
    """

    info_rows: reactive[tuple[InfoRow, ...]] = reactive((), init=False)
    current_state: reactive[str | None] = reactive(None, init=False)

    def __init__(
        self,
        *,
        info_rows: tuple[InfoRow, ...] = (),
        current_state: str | None = None,
        states_entries: tuple[StateEntry, ...] = (),
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self._states_entries = states_entries
        self.info_rows = info_rows
        self.current_state = current_state

    def compose(self) -> ComposeResult:
        # Top section: key/value info rows
        for row in self.info_rows:
            with HorizontalGroup(classes="info-row"):
                yield Static(row.key, classes="info-key")
                yield Static(row.value, classes="info-value")

        # Horizontal rule
        rule = Rule(classes="hr")
        rule.styles.margin = (0, 0)
        yield rule

        # State section: centered lifecycle list
        with VerticalGroup(classes="state"):
            with VerticalGroup(classes="state-rows"):
                state = self.current_state
                for entry in self._states_entries:
                    yield Static(
                        render_state_cell(
                            entry,
                            entry.id == state,
                            is_parent_highlight=bool(state)
                            and state in entry.children,
                        ),
                        classes="state-row",
                    )

    def watch_current_state(self, state: str | None) -> None:
        """Re-render every state row when the session state changes."""
        state_rows = self.query(".state-row")
        for idx, entry in enumerate(self._states_entries):
            if idx < len(state_rows):
                row = state_rows[idx]
                assert isinstance(row, Static)
                row.update(
                    render_state_cell(
                        entry,
                        entry.id == state,
                        is_parent_highlight=bool(state)
                        and state in entry.children,
                    )
                )

    def watch_info_rows(self, rows: tuple[InfoRow, ...]) -> None:
        """Rebuild the info section when info_rows changes."""
        info_groups = self.query(".info-row")
        # Update existing rows or create new ones as needed
        for i, group in enumerate(info_groups):
            if i < len(rows):
                key_el, value_el = list(group.query(Static))
                key_el.update(rows[i].key)
                value_el.update(rows[i].value)
                group.display = True
            else:
                group.display = False
