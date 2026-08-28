"""A set of widgets designed to be used as ``MenuScreen`` descriptions."""

from __future__ import annotations

from dataclasses import dataclass

from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Rule, Static


@dataclass
class KeyValueEntry:
    """A single key/value row for ``KeyValueWidget``."""

    key: str
    value: str


@dataclass
class StateEntry:
    """A lifecycle state entry.

    ``children`` lists substate ids, when one is active the entry is
    highlighted (bold + color) without the active marker.
    """

    id: str
    label: str
    color: str | None = None
    children: tuple[str, ...] = ()


class KeyValueWidget(Widget):
    """Key/value widget: rows rendered as a centered, auto-sized two-column Rich ``Table``.

    The key column is bold ``$text-primary``. A cell wraps only when the
    table does not fit. ``key_value_entries`` is a reactive.
    """

    DEFAULT_CSS = """\
    KeyValueWidget {
        width: 1fr;
        height: auto;

        #key-value-table {
            width: 1fr;
            height: auto;
            content-align-horizontal: center;
        }
    }
    """

    key_value_entries: reactive[tuple[KeyValueEntry, ...]] = reactive((), init=False)

    def __init__(
        self,
        *,
        key_value_entries: tuple[KeyValueEntry, ...] = (),
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self.key_value_entries = key_value_entries

    def _build_table(self) -> Table:
        """Build a borderless, auto-sized two-column table from key_value_entries."""
        table = Table(box=None, show_header=False, padding=(0, 1), expand=False)
        color = self.app.get_css_variables().get("text-primary")
        key_style = f"bold {color}" if color is not None else None
        table.add_column("key", justify="right", no_wrap=True, style=key_style)
        table.add_column("value", justify="left")
        for row in self.key_value_entries:
            table.add_row(row.key, row.value)
        return table

    def compose(self) -> ComposeResult:
        yield Static(self._build_table(), id="key-value-table")

    def on_mount(self) -> None:
        # Rebuild once mounted so the key column picks up the theme color.
        self.query_one("#key-value-table", Static).update(self._build_table())

    def watch_key_value_entries(self, rows: tuple[KeyValueEntry, ...]) -> None:
        """Rebuild the table when key_value_entries changes."""
        if not self.is_mounted:
            return
        self.query_one("#key-value-table", Static).update(self._build_table())


class StateWidget(Widget):
    """Description widget for ``MenuScreen``: a ``KeyValueWidget`` plus a lifecycle state list.

    ``key_value_entries`` and ``current_state`` are reactives whose watchers
    update child widgets in place.
    """

    _DEFAULT_ACTIVE_COLOR = "$success"
    _ACTIVE_MARKER = "▶ "
    _INACTIVE_MARKER = "  "

    DEFAULT_CSS = """\
    StateWidget {
        width: 1fr;
        height: auto;

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

    key_value_entries: reactive[tuple[KeyValueEntry, ...]] = reactive((), init=False)
    current_state: reactive[str | None] = reactive(None, init=False)

    def __init__(
        self,
        *,
        key_value_entries: tuple[KeyValueEntry, ...] = (),
        current_state: str | None = None,
        states_entries: tuple[StateEntry, ...] = (),
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self._states_entries = states_entries
        self.key_value_entries = key_value_entries
        self.current_state = current_state

    @staticmethod
    def _render_state_cell(
        entry: StateEntry,
        is_active: bool,
        is_parent_highlight: bool = False,
    ) -> Text:
        """Render a single state row.

        - exact active state: ▶ marker + bold + color
        - parent of the active state: bold + color, no marker
        - otherwise: plain text
        """
        color = entry.color or StateWidget._DEFAULT_ACTIVE_COLOR
        if is_active:
            return Text(
                f"{StateWidget._ACTIVE_MARKER}{entry.label}", style=f"bold {color}"
            )
        if is_parent_highlight:
            return Text(
                f"{StateWidget._INACTIVE_MARKER}{entry.label}", style=f"bold {color}"
            )
        return Text(f"{StateWidget._INACTIVE_MARKER}{entry.label}")

    def compose(self) -> ComposeResult:
        yield KeyValueWidget(key_value_entries=self.key_value_entries)

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
                        self._render_state_cell(
                            entry,
                            entry.id == state,
                            is_parent_highlight=bool(state) and state in entry.children,
                        ),
                        classes="state-row",
                    )

    def watch_current_state(self, state: str | None) -> None:
        """Re-render every state row when the session state changes."""
        if not self.is_mounted:
            return
        state_rows = self.query(".state-row")
        for idx, entry in enumerate(self._states_entries):
            if idx < len(state_rows):
                row = state_rows[idx]
                assert isinstance(row, Static)
                row.update(
                    self._render_state_cell(
                        entry,
                        entry.id == state,
                        is_parent_highlight=bool(state) and state in entry.children,
                    )
                )

    def watch_key_value_entries(self, rows: tuple[KeyValueEntry, ...]) -> None:
        """Forward key/value entry updates to the embedded KeyValueWidget."""
        try:
            info = self.query_one(KeyValueWidget)
        except NoMatches:
            return
        info.key_value_entries = rows
