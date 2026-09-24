from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from textual.app import App

from termux_tasker.ui.base.menu_screen import ButtonConfig, MenuScreen
from termux_tasker.ui.screens._ui_utils import go_home  # noqa
from termux_tasker.ui.screens.dashboard import DashboardScreen


def _make_mock_app(runners_path: Path) -> Any:
    app = MagicMock()
    app.state.runners_path = runners_path
    app.state.runners = {}
    return app


class TestGoHome:
    @pytest.mark.asyncio
    async def test_pops_stack_to_dashboard(self, tmp_path: Path) -> None:
        runners_path = tmp_path / "runners"
        runners_path.mkdir()
        mock_app = _make_mock_app(runners_path)

        with patch(
            "termux_tasker.ui.screens.dashboard.termux_app",
            return_value=mock_app,
        ):
            class TestApp(App):
                def on_mount(self) -> None:
                    self.push_screen(DashboardScreen())
                    self.push_screen(MenuScreen(
                        menu_items=[ButtonConfig(label="A", id="a")],
                        show_home_button=True,
                        show_back_button=True,
                    ))
                    self.push_screen(MenuScreen(
                        menu_items=[ButtonConfig(label="B", id="b")],
                        show_home_button=True,
                        show_back_button=True,
                    ))

            async with TestApp().run_test() as pilot:
                await pilot.pause()
                go_home(pilot.app.screen)
                await pilot.pause()
                assert isinstance(pilot.app.screen, DashboardScreen)
                assert len(pilot.app.screen_stack) == 2

    @pytest.mark.asyncio
    async def test_stops_at_last_screen_without_dashboard(self) -> None:
        """The stack-size guard prevents popping past the bottom screen."""

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(MenuScreen(
                    menu_items=[ButtonConfig(label="A", id="a")],
                ))
                self.push_screen(MenuScreen(
                    menu_items=[ButtonConfig(label="B", id="b")],
                ))

        async with TestApp().run_test() as pilot:
            await pilot.pause()
            go_home(pilot.app.screen)
            await pilot.pause()
            assert len(pilot.app.screen_stack) == 1
