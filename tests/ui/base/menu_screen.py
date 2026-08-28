from __future__ import annotations

from pathlib import Path

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.containers import VerticalGroup, HorizontalGroup
from textual.widgets import Button, Static, DataTable, Rule

from termux_tasker.ui.base import (
    ButtonConfig,
    ButtonLayout,
    MenuScreen,
)

INFO_ROWS: tuple[tuple[str, str], ...] = (
    ("Version", "0.1.0"),
    ("Enabled", "False"),
)

STATES: tuple[str, ...] = (
    "off",
    "initialization",
    "before-exec",
    "exec",
    "├─ before-task",
    "├─ task-exec",
    "└─ after-task",
    "after-exec",
    "idle",
    "termination",
)

INITIAL_ACTIVE_INDEX = 5  # task-exec, as in the mockup
ACTIVE_MARKER = "▶ "
INACTIVE_MARKER = "  "
ACTIVE_STATE_COLORS: dict[str, str] = {
    "off": "$text-error",
    "idle": "$text-warning",
    "termination": "$text-error",
}
DEFAULT_ACTIVE_COLOR = "$text-success"


def render_state_cell(state: str, is_active: bool) -> Text:
    """Active state gets the ▶ marker, bold font and a status color."""
    if not is_active:
        return Text(f"{INACTIVE_MARKER}{state}")
    color = ACTIVE_STATE_COLORS.get(state, DEFAULT_ACTIVE_COLOR)
    return Text(f"{ACTIVE_MARKER}{state}", style=f"bold {color}")


class LiveCyclingStateDescription(VerticalGroup):
    """Centered description: key/value rows + live-cycling state list."""

    def __init__(self) -> None:
        super().__init__()
        self._active_index = INITIAL_ACTIVE_INDEX
        self._state_rows: list[Static] = []

    def compose(self) -> ComposeResult:
        for key, value in INFO_ROWS:
            with HorizontalGroup(classes="info-row"):
                yield Static(key, classes="info-key")
                yield Static(value, classes="info-value")
        yield Rule(classes="hr")
        with Static(classes="state"):
            with VerticalGroup(classes="state-rows"):
                self._state_rows = [
                    Static(
                        render_state_cell(state, idx == self._active_index),
                        classes="state-row",
                    )
                    for idx, state in enumerate(STATES)
                ]
                for row in self._state_rows:
                    yield row

    def on_mount(self) -> None:
        self.set_interval(1.0, self.advance_active_state)

    def advance_active_state(self) -> None:
        """Move the ▶ marker to the next state (round-robin)."""
        previous = self._active_index
        self._active_index = (self._active_index + 1) % len(STATES)
        for idx in (previous, self._active_index):
            self._state_rows[idx].update(
                render_state_cell(STATES[idx], idx == self._active_index)
            )


class MenuScreenTestApp(App):
    """Test app for MenuScreen variations. Each button pushes a different test case."""

    _HERE = Path(__file__).parent
    CSS_PATH = _HERE / "tcss" / "menu_screen.tcss"

    def compose(self) -> ComposeResult:
        yield Button("Test 1: Default (1 col, rich text)", id="test_default")
        yield Button("Test 2: Widget description (DataTable)", id="test_widget_desc")
        yield Button("Test 3: 2 columns", id="test_2cols")
        yield Button("Test 4: Large description", id="test_large_desc")
        yield Button(
            "Test 5: Info rows + live state description", id="life_state_desc"
        )

    @on(Button.Pressed, "#test_default")
    def show_default(self) -> None:
        items = [
            ButtonConfig(
                label="enable/disable",
                id="action_1",
                title="[b]Actions[/b]",
            ),
            ButtonConfig(label="set timeout", id="action_2"),
            ButtonConfig(
                label="set property 1: <current_val>",
                id="action_3",
                title="[b]Set property 1[/b]",
            ),
            ButtonConfig(label="show task logs", id="action_4"),
            ButtonConfig(
                label="Disabled Btn",
                id="disabled_btn",
                disabled=True,
            ),
            ButtonConfig(
                label="update version",
                id="action_5",
                layout=ButtonLayout.BOTTOM,
            ),
        ]
        description = (
            "version:         [b]0.1[/b]\n"
            "enabled:         [green]true[/green]\n"
            "state:           [yellow]running[/yellow]\n"
            "timeout:         2h\n"
            "last run:        <time>"
        )
        screen = MenuScreen(
            menu_items=items,
            description=description,
            show_back_button=True,
            show_exit_button=True,
        )
        screen.title = "Test 1"
        screen.sub_title = "Default (1 col, rich text)"
        self.push_screen(screen)

    @on(Button.Pressed, "#test_widget_desc")
    def show_widget_desc(self) -> None:
        table = DataTable(id="description")
        table.add_columns("Key", "Value")
        table.add_row("version", "0.1")
        table.add_row("enabled", "true")
        table.add_row("state", "running")
        table.add_row("timeout", "2h")
        table.add_row("last run", "10m ago")

        items = [
            ButtonConfig(label="enable/disable", id="action_1"),
            ButtonConfig(label="update version", id="action_2"),
            ButtonConfig(label="set timeout", id="action_3"),
        ]
        screen = MenuScreen(
            menu_items=items,
            description_widget=table,
            show_back_button=True,
        )
        screen.title = "Test 2"
        screen.sub_title = "Widget description (DataTable)"
        self.push_screen(screen)

    @on(Button.Pressed, "#test_2cols")
    def show_2cols(self) -> None:
        items = [
            ButtonConfig(label="Short A", id="a"),
            ButtonConfig(label="Short B", id="b"),
            ButtonConfig(label="\nShort C\n", id="c"),
            ButtonConfig(label="\nShort D\n", id="d"),
            ButtonConfig(label="Short E", id="e"),
            ButtonConfig(label="Short F", id="f"),

            ButtonConfig(label="Short G", id="g", layout=ButtonLayout.BOTTOM),
            ButtonConfig(label="Short H", id="h", layout=ButtonLayout.BOTTOM),
            ButtonConfig(label="Short I", id="i", layout=ButtonLayout.BOTTOM),
        ]
        screen = MenuScreen(
            menu_items=items,
            description="6 buttons in 2 columns",
            column_count=2,
            show_back_button=True,
        )
        screen.title = "Test 3"
        screen.sub_title = "2 columns"
        self.push_screen(screen)

    @on(Button.Pressed, "#test_large_desc")
    def show_large_desc(self) -> None:
        items = [
            ButtonConfig(label="Short A", id="a"),
            ButtonConfig(label="Short B", id="b"),
        ]
        lines = "\n".join(f"line {i}" for i in range(1, 31))
        screen = MenuScreen(
            menu_items=items,
            description=lines,
            description_max_height="30%",
            show_back_button=True,
        )
        screen.title = "Test 4"
        screen.sub_title = "Large description (scrollable)"
        self.push_screen(screen)

    @on(Button.Pressed, "#life_state_desc")
    def life_state_desc(self) -> None:
        items = [
            ButtonConfig(label="Start", id="action_1"),
            ButtonConfig(label="Stop", id="action_2"),
        ]
        screen = MenuScreen(
            menu_items=items,
            description_widget=LiveCyclingStateDescription(),
            show_back_button=True,
        )
        screen.title = "Test 5"
        screen.sub_title = "Info rows + live state description"
        self.push_screen(screen)

    @on(Button.Pressed)
    def handle_button_click(self, event: Button.Pressed) -> None:
        if event.button.id == "exit":
            self.notify("Closing application gracefully...")
            self.exit()
        elif event.button.id:
            self.notify(f"Button with ID '{event.button.id}' was pressed")


if __name__ == "__main__":
    app = MenuScreenTestApp()
    app.run()
