from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import LoadingIndicator, Static

_HERE = Path(__file__).parent


class LoadingScreen(ModalScreen[None]):
    """A modal screen with a loading indicator and a message."""

    CSS_PATH = _HERE / "tcss" / "loading_screen.tcss"

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
