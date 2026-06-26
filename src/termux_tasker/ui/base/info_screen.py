from __future__ import annotations

from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

_HERE = Path(__file__).parent


class InfoScreen(ModalScreen[None]):
    """A modal screen for displaying messages with different severity levels."""

    CSS_PATH = _HERE / "tcss" / "info_screen.tcss"
    BINDINGS = [("escape", "dismiss", "Close")]

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
    def on_ok(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss(None)

    def action_dismiss(self, result: None = None) -> None:  # type: ignore[override]
        self.dismiss(None)
