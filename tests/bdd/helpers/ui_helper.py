"""Helper class encapsulating all pilot-based UI interactions for BDD steps."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from termux_tasker.ui.base.screen import ConfirmationScreen, LogScreen
from termux_tasker.ui.screens.runner_menu import RunnerMenuScreen
from termux_tasker.ui.screens.runners_screen import RunnersScreen
from termux_tasker.ui.screens.settings_screen import SettingsScreen
from termux_tasker.ui.screens.task_menu import TaskMenuScreen
from termux_tasker.ui.screens.tasks_menu import TasksMenuScreen

if TYPE_CHECKING:
    from tests.bdd.pilot_driver import PilotDriver


class UIHelper:
    """Wraps a Textual PilotDriver and exposes high-level interaction methods."""

    def __init__(self, pilot: PilotDriver) -> None:
        self._pilot = pilot

    @property
    def pilot(self) -> PilotDriver:
        return self._pilot

    @property
    def app(self) -> Any:
        return self._pilot.app

    # ── Button helpers ──────────────────────────────────────────────────

    def button(self, label: str) -> Any:
        """Return the first Button whose display text matches *label*."""
        for btn in self.app.screen.query("Button"):
            if str(btn.label).strip() == label:
                return btn
        msg = f"Button {label!r} not found on {type(self.app.screen).__name__}"
        raise AssertionError(msg)

    def click_label(self, label: str) -> None:
        """Click a button by its display label.

        Handles both menu-driven screens (via menu_items) and direct
        Button widgets.
        """
        screen = self.app.screen
        if hasattr(screen, "menu_items"):
            for lbl, btn_id in screen.menu_items.items():
                if str(lbl).strip() == label and btn_id:
                    self._pilot.click(f"#{btn_id}")
                    self._pilot.pause()
                    return
        for btn in screen.query("Button"):
            if str(btn.label).strip() == label and btn.id:
                self._pilot.click(f"#{btn.id}")
                self._pilot.pause()
                return
        raise AssertionError(f"No clickable button with label {label!r}")

    def click_id(self, selector: str) -> None:
        """Click a widget by its CSS selector (e.g. ``#my_button``)."""
        self._pilot.click(selector)

    def has_button(self, label: str) -> bool:
        for btn in self.app.screen.query("Button"):
            if str(btn.label).strip() == label:
                return True
        return False

    # ── Screen info ─────────────────────────────────────────────────────

    def title(self) -> str:
        return self.app.screen.title or ""

    def sub_title(self) -> str:
        return self.app.screen.sub_title or ""

    def screen_is(self, screen_type) -> bool:
        return isinstance(self.app.screen, screen_type)

    def assert_screen(self, screen_type: type) -> None:
        assert isinstance(self.app.screen, screen_type), (
            f"Expected {screen_type.__name__}, got {type(self.app.screen).__name__}"
        )

    # ── Value / key helpers ─────────────────────────────────────────────

    def set_value(self, selector: str, value: str) -> None:
        self._pilot.set_value(selector, value)

    def press(self, *keys: str) -> None:
        self._pilot.press(*keys)

    def pause(self, delay: float = 0.1) -> None:
        self._pilot.pause(delay)

    def click_yes(self) -> None:
        """Click the 'Yes' button, which can have varying IDs."""
        screen = self.app.screen
        for btn in screen.query("Button"):
            txt = str(btn.label).strip()
            if txt == "Yes" and btn.id:
                self._pilot.click(f"#{btn.id}")
                return
        raise AssertionError("No 'Yes' button found")

    # ── Navigation ──────────────────────────────────────────────────────

    def nav_to_runners(self) -> None:
        """From the main menu, navigate to the Runners screen."""
        self._pilot.click("#show_runners")

    def nav_to_runner_menu(self, runner_id: str = "sh_runner") -> None:
        """Navigate to the Runner Menu screen for *runner_id*."""
        screen = self.app.screen
        while isinstance(screen, ConfirmationScreen):
            self._pilot.pop_screen()
            self._pilot.pause(0.05)
            screen = self.app.screen
        if isinstance(screen, RunnerMenuScreen):
            return
        if isinstance(screen, RunnersScreen):
            self._pilot.click(f"#open_{runner_id}")
            self._pilot.pause()
            return
        self.nav_to_runners()
        self._pilot.click(f"#open_{runner_id}")
        self._pilot.pause()

    def nav_to_tasks(self, runner_id: str = "sh_runner") -> None:
        """Navigate to the Tasks screen for *runner_id*."""
        screen = self.app.screen
        if isinstance(screen, TasksMenuScreen):
            return
        self.nav_to_runner_menu(runner_id)
        screen = self.app.screen
        if isinstance(screen, TasksMenuScreen):
            return
        self._pilot.click("#show_tasks")
        self._pilot.pause()

    def nav_to_task_menu(self, task_id: str = "sh_runner_task") -> None:
        """Navigate to the Task Menu screen for *task_id*."""
        screen = self.app.screen
        if isinstance(screen, TaskMenuScreen):
            return
        self.nav_to_tasks()
        screen = self.app.screen
        if isinstance(screen, TaskMenuScreen):
            return
        self._pilot.click(f"#open_{task_id}")

    def nav_to_settings(self) -> None:
        """From the main menu, navigate to the Settings screen."""
        screen = self.app.screen
        if isinstance(screen, SettingsScreen):
            return
        self._pilot.click("#settings")

    # ── Pilot passthrough ────────────────────────────────────────────────

    def push_screen(self, screen: Any) -> None:
        self._pilot.push_screen(screen)

    def wait_until_screen(self, screen_type: type, timeout: float = 5) -> None:
        self._pilot.wait_until_screen(screen_type, timeout=timeout)

    @property
    def pilot_driver(self) -> Any:
        return self._pilot

    # ── Log screen helpers ──────────────────────────────────────────────

    def push_log_screen(self, log_file: Path, follow: bool = False) -> None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        if not log_file.exists():
            log_file.write_text("")
        self._pilot.push_screen(
            factory=lambda: LogScreen(content=log_file, show_follow=follow)
        )
        self._pilot.pause(0.3)

    # ── Assertions ──────────────────────────────────────────────────────

    def assert_has_button(self, label: str) -> None:
        assert self.has_button(label), f"Button {label!r} not found"

    def assert_description_contains(self, text: str) -> None:
        desc = getattr(self.app.screen, "description", "") or ""
        assert text in desc, f"Description does not contain {text!r}: {desc}"

    def assert_confirmation_message_contains(self, text: str) -> None:
        assert isinstance(self.app.screen, ConfirmationScreen)
        msg = self.app.screen.query_one("#confirmation_message")
        content = (
            str(msg.render())
            if hasattr(msg, "render")
            else str(msg._content)
        )
        assert text in content
