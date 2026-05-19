from __future__ import annotations

from textual import on
from textual.app import App
from textual.widgets import Button

from termux_tasker.ui.base.screen import MenuScreen


class ScreenTestApp(App):
    def on_mount(self) -> None:
        # Mapping button IDs to labels
        menu_items = {
            "action_1": "enable/disable",
            "action_2": "update version",
            "action_3": "set timeout",
            "action_4": "set property 1: <current_val>",
            "action_5": "show task logs"
        }
        description = (
            "version:         0.1\n"
            "enabled:         true\n"
            "state:           running\n"
            "timeout:         2h\n"
            "last run:        <time>"
        )

        menu = MenuScreen(
            menu_items=menu_items,
            description=description,
            show_back_button=True,
            show_exit_button=True
        )
        menu.title = "task runner 1 [enabled]"
        menu.sub_title = "task 1"
        self.push_screen(menu)

    @on(Button.Pressed)
    def handle_button_click(self, event: Button.Pressed) -> None:
        """Handle button clicks.
        
        Custom actions and 'Exit' bubble up here.
        """
        if event.button.id == "exit":
            self.notify("Closing application gracefully...")
            self.exit()
        elif event.button.id:
            self.notify(f"Button with ID '{event.button.id}' was pressed")


if __name__ == "__main__":
    app = ScreenTestApp()
    app.run()
