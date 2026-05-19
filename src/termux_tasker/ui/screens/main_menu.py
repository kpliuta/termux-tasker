from __future__ import annotations

from textual import on
from textual.widgets import Button

from termux_tasker.ui.base.screen import MenuScreen
from termux_tasker.config import AppConfig
from termux_tasker.ui.screens.settings_screen import SettingsScreen
from termux_tasker.ui.screens.runners_screen import RunnersScreen
from termux_tasker.ui.screens._utils import termux_app


class MainMenuScreen(MenuScreen):
    def __init__(self) -> None:
        super().__init__(
            menu_items={
                "Show Runners": "show_runners",
                "Settings": "settings",
            },
            show_exit_button=True,
        )
        self.title = "Main Menu"

    @on(Button.Pressed, "#show_runners")
    def on_show_runners(self, event: Button.Pressed) -> None:
        event.stop()
        termux_app(self).push_screen(RunnersScreen())

    @on(Button.Pressed, "#settings")
    def on_settings(self, event: Button.Pressed) -> None:
        event.stop()
        app = termux_app(self)
        cfg = AppConfig.load(app.state.app_config_file)
        termux_app(self).push_screen(
            SettingsScreen(app.state.app_version, app.state.session_id, cfg.settings.upgrade_on_startup)
        )

    @on(Button.Pressed, "#exit")
    def on_exit(self, event: Button.Pressed) -> None:
        event.stop()
        termux_app(self).action_quit()
