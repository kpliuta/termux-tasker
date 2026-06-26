from __future__ import annotations

from pathlib import Path
from typing import Union

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Static

_HERE = Path(__file__).parent


class ConfirmationScreen(ModalScreen[Union[str, None]]):
    """A modal screen for displaying a confirmation message with two action buttons.

    The return value is the *ok_button_id* string on confirm, or *None* on cancel.
    Callers can pattern-match on the button ID to distinguish multiple
    confirmation screens (e.g. "yes_exit" vs "yes_uninstall").
    """

    CSS_PATH = _HERE / "tcss" / "confirmation_screen.tcss"
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(
            self,
            message: str,
            ok_button_text: str = "Ok",
            cancel_button_text: str = "Cancel",
            ok_button_id: str = "ok_button",
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.message = message
        self.ok_button_text = ok_button_text
        self.cancel_button_text = cancel_button_text
        self.ok_button_id = ok_button_id

    def compose(self) -> ComposeResult:
        with Vertical(id="confirmation_dialog"):
            yield Static(self.message, id="confirmation_message")
            with Horizontal(id="confirmation_buttons"):
                yield Button(self.cancel_button_text, id="cancel_button", variant="error")
                yield Button(self.ok_button_text, id=self.ok_button_id, variant="primary")

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dismiss the screen with ok_button_id or None."""
        event.stop()
        if event.button.id == "cancel_button":
            self.dismiss(None)
        else:
            self.dismiss(self.ok_button_id)

    def action_cancel(self) -> None:
        self.dismiss(None)
