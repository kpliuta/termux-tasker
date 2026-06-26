from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll, Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, RadioButton, RadioSet, Static

_HERE = Path(__file__).parent


class InputScreen(ModalScreen[Union[str, Sequence[str], None]]):
    """A modal screen for gathering user input via text, radio buttons, or checkboxes."""

    CSS_PATH = _HERE / "tcss" / "input_screen.tcss"
    BINDINGS = [("escape", "cancel", "Cancel")]

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
    def handle_ok(self, event: Button.Pressed) -> None:
        """Collect and return the selected value(s)."""
        event.stop()
        if self.input_type == "text":
            self.dismiss(self.query_one(Input).value)
        elif self.input_type == "radio":
            radio_set = self.query_one(RadioSet)
            pressed = radio_set.pressed_button
            if pressed is not None:
                self.dismiss(str(pressed.label))
            else:
                self.dismiss(None)
        elif self.input_type == "checkbox":
            selected = [
                str(cb.label) for cb in self.query(Checkbox) if cb.value
            ]
            self.dismiss(selected)

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self, event: Button.Pressed) -> None:
        """Close the dialog without returning a value."""
        event.stop()
        self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
