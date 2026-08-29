from __future__ import annotations

from pathlib import Path
from typing import Any

from textual import on
from textual.widgets import Button

from termux_tasker.config import AppConfig, RunnerMetadata, RunnerSettings, TaskMetadata, TaskSettings
from termux_tasker.ui.base import ButtonConfig, MenuScreen
from termux_tasker.ui.screens._state_colors import (
    runner_emoji,
    runner_state_color,
    task_state_color,
)
from termux_tasker.ui.screens._utils import termux_app
from termux_tasker.ui.screens.runners_screen import RunnersScreen
from termux_tasker.ui.screens.settings_screen import SettingsScreen


class DashboardScreen(MenuScreen):
    def __init__(self) -> None:
        super().__init__(
            menu_items=[
                ButtonConfig("runners", "Runners"),
                ButtonConfig("settings", "Settings"),
            ],
            show_exit_button=True,
            column_count=2,
            description="[b]Overview[/b]",
            description_max_height="50%",
        )
        self.title = "Dashboard"
        self._poll_timer: Any = None

    def on_mount(self) -> None:
        self._refresh()
        self._start_polling()

    def on_unmount(self) -> None:
        self._stop_polling()

    def _start_polling(self) -> None:
        self._poll_timer = self.set_interval(1.0, self._refresh)

    def _stop_polling(self) -> None:
        if self._poll_timer is not None:
            self._poll_timer.stop()
            self._poll_timer = None

    def _refresh(self) -> None:
        app = termux_app(self)
        self.description = self._build_overview(app.state.runners_path)

    def _build_overview(self, runners_path: Path) -> str:
        lines: list[str] = ["[b $text-primary]Overview[/b $text-primary]"]
        runner_entries = self._load_runners(runners_path)
        if not runner_entries:
            lines.append("No runners installed")
            return "\n".join(lines)
        for runner_idx, (runner_meta, runner_settings) in enumerate(runner_entries):
            emoji = runner_emoji(runner_settings)
            color = runner_state_color(runner_settings)
            state = runner_settings.session.state
            lines.append(
                rf"{emoji} {runner_meta.general.name} [{color}]\[{state}][/{color}]"
            )
            tasks = self._load_tasks(runners_path / runner_meta.general.id / "tasks")
            for task_idx, (task_meta, task_settings) in enumerate(tasks):
                is_last_task = task_idx == len(tasks) - 1
                prefix = "\u2514\u2500" if is_last_task else "\u251c\u2500"
                if not task_settings.general.enabled:
                    lines.append(
                        rf"  {prefix} [$foreground-disabled]{task_meta.general.name} \[disabled][/$foreground-disabled]"
                    )
                else:
                    t_color = task_state_color(task_settings)
                    t_state = task_settings.session.state
                    lines.append(
                        rf"  {prefix} {task_meta.general.name} [{t_color}]\[{t_state}][/{t_color}]"
                    )
        return "\n".join(lines)

    @staticmethod
    def _load_runners(runners_path: Path) -> list[tuple[RunnerMetadata, RunnerSettings]]:
        result: list[tuple[RunnerMetadata, RunnerSettings]] = []
        if not runners_path.exists():
            return result
        for runner_path in sorted(runners_path.iterdir()):
            if not runner_path.is_dir():
                continue
            meta_path = runner_path / "metadata.toml"
            if not meta_path.exists():
                continue
            meta = RunnerMetadata.load(meta_path)
            settings = RunnerSettings.load(runner_path / "settings.toml")
            result.append((meta, settings))
        return result

    @staticmethod
    def _load_tasks(tasks_path: Path) -> list[tuple[TaskMetadata, TaskSettings]]:
        result: list[tuple[TaskMetadata, TaskSettings]] = []
        if not tasks_path.exists():
            return result
        for task_path in sorted(tasks_path.iterdir()):
            if not task_path.is_dir():
                continue
            meta_path = task_path / "metadata.toml"
            if not meta_path.exists():
                continue
            meta = TaskMetadata.load(meta_path)
            settings = TaskSettings.load(task_path / "settings.toml")
            result.append((meta, settings))
        return result

    @on(Button.Pressed, "#runners")
    def on_runners(self, event: Button.Pressed) -> None:
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
