from __future__ import annotations

from termux_tasker.config import RunnerSettings, TaskSettings

# ── Runner state → Textual CSS color ──────────────────────────────────

RUNNER_STATE_COLORS: dict[str, str] = {
    "off": "$text-error",
    "initialization": "$text-success",
    "before-exec": "$text-success",
    "exec": "$text-success",
    "before-task": "$text-success",
    "task-exec": "$text-success",
    "after-task": "$text-success",
    "after-exec": "$text-success",
    "idle": "$text-warning",
    "termination": "$text-error",
}

# ── Task state → Textual CSS color ────────────────────────────────────

TASK_STATE_COLORS: dict[str, str] = {
    "running": "$text-success",
    "stopped": "$text-error",
}

# ── Enabled / disabled colors ─────────────────────────────────────────

ENABLED_COLOR = "$text-success"
DISABLED_COLOR = "$text-error"

# ── Ball emojis ───────────────────────────────────────────────────────

EMOJI_GREEN = "\U0001f7e2"
EMOJI_YELLOW = "\U0001f7e1"
EMOJI_RED = "\U0001f534"


def runner_state_color(settings: RunnerSettings) -> str:
    """Return the Textual CSS color for a runner's current state."""
    if not settings.general.enabled:
        return DISABLED_COLOR
    return RUNNER_STATE_COLORS.get(settings.session.state, ENABLED_COLOR)


def task_state_color(settings: TaskSettings) -> str:
    """Return the Textual CSS color for a task's current state."""
    if not settings.general.enabled:
        return DISABLED_COLOR
    return TASK_STATE_COLORS.get(settings.session.state, ENABLED_COLOR)


def runner_emoji(settings: RunnerSettings) -> str:
    """Return a ball emoji reflecting the runner's overall status.

    - green  = enabled + working state
    - yellow = enabled + idle
    - red    = disabled or off/termination
    """
    if not settings.general.enabled:
        return EMOJI_RED
    state = settings.session.state
    if state == "idle":
        return EMOJI_YELLOW
    if state in ("off", "termination"):
        return EMOJI_RED
    return EMOJI_GREEN
