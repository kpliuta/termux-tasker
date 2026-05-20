from __future__ import annotations

import shutil

from textual.app import App

from termux_tasker.app_state import AppState
from termux_tasker.config import AppConfig, RunnerSettings
from termux_tasker.ui.base.screen import ConfirmationScreen, LoadingScreen
from termux_tasker.ui.screens.main_menu import MainMenuScreen


class TermuxTaskerApp(App[None]):
    BINDINGS = [("ctrl+q", "quit", "Exit")]

    def __init__(self, app_version: str) -> None:
        super().__init__()
        self.state = AppState(app_version)

    def action_quit(self) -> None:  # type: ignore[override]
        if not self.state.runners:
            self.exit()
            return

        def on_confirm(result: str | None) -> None:
            if result is not None:
                self.run_worker(self._do_shutdown_exit())

        self.push_screen(
            ConfirmationScreen(
                message="Are you sure you want terminate runners in progress and exit?",
                ok_button_text="Yes",
                cancel_button_text="No",
                ok_button_id="yes_exit",
            ),
            on_confirm,
        )

    async def _do_shutdown_exit(self) -> None:
        loading = LoadingScreen("Runners shutting down")
        await self.push_screen(loading)
        for runner_proc in self.state.runners.values():
            await runner_proc.shutdown()
            settings = RunnerSettings.load(runner_proc.runner_dir / "settings.toml")
            settings.general.enabled = False
            settings.save(runner_proc.runner_dir / "settings.toml")
        await loading.dismiss(None)
        self.exit()

    def on_mount(self) -> None:
        self.state.ensure_dirs()
        self._ensure_app_config()
        self.push_screen(MainMenuScreen())

    def _ensure_app_config(self) -> None:
        config_path = self.state.app_config_file
        if config_path.exists():
            return

        default_path = self.state.default_app_config_file
        if default_path.exists():
            shutil.copy2(default_path, config_path)
        else:
            AppConfig().save(config_path)

    def on_exit_app(self) -> None:
        self.state.cleanup()


def main() -> None:
    import importlib.metadata
    try:
        version = importlib.metadata.version("termux-tasker")
    except importlib.metadata.PackageNotFoundError:
        version = "0.1.0"

    app = TermuxTaskerApp(app_version=version)
    app.run()


if __name__ == "__main__":
    main()
