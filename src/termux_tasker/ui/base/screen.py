from pathlib import Path
from typing import Mapping, Sequence, Union

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Grid, Vertical, Horizontal
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Header, Footer, Button, Static, DirectoryTree, Input,
    Checkbox, RadioButton, RadioSet, LoadingIndicator, RichLog
)


class MenuScreen(Screen):
    """A screen with a menu of buttons."""

    CSS_PATH = "menu_screen.tcss"

    def __init__(
            self,
            menu_items: Mapping[str, str],
            description: str | None = None,
            show_back_button: bool = False,
            show_exit_button: bool = False,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ) -> None:
        """Initialize the menu screen.

        Args:
            menu_items: A mapping of button IDs to their labels.
            description: Optional multiline description text.
            show_back_button: Whether to show a 'Back' button.
            show_exit_button: Whether to show an 'Exit' button.
        """
        super().__init__(name=name, id=id, classes=classes)
        self.menu_items = menu_items
        self.description = description
        self.show_back_button = show_back_button
        self.show_exit_button = show_exit_button

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            if self.description:
                yield Static(self.description, id="description")

            for btn_id, label in self.menu_items.items():
                yield Button(label, id=btn_id, variant="default")

            yield Static(classes="spacer")

            if self.show_back_button:
                yield Button("Back", id="back", variant="error")

            if self.show_exit_button:
                yield Button("Exit", id="exit", variant="error")

        yield Footer()

    @on(Button.Pressed, "#back")
    def on_back_button_pressed(self, event: Button.Pressed) -> None:
        """Handle back button presses."""
        event.stop()
        self.app.pop_screen()

    def on_key(self, event) -> None:
        """Handle key presses for navigation."""
        if event.key == "up":
            self.focus_previous(Button)
            event.stop()
        elif event.key == "down":
            self.focus_next(Button)
            event.stop()

    def on_mount(self) -> None:
        pass


class FileBrowserScreen(ModalScreen[Path]):
    """A modal screen for browsing and selecting files or folders."""

    CSS_PATH = "file_browser_screen.tcss"

    def __init__(
            self,
            select_folder: bool = False,
            path: str = "./",
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.select_folder = select_folder
        self.path = path
        self._selected_path: Path | None = None

    def compose(self) -> ComposeResult:
        with Grid():
            yield DirectoryTree(self.path)
            yield Button("Cancel", id="cancel", variant="error")
            yield Button("Select", id="select", variant="primary", disabled=True)

    @on(DirectoryTree.FileSelected)
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        if not self.select_folder:
            self._selected_path = event.path
            self.query_one("#select", Button).disabled = False
        else:
            self._selected_path = None
            self.query_one("#select", Button).disabled = True

    @on(DirectoryTree.DirectorySelected)
    def on_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        if self.select_folder:
            self._selected_path = event.path
            self.query_one("#select", Button).disabled = False
        else:
            self._selected_path = None
            self.query_one("#select", Button).disabled = True

    @on(Button.Pressed, "#select")
    def on_select(self) -> None:
        if self._selected_path:
            self.dismiss(self._selected_path)

    @on(Button.Pressed, "#cancel")
    def on_cancel(self) -> None:
        self.dismiss(None)


class InputScreen(ModalScreen[Union[str, Sequence[str], None]]):
    """A modal screen for gathering user input via text, radio buttons, or checkboxes."""

    CSS_PATH = "input_screen.tcss"

    def __init__(
            self,
            title: str,
            description: str | None = None,
            input_type: str = "text",
            options: Sequence[str] | None = None,
            current_value: Union[str, Sequence[str], None] = None,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ) -> None:
        """Initialize the input screen.

        Args:
            title: The title of the dialog.
            description: Optional description text.
            input_type: One of 'text', 'radio', or 'checkbox'.
            options: List of options for radio or checkbox types.
            current_value: Initial value(s) to pre-populate or select.
        """
        super().__init__(name=name, id=id, classes=classes)
        self.dialog_title = title
        self.description = description
        self.input_type = input_type
        self.options = options or []
        self.current_value = current_value

    def compose(self) -> ComposeResult:
        with Grid():
            with Vertical(id="input_dialog"):
                yield Static(self.dialog_title, id="input_title")
                if self.description:
                    yield Static(self.description, id="input_description")

                with VerticalScroll(id="input_content"):
                    if self.input_type == "text":
                        yield Input(
                            value=str(self.current_value) if self.current_value is not None else "",
                            id="input_field"
                        )
                    elif self.input_type == "radio":
                        with RadioSet():
                            for option in self.options:
                                is_selected = False
                                if self.current_value is not None:
                                    if isinstance(self.current_value, str):
                                        is_selected = option.lower() == self.current_value.lower()
                                yield RadioButton(option, value=is_selected)
                    elif self.input_type == "checkbox":
                        selected_values = set()
                        if self.current_value:
                            if isinstance(self.current_value, str):
                                selected_values.add(self.current_value.lower())
                            elif isinstance(self.current_value, (list, tuple, set)):
                                selected_values = {v.lower() for v in self.current_value if isinstance(v, str)}

                        for option in self.options:
                            yield Checkbox(
                                option,
                                value=option.lower() in selected_values
                            )

            yield Button("Cancel", id="cancel", variant="error")
            yield Button("Ok", id="ok", variant="primary")

    @on(Button.Pressed, "#ok")
    def handle_ok(self) -> None:
        """Collect and return the selected value(s)."""
        if self.input_type == "text":
            self.dismiss(self.query_one(Input).value)
        elif self.input_type == "radio":
            radio_set = self.query_one(RadioSet)
            if radio_set.pressed_button:
                self.dismiss(str(radio_set.pressed_button.label))
            else:
                self.dismiss(None)
        elif self.input_type == "checkbox":
            selected = [
                str(cb.label) for cb in self.query(Checkbox) if cb.value
            ]
            self.dismiss(selected)

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        """Close the dialog without returning a value."""
        self.dismiss(None)


class InfoScreen(ModalScreen[None]):
    """A modal screen for displaying messages with different severity levels."""

    CSS_PATH = "info_screen.tcss"

    def __init__(
            self,
            message: str,
            severity: str = "info",
            button_text: str = "Ok",
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.message = message
        self.severity = severity
        self.button_text = button_text

    def compose(self) -> ComposeResult:
        with Vertical(id="info_dialog"):
            yield Static(self.message, id="info_message", classes=self.severity)
            yield Button(self.button_text, id="info_button", variant="primary")

    @on(Button.Pressed, "#info_button")
    def on_ok(self) -> None:
        self.dismiss(None)


class LoadingScreen(ModalScreen[None]):
    """A modal screen with a loading indicator and a message."""

    CSS_PATH = "loading_screen.tcss"

    def __init__(
            self,
            message: str = "",
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.initial_message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="loading_dialog"):
            yield LoadingIndicator()
            yield Static(self.initial_message, id="loading_message")

    def update_message(self, message: str) -> None:
        """Update the message displayed below the loading indicator."""
        self.query_one("#loading_message", Static).update(message)


class LogScreen(ModalScreen[None]):
    """A modal screen for displaying logs with an optional 'follow' feature."""

    CSS_PATH = "log_screen.tcss"

    def __init__(
            self,
            content: str | Path = "",
            show_follow: bool = False,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.content = content
        self.show_follow = show_follow and isinstance(content, Path)
        self._timer = None

    def compose(self) -> ComposeResult:
        with Vertical(id="log_dialog"):
            yield RichLog(highlight=True, markup=True)
            with Horizontal(id="log_controls"):
                if self.show_follow:
                    yield Checkbox("Follow", id="follow_checkbox")
                yield Button("Close", id="close_button", variant="primary")

    def on_mount(self) -> None:
        log = self.query_one(RichLog)
        if isinstance(self.content, Path):
            if self.content.exists():
                log.write(self.content.read_text())
            else:
                log.write(f"[red]File not found: {self.content}[/]")
        else:
            log.write(self.content)

    @on(Checkbox.Changed, "#follow_checkbox")
    def on_follow_changed(self, event: Checkbox.Changed) -> None:
        if event.value:
            # Simple follow implementation using a timer
            self._timer = self.set_interval(1.0, self._update_log_from_file)
        else:
            if self._timer:
                self._timer.stop()
                self._timer = None

    def _update_log_from_file(self) -> None:
        if isinstance(self.content, Path) and self.content.exists():
            log = self.query_one(RichLog)
            # This is a naive implementation; in a real app, you'd track file offset
            log.clear()
            log.write(self.content.read_text())

    @on(Button.Pressed, "#close_button")
    def on_close(self) -> None:
        if self._timer:
            self._timer.stop()
        self.dismiss(None)
