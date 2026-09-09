from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from textual import on
from textual.widgets import Button

from termux_tasker import proc_stats
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


@dataclass(frozen=True)
class _RunnerStatSummary:
    """Per-runner rollup feeding the System stats block (no OS probing here)."""

    id: str
    name: str
    state: str
    tasks_running: int
    tasks_total: int


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
        live_pids = {rid: proc.live_pids for rid, proc in app.state.runners.items()}
        self.description = self._build_overview(app.state.runners_path, live_pids)

    def _build_overview(
        self,
        runners_path: Path,
        live_pids: Mapping[str, list[int]] | None = None,
    ) -> str:
        lines: list[str] = ["[b $text-primary]Overview[/b $text-primary]"]
        runner_entries = self._load_runners(runners_path)
        summaries: list[_RunnerStatSummary] = []
        if not runner_entries:
            lines.append("No runners installed")
        for runner_meta, runner_settings in runner_entries:
            emoji = runner_emoji(runner_settings)
            color = runner_state_color(runner_settings)
            state = runner_settings.session.state
            lines.append(
                rf"{emoji} {runner_meta.general.name} [{color}]\[{state}][/{color}]"
            )
            tasks = self._load_tasks(runners_path / runner_meta.general.id / "tasks")
            running = sum(
                1
                for _, task_settings in tasks
                if task_settings.general.enabled
                and task_settings.session.state == "running"
            )
            summaries.append(
                _RunnerStatSummary(
                    id=runner_meta.general.id,
                    name=runner_meta.general.name,
                    state=state,
                    tasks_running=running,
                    tasks_total=len(tasks),
                )
            )
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
        lines.extend(self._build_stats(summaries, live_pids or {}))
        return "\n".join(lines)

    @staticmethod
    def _system_line(sys: proc_stats.SystemSummary) -> str:
        cpu_text = f"CPU {sys.cpu_percent:.0f}%" if sys.cpu_percent is not None else "CPU n/a"
        if sys.load_1 is None or sys.load_5 is None or sys.load_15 is None:
            load_text = "load n/a"
        else:
            load_text = f"load {sys.load_1:.1f} {sys.load_5:.1f} {sys.load_15:.1f}"
        cores_text = f"({sys.cpu_count} cores)" if sys.cpu_count else "(cores n/a)"
        if sys.mem_total is None or sys.mem_available is None or sys.mem_percent is None:
            mem_text = "MEM n/a"
        else:
            mem_text = (
                f"MEM {proc_stats.format_bytes(sys.mem_total - sys.mem_available)}"
                f"/{proc_stats.format_bytes(sys.mem_total)} {sys.mem_percent:.0f}%"
            )
        return f"{cpu_text} {load_text} {cores_text} | {mem_text}"

    @staticmethod
    def _build_stats(
        summaries: list[_RunnerStatSummary],
        live_pids: Mapping[str, list[int]],
    ) -> list[str]:
        """System + per-runner resource lines for the dashboard description.

        Only PIDs of currently executing runner children are probed, so the
        block stays cheap on the 1-second tick. Vanished or hidden
        (non-root Android) processes simply render as not-live.
        """
        lines = ["", "[b $text-primary]System[/b $text-primary]"]
        lines.append(DashboardScreen._system_line(proc_stats.system_summary()))
        live_count = 0
        total_procs = 0
        total_rss = 0
        runner_lines: list[str] = []
        for summary in summaries:
            roots = [pid for pid in live_pids.get(summary.id, [])]
            tree = proc_stats.tree_stats(roots) if roots else None
            if tree is not None and tree.num_procs > 0:
                live_count += 1
                total_procs += tree.num_procs
                total_rss += tree.rss_total
                label = roots[0] if roots[0] in tree.pids else tree.pids[0]
                extra = tree.num_procs - 1
                pid_text = f"pid {label}+{extra}" if extra > 0 else f"pid {label}"
                cpu_pct = proc_stats.cpu_percent_delta(
                    f"runner:{summary.id}", tree.cpu_s_total
                )
                cpu_text = f" CPU {cpu_pct:.0f}%" if cpu_pct is not None else ""
                stat_text = (
                    f"{pid_text} RSS {proc_stats.format_bytes(tree.rss_total)}"
                    f"{cpu_text} thr {tree.threads_total}"
                )
            else:
                stat_text = f"- ({summary.state})"
            runner_lines.append(
                f"  {summary.name}: {stat_text}"
                f" | tasks {summary.tasks_running}/{summary.tasks_total} run"
            )
        lines.append(
            f"Live {live_count}/{len(summaries)} runners"
            f" | procs {total_procs} | RSS {proc_stats.format_bytes(total_rss)}"
        )
        lines.extend(runner_lines)
        return lines

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
