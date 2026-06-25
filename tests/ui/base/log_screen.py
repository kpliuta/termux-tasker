from __future__ import annotations

from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Button

from termux_tasker.ui.base.log_screen import LogScreen

_LONG_TEXT = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.

THIS_IS_A_VERY_LONG_STRING_WITHOUT_ANY_SPACES_THAT_SHOULD_REQUIRE_HORIZONTAL_SCROLLING_WHEN_WORD_WRAP_IS_DISABLED_0123456789_abcdefghijklmnopqrstuvwxyz_REPEAT_THIS_IS_A_VERY_LONG_STRING_WITHOUT_ANY_SPACES_THAT_SHOULD_REQUIRE_HORIZONTAL_SCROLLING_WHEN_WORD_WRAP_IS_DISABLED

Short line 1
Medium length line with some words to see how wrapping behaves at different widths.
Another very long line without spaces -> abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz
Final short line.
"""  # noqa: E501


class LogTestApp(App):
    def compose(self) -> ComposeResult:
        yield Button("Show Text Log", id="text_log")
        yield Button("Show File Log (Static)", id="file_log")
        yield Button("Show File Log (Dynamic)", id="follow_log")
        yield Button("Wrap Test (file)", id="wrap_file")
        yield Button("Wrap Test (string)", id="wrap_text")
        yield Button("Wrap Test (dynamic)", id="wrap_dynamic")

    @on(Button.Pressed, "#text_log")
    def show_text_log(self) -> None:
        content = "Line 1: System initialized.\nLine 2: Loading components...\nLine 3: Success!"
        self.push_screen(LogScreen(content=content))

    @on(Button.Pressed, "#file_log")
    def show_file_log(self) -> None:
        log_file = Path("test_simple.log")
        log_file.write_text("This is a simple log file content.")
        self.push_screen(LogScreen(content=log_file))

    @on(Button.Pressed, "#follow_log")
    def show_follow_log(self) -> None:
        log_file = Path("test_follow.log")
        log_file.write_text("Log started...\n")
        self.push_screen(LogScreen(content=log_file, is_dynamic=True))
        self.run_worker(self.append_to_file(log_file))

    @on(Button.Pressed, "#wrap_file")
    def show_wrap_file(self) -> None:
        log_file = Path("/tmp/wrap_test.log")
        log_file.write_text(_LONG_TEXT)
        self.push_screen(LogScreen(content=log_file, soft_wrap=True))

    @on(Button.Pressed, "#wrap_text")
    def show_wrap_text(self) -> None:
        self.push_screen(LogScreen(content=_LONG_TEXT, soft_wrap=True))

    @on(Button.Pressed, "#wrap_dynamic")
    def show_wrap_dynamic(self) -> None:
        log_file = Path("/tmp/wrap_dynamic.log")
        log_file.write_text(_LONG_TEXT)
        self.push_screen(LogScreen(content=log_file, is_dynamic=True, soft_wrap=True))

    @staticmethod
    async def append_to_file(path: Path):
        import asyncio
        for i in range(20):
            await asyncio.sleep(2)
            with path.open("a") as f:
                f.write(f"New entry {i + 1} at {asyncio.get_event_loop().time()}\n")


if __name__ == "__main__":
    app = LogTestApp()
    app.run()
