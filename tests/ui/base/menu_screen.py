from __future__ import annotations


from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Button, DataTable

from termux_tasker.ui.base import (
    ButtonConfig,
    ButtonLayout,
    MenuScreen,
)


class MenuScreenTestApp(App):
    """Test app for MenuScreen variations. Each button pushes a different test case."""

    def compose(self) -> ComposeResult:
        yield Button("Test 1: Default (1 col, rich text)", id="test_default")
        yield Button("Test 2: Widget description (DataTable)", id="test_widget_desc")
        yield Button("Test 3: 2 columns", id="test_2cols")
        yield Button("Test 4: Large description", id="test_large_desc")

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
