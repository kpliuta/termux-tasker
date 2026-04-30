from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Button
from termux_tasker.ui.base.screen import InfoScreen


class InfoTestApp(App):
    def compose(self) -> ComposeResult:
        yield Button("Show Info", id="info")
        yield Button("Show Warning", id="warning")
        yield Button("Show Error", id="error")

    @on(Button.Pressed, "#info")
    def show_info(self) -> None:
        self.push_screen(InfoScreen("Operation successful!", severity="info"))

    @on(Button.Pressed, "#warning")
    def show_warning(self) -> None:
        self.push_screen(InfoScreen("Disk space is low.", severity="warning"))

    @on(Button.Pressed, "#error")
    def show_error(self) -> None:
        self.push_screen(InfoScreen("Connection failed.", severity="error", button_text="Close"))


if __name__ == "__main__":
    app = InfoTestApp()
    app.run()
