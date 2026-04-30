from pathlib import Path

from textual.app import App

from termux_tasker.ui.base.screen import FileBrowserScreen


class FileBrowserTestApp(App):
    def on_mount(self) -> None:
        # Test case: Select a file and return absolute path
        self.push_screen(
            FileBrowserScreen(select_folder=False),
            callback=self.handle_selection
        )

    def handle_selection(self, selected_path: Path | None) -> None:
        if selected_path:
            self.notify(f"Selected: {selected_path}")
        else:
            self.notify("Selection cancelled")


if __name__ == "__main__":
    app = FileBrowserTestApp()
    app.run()
