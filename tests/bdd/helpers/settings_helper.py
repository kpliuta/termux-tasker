from __future__ import annotations

from pathlib import Path

from termux_tasker.config import RunnerMetadata, RunnerSettings, TaskSettings


def load_runner_settings(runner_dir: Path) -> RunnerSettings:
    return RunnerSettings.load(runner_dir / "settings.toml")


def save_runner_settings(runner_dir: Path, settings: RunnerSettings) -> None:
    settings.save(runner_dir / "settings.toml")


def update_runner_settings(runner_dir: Path, **kwargs: object) -> RunnerSettings:
    settings = load_runner_settings(runner_dir)
    for key, value in kwargs.items():
        parts = key.split(".")
        obj = settings
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)
    save_runner_settings(runner_dir, settings)
    return settings


def enable_runner(runner_dir: Path) -> RunnerSettings:
    return update_runner_settings(runner_dir, **{"general.enabled": True})


def disable_runner(runner_dir: Path) -> RunnerSettings:
    return update_runner_settings(runner_dir, **{"general.enabled": False})


def set_runner_state(runner_dir: Path, state: str) -> RunnerSettings:
    return update_runner_settings(runner_dir, **{"session.state": state})


def set_runner_property(runner_dir: Path, key: str, value: str) -> RunnerSettings:
    settings = load_runner_settings(runner_dir)
    settings.properties[key] = value
    save_runner_settings(runner_dir, settings)
    return settings


def load_runner_metadata(runner_dir: Path) -> RunnerMetadata:
    return RunnerMetadata.load(runner_dir / "metadata.toml")


def load_task_settings(task_dir: Path) -> TaskSettings:
    return TaskSettings.load(task_dir / "settings.toml")


def save_task_settings(task_dir: Path, settings: TaskSettings) -> None:
    settings.save(task_dir / "settings.toml")


def update_task_settings(task_dir: Path, **kwargs: object) -> TaskSettings:
    settings = load_task_settings(task_dir)
    for key, value in kwargs.items():
        parts = key.split(".")
        obj = settings
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)
    save_task_settings(task_dir, settings)
    return settings


def enable_task(task_dir: Path) -> TaskSettings:
    return update_task_settings(task_dir, **{"general.enabled": True})


def disable_task(task_dir: Path) -> TaskSettings:
    return update_task_settings(task_dir, **{"general.enabled": False})


def set_task_state(task_dir: Path, state: str) -> TaskSettings:
    return update_task_settings(task_dir, **{"session.state": state})


def toggle_task_enabled(task_dir: Path) -> TaskSettings:
    settings = load_task_settings(task_dir)
    settings.general.enabled = not settings.general.enabled
    save_task_settings(task_dir, settings)
    return settings


def set_task_timeout(task_dir: Path, timeout: str) -> TaskSettings:
    return update_task_settings(task_dir, **{"general.timeout": timeout})
