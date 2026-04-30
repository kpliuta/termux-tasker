from typing import Union, Sequence

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Button

from termux_tasker.ui.base.screen import InputScreen


class InputTestApp(App):
    def compose(self) -> ComposeResult:
        yield Button("Test Text Input", id="test_text")
        yield Button("Test Radio Input", id="test_radio")
        yield Button("Test Checkbox Input", id="test_checkbox")

    @on(Button.Pressed, "#test_text")
    def show_text_input(self) -> None:
        self.push_screen(
            InputScreen(
                title="Set Username",
                description="Please enter your preferred username below.",
                input_type="text",
                current_value="hound"
            ),
            callback=self.handle_result
        )

    @on(Button.Pressed, "#test_radio")
    def show_radio_input(self) -> None:
        self.push_screen(
            InputScreen(
                title="Select Theme",
                description="Choose a color theme for the UI.",
                input_type="radio",
                options=["Light", "Dark", "System Default"],
                current_value="Dark"
            ),
            callback=self.handle_result
        )

    @on(Button.Pressed, "#test_checkbox")
    def show_checkbox_input(self) -> None:
        self.push_screen(
            InputScreen(
                title="Select Features",
                description="Enable or disable optional components.",
                input_type="checkbox",
                options=["Logging", "Auto-save", "Cloud Sync", "Notifications"],
                current_value=["logging", "notifications"]
            ),
            callback=self.handle_result
        )

    def handle_result(self, result: Union[str, Sequence[str], None]) -> None:
        if result is not None:
            self.notify(f"Result: {result}")
        else:
            self.notify("Action cancelled")


if __name__ == "__main__":
    app = InputTestApp()
    app.run()
