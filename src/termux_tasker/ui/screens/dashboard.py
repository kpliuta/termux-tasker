from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.css.query import NoMatches
from textual.widget import Widget
from textual.widgets import Button, Rule, Static

from termux_tasker import proc_stats
from termux_tasker.config import AppConfig, RunnerMetadata, RunnerSettings, TaskMetadata, TaskSettings
from termux_tasker.ui.base import ButtonConfig, ButtonLayout, MenuScreen
from termux_tasker.ui.screens._state_colors import (
    runner_emoji,
    runner_state_color,
    task_state_color,
)
from termux_tasker.ui.screens._utils import termux_app
from termux_tasker.ui.screens.runners_screen import RunnersScreen
from termux_tasker.ui.screens.settings_screen import SettingsScreen

_BAR_CHAR = "■"
_CPU_DARK = "#7f1d1d"
_CPU_BRIGHT = "#ff4545"
_MEM_DARK = "#1e3a8a"
_MEM_BRIGHT = "#60a5fa"

_FALLBACK_HEXES: dict[str, str] = {
    "text-success": "#22c55e",
    "text-error": "#ef4444",
    "text-warning": "#eab308",
    "text-primary": "#3b82f6",
    "foreground-disabled": "#6b7280",
}

_BAR_MIN_WIDTH = 1
_WIDTH_FALLBACK = 40
_WIDTH_SLACK = 2


def _parse_hex_digits(digits: str) -> tuple[int, ...] | None:
    """Parse 6- or 8-digit hex into channels; None when malformed."""
    if len(digits) not in (6, 8):
        return None
    try:
        return tuple(int(digits[idx : idx + 2], 16) for idx in range(0, len(digits), 2))
    except ValueError:
        return None


def _opaque_hex(value: str, background: tuple[int, int, int], fallback: str) -> str:
    """Resolve a theme hex to an opaque ``#rrggbb`` Rich can parse.

    Translucent theme colors (``#rrggbbaa``, e.g. ``$foreground-disabled``)
    are alpha-blended over ``background`` — truncating the alpha would turn
    them into fully opaque look-alikes of the default text color.
    """
    text = value.strip()
    if not text.startswith("#"):
        return fallback
    channels = _parse_hex_digits(text[1:])
    if channels is None:
        return fallback
    if len(channels) == 3:
        red, green, blue = channels
        return f"#{red:02x}{green:02x}{blue:02x}"
    red, green, blue, alpha_byte = channels
    alpha = alpha_byte / 255
    blended = tuple(
        round(fg * alpha + bg * (1 - alpha)) for fg, bg in zip((red, green, blue), background)
    )
    return f"#{blended[0]:02x}{blended[1]:02x}{blended[2]:02x}"


def _lerp_hex(dark: str, bright: str, ratio: float) -> str:
    """Blend two ``#rrggbb`` colors; ratio 0 gives dark, 1 gives bright."""
    clamped = min(1.0, max(0.0, ratio))
    dark_rgb = tuple(int(dark[idx : idx + 2], 16) for idx in (1, 3, 5))
    bright_rgb = tuple(int(bright[idx : idx + 2], 16) for idx in (1, 3, 5))
    mixed = tuple(round(d + (b - d) * clamped) for d, b in zip(dark_rgb, bright_rgb))
    return f"#{mixed[0]:02x}{mixed[1]:02x}{mixed[2]:02x}"


def _make_bar(
    label: str,
    fraction: float | None,
    width: int,
    dark_hex: str,
    bright_hex: str,
    right_text: str,
    empty_hex: str,
) -> Text:
    """One resource bar: label left, gradient blocks middle, value right.

    The bar stretches to ``width``; the filled portion carries a dark to
    bright gradient, the remainder stays gray. ``fraction=None`` renders an
    empty bar (used while the CPU sampler has no second sample yet). A
    one-cell left pad mirrors the slack gap on the right.
    """
    bar_len = max(_BAR_MIN_WIDTH, width - len(label) - len(right_text) - 3)
    if fraction is None:
        filled = 0
    else:
        filled = min(bar_len, max(0, round(min(1.0, max(0.0, fraction)) * bar_len)))
    line = Text()
    line.append(f" {label} ")
    for idx in range(bar_len):
        if idx < filled:
            line.append(_BAR_CHAR, style=_lerp_hex(dark_hex, bright_hex, idx / max(filled - 1, 1)))
        else:
            line.append(_BAR_CHAR, style=empty_hex)
    line.append(f" {right_text}")
    return line


def _make_bars(
    cpu_percent: float | None,
    mem_used: int | None,
    mem_total: int | None,
    width: int,
    empty_hex: str,
) -> Text:
    """Top description part: CPU and MEM bars with adaptive byte units."""
    if cpu_percent is None:
        cpu_right = "n/a"
        cpu_fraction: float | None = None
    else:
        cpu_right = f"{cpu_percent:.0f}%"
        cpu_fraction = cpu_percent / 100
    if mem_total is None:
        mem_right = "n/a"
        mem_fraction: float | None = None
    elif mem_used is None:
        mem_right = f"n/a/{proc_stats.format_bytes(mem_total)}"
        mem_fraction = None
    else:
        used_text = proc_stats.format_bytes(mem_used)
        total_text = proc_stats.format_bytes(mem_total)
        used_val, _, used_unit = used_text.partition(" ")
        total_val, _, total_unit = total_text.partition(" ")
        if used_unit and used_unit == total_unit:
            mem_right = f"{used_val}/{total_val} {total_unit}"
        else:
            mem_right = f"{used_text}/{total_text}"
        mem_fraction = mem_used / mem_total if mem_total > 0 else None
    bars = Text()
    bars.append(_make_bar("CPU", cpu_fraction, width, _CPU_DARK, _CPU_BRIGHT, cpu_right, empty_hex))
    bars.append("\n")
    bars.append(_make_bar("MEM", mem_fraction, width, _MEM_DARK, _MEM_BRIGHT, mem_right, empty_hex))
    return bars


def _make_pid_line(
    roots: list[int], tree: proc_stats.TreeStats, warning_hex: str
) -> Text | None:
    """``PID <root>+<children> RSS <bytes>``; None when nothing live to show."""
    if not roots or tree.num_procs == 0:
        return None
    label = roots[0] if roots[0] in tree.pids else tree.pids[0]
    extra = tree.num_procs - 1
    pid_text = f"PID {label}+{extra}" if extra > 0 else f"PID {label}"
    line = Text()
    line.append("   │  ")
    line.append(f"{pid_text} RSS {proc_stats.format_bytes(tree.rss_total)}", style=warning_hex)
    return line


class _DashboardDescription(Widget):
    """Dashboard-only description: resource bars, a Rule, then the runner list."""

    DEFAULT_CSS = """\
    _DashboardDescription {
        width: 1fr;
        height: 1fr;

        .hr {
            color: $primary;
        }
        #dash-bars {
            width: 1fr;
            height: auto;
        }
        #dash-list-scroll {
            width: 1fr;
            height: 1fr;
        }
        #dash-list {
            width: 1fr;
            height: auto;
        }
    }
    """

    def __init__(self) -> None:
        super().__init__(id="description-widget")
        self._pending_bars: Text | None = None
        self._pending_runners: Text | None = None

    def compose(self) -> ComposeResult:
        yield Static(id="dash-bars")
        rule = Rule(classes="hr")
        rule.styles.margin = (0, 0)
        yield rule
        with VerticalScroll(id="dash-list-scroll"):
            yield Static(id="dash-list")

    def on_mount(self) -> None:
        if self._pending_bars is not None:
            self.update_bars(self._pending_bars)
            self._pending_bars = None
        if self._pending_runners is not None:
            self.update_runners(self._pending_runners)
            self._pending_runners = None

    def update_bars(self, bars: Text) -> None:
        """Replace the top resource-bars block (stashed until mounted)."""
        try:
            self.query_one("#dash-bars", Static).update(bars)
        except NoMatches:
            self._pending_bars = bars

    def update_runners(self, runner_lines: Text) -> None:
        """Replace the bottom runner/task block (stashed until mounted)."""
        try:
            self.query_one("#dash-list", Static).update(runner_lines)
        except NoMatches:
            self._pending_runners = runner_lines

    def palette(self) -> dict[str, str]:
        """Theme hexes for the vars the dashboard uses, with fallbacks.

        Rich ``Text`` styles cannot resolve Textual ``$text-*`` variables,
        so the hex is looked up here and passed into the pure builders.
        """
        resolved = dict(_FALLBACK_HEXES)
        if not self.is_mounted:
            return resolved
        theme_vars = self.app.get_css_variables()
        bg_channels = _parse_hex_digits((theme_vars.get("surface") or "").strip().lstrip("#"))
        background = (
            (bg_channels[0], bg_channels[1], bg_channels[2])
            if bg_channels is not None and len(bg_channels) == 3
            else (0x1E, 0x1E, 0x1E)
        )
        for key in resolved:
            value = theme_vars.get(key)
            if value is not None:
                resolved[key] = _opaque_hex(value, background, resolved[key])
        return resolved


class DashboardScreen(MenuScreen):
    def __init__(self) -> None:
        self._dashboard = _DashboardDescription()
        super().__init__(
            menu_items=[
                ButtonConfig("help", "Help", layout=ButtonLayout.BOTTOM),
                ButtonConfig("settings", "Settings", layout=ButtonLayout.BOTTOM),
                ButtonConfig("runners", "Runners", layout=ButtonLayout.BOTTOM),
            ],
            show_exit_button=True,
            column_count=3,
            description_widget=self._dashboard,
            description_min_height="100%",
            description_max_height="100%",
        )
        self.title = "Dashboard"
        self._poll_timer: Any = None

    def on_mount(self) -> None:
        self._refresh()
        # Widget sizes are not final on the very first paint (margins, the
        # scroll border and a late-appearing scrollbar all shrink the bar
        # area), so rebuild once layout has settled instead of showing
        # mis-sized bars until the next 1-second tick.
        self.call_after_refresh(self._refresh)
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
        runners = app.state.runners
        live_pids: dict[str, list[int]] = {
            runner_id: proc.live_pids for runner_id, proc in runners.items()
        }
        summary = proc_stats.system_summary()
        trees: dict[str, proc_stats.TreeStats] = {}
        for runner_id, pids in live_pids.items():
            if not pids:
                continue
            tree = proc_stats.tree_stats(pids)
            if tree.num_procs > 0:
                trees[runner_id] = tree
        palette = self._dashboard.palette()
        if summary.mem_total is not None and summary.mem_available is not None:
            mem_used: int | None = summary.mem_total - summary.mem_available
        else:
            mem_used = None
        self._dashboard.update_bars(
            _make_bars(
                summary.cpu_percent,
                mem_used,
                summary.mem_total,
                self._content_width(),
                palette["foreground-disabled"],
            )
        )
        self._dashboard.update_runners(
            self._build_runner_lines(app.state.runners_path, live_pids, trees, palette)
        )

    def _content_width(self) -> int:
        """Width available for the resource bars, with an unmounted fallback.

        A couple of cells of slack are reserved because the surrounding
        scroll container can grow a scrollbar that steals width after
        measuring — without it the bars wrap onto a second line.
        """
        measured = 0
        try:
            bars = self._dashboard.query_one("#dash-bars", Static)
            measured = bars.content_size.width or bars.size.width
        except NoMatches:
            pass
        if measured <= 0:
            try:
                scroll = self.query_one("#description-scroll")
                measured = scroll.content_size.width or scroll.size.width
            except NoMatches:
                pass
        if measured <= 0:
            measured = self.size.width
        if measured <= 0:
            return _WIDTH_FALLBACK
        return max(_BAR_MIN_WIDTH + 2, measured - _WIDTH_SLACK)

    def _build_runner_lines(
        self,
        runners_path: Path,
        live_pids: Mapping[str, list[int]] | None = None,
        trees: Mapping[str, proc_stats.TreeStats] | None = None,
        palette: Mapping[str, str] | None = None,
    ) -> Text:
        """Bottom description part: runners with PID lines plus their tasks."""
        pal = dict(_FALLBACK_HEXES)
        if palette is not None:
            pal.update(palette)
        lines = Text()
        runner_entries = self._load_runners(runners_path)
        if not runner_entries:
            lines.append(" No runners installed")
            return lines
        for runner_idx, (runner_meta, runner_settings) in enumerate(runner_entries):
            if runner_idx > 0:
                lines.append("\n")
            state = runner_settings.session.state
            state_hex = pal.get(runner_state_color(runner_settings).lstrip("$"), "#ffffff")
            header = Text()
            header.append(f" {runner_emoji(runner_settings)} {runner_meta.general.name} ")
            header.append(f"[{state}]", style=state_hex)
            lines.append(header)
            runner_id = runner_meta.general.id
            tree = (trees or {}).get(runner_id)
            if tree is not None:
                pid_line = _make_pid_line(list((live_pids or {}).get(runner_id, [])), tree, pal["text-warning"])
                if pid_line is not None:
                    lines.append("\n")
                    lines.append(pid_line)
            tasks = self._load_tasks(runners_path / runner_id / "tasks")
            for task_idx, (task_meta, task_settings) in enumerate(tasks):
                is_last_task = task_idx == len(tasks) - 1
                prefix = "   └─ " if is_last_task else "   ├─ "
                lines.append("\n")
                if not task_settings.general.enabled:
                    lines.append(
                        Text(f"{prefix}{task_meta.general.name} [disabled]", style=pal["foreground-disabled"])
                    )
                else:
                    task_line = Text()
                    task_line.append(f"{prefix}{task_meta.general.name} ")
                    t_color = task_state_color(task_settings)
                    task_line.append(
                        f"[{task_settings.session.state}]",
                        style=pal.get(t_color.lstrip("$"), "#ffffff"),
                    )
                    lines.append(task_line)
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

    @on(Button.Pressed, "#help")
    def on_help(self, event: Button.Pressed) -> None:
        event.stop()

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
