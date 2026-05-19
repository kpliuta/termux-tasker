from __future__ import annotations

from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Button

from termux_tasker.ui.base.screen import LogScreen


class LogTestApp(App):
    def compose(self) -> ComposeResult:
        yield Button("Show Text Log", id="text_log")
        yield Button("Show File Log (No Follow)", id="file_log")
        yield Button("Show File Log (With Follow)", id="follow_log")
        yield Button("Show File Log (With Follow + Reset)", id="follow_reset_log")

    @on(Button.Pressed, "#text_log")
    def show_text_log(self) -> None:
        content = "Line 1: System initialized.\nLine 2: Loading components...\nLine 3: Success!"
        self.push_screen(LogScreen(content=content))

    @on(Button.Pressed, "#file_log")
    def show_file_log(self) -> None:
        # Create a dummy log file
        log_file = Path("test_simple.log")
        log_file.write_text("This is a simple log file content.")
        self.push_screen(LogScreen(content=log_file))

    @on(Button.Pressed, "#follow_log")
    def show_follow_log(self) -> None:
        log_file = Path("test_follow.log")
        log_file.write_text("Log started...\n")
        self.push_screen(LogScreen(content=log_file, show_follow=True))

        # Start a background task to append to the file
        self.run_worker(self.append_to_file(log_file))

    @on(Button.Pressed, "#follow_reset_log")
    def show_follow_reset_log(self) -> None:
        log_file = Path("test_follow_reset.log")
        log_file.write_text("Initial content line 1\nInitial content line 2\n")
        self.push_screen(LogScreen(content=log_file, show_follow=True))

        self.run_worker(self.append_to_file(log_file))

    async def append_to_file(self, path: Path):
        import asyncio
        for i in range(5):
            await asyncio.sleep(2)
            with path.open("a") as f:
                f.write(f"New entry {i + 1} at {asyncio.get_event_loop().time()}\n")


if __name__ == "__main__":
    app = LogTestApp()
    app.run()
