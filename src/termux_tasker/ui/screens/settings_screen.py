from __future__ import annotations

from typing import Any

from textual import on
from textual.widgets import Button

from termux_tasker.config import AppConfig
from termux_tasker.ui.base.screen import MenuScreen, InputScreen
from termux_tasker.ui.screens._utils import termux_app


class SettingsScreen(MenuScreen):
    def __init__(self, app_version: str, session_id: str, upgrade_on_startup: bool) -> None:
        super().__init__(
            menu_items={
                rf"Termux upgrade on startup \[{upgrade_on_startup}]": "upgrade_on_startup",
            },
            description=f"App Version: {app_version}\nSession ID: {session_id}",
            show_back_button=True,
        )
        self.title = "Settings"
        self._upgrade_val = upgrade_on_startup

    @on(Button.Pressed, "#upgrade_on_startup")
    def on_upgrade(self, event: Button.Pressed) -> None:
        event.stop()
        app = termux_app(self)
        cur_val = str(self._upgrade_val).lower()

        def on_setting(result: Any) -> None:
            if result is not None:
                cfg = AppConfig.load(app.state.app_config_file)
                cfg.settings.upgrade_on_startup = result == "true"
                cfg.save(app.state.app_config_file)
                self._upgrade_val = cfg.settings.upgrade_on_startup
                self.menu_items = {
                    rf"Termux upgrade on startup \[{cfg.settings.upgrade_on_startup}]": "upgrade_on_startup",
                }

        self.app.push_screen(
            InputScreen(
                title="Termux upgrade on startup",
                input_type="radio",
                options=["true", "false"],
                current_value=cur_val,
            ),
            on_setting,
        )
