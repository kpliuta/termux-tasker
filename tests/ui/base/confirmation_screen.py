from __future__ import annotations

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Button

from termux_tasker.ui.base.screen import ConfirmationScreen


class ConfirmationTestApp(App):
    """An example app for demonstrating the ConfirmationScreen."""

    def compose(self) -> ComposeResult:
        yield Button("Show Custom Confirmation", id="custom_confirmation_button")

    @on(Button.Pressed, "#custom_confirmation_button")
    def action_show_custom_confirmation(self) -> None:
        self.push_screen(
            ConfirmationScreen(
                message="Do you want to delete this item permanently?",
                ok_button_text="Delete",
                cancel_button_text="Keep",
                ok_button_id="delete_confirmed"
            )
        )

    @on(Button.Pressed, "#delete_confirmed")
    def handle_delete_confirmed(self) -> None:
        self.notify("Delete action confirmed!")


if __name__ == "__main__":
    app = ConfirmationTestApp()
    app.run()
