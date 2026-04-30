import asyncio

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Button

from termux_tasker.ui.base.screen import LoadingScreen


class LoadingTestApp(App):
    def compose(self) -> ComposeResult:
        yield Button("Start Long Operation", id="start")

    @on(Button.Pressed, "#start")
    async def start_operation(self) -> None:
        loading = LoadingScreen("Starting...")
        await self.push_screen(loading)

        # 2 sec without (initial) message - actually it has initial message "Starting..."
        # Let's adjust to the prompt: 2 sec starting, then 2 sec updated message, then 2 sec another.

        await asyncio.sleep(2)
        loading.update_message("Processing data...")

        await asyncio.sleep(2)
        loading.update_message("Finalizing...")

        await asyncio.sleep(2)
        await self.pop_screen()
        self.notify("Operation complete!")


if __name__ == "__main__":
    app = LoadingTestApp()
    app.run()
