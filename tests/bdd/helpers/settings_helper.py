from __future__ import annotations

from pathlib import Path

from termux_tasker.config import RunnerMetadata, RunnerSettings, TaskSettings


def load_runner_settings(runner_path: Path) -> RunnerSettings:
    return RunnerSettings.load(runner_path / "settings.toml")


def save_runner_settings(runner_path: Path, settings: RunnerSettings) -> None:
    settings.save(runner_path / "settings.toml")


def update_runner_settings(runner_path: Path, **kwargs: object) -> RunnerSettings:
    settings = load_runner_settings(runner_path)
    for key, value in kwargs.items():
        parts = key.split(".")
        obj = settings
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)
    save_runner_settings(runner_path, settings)
    return settings


def enable_runner(runner_path: Path) -> RunnerSettings:
    return update_runner_settings(runner_path, **{"general.enabled": True})


def disable_runner(runner_path: Path) -> RunnerSettings:
    return update_runner_settings(runner_path, **{"general.enabled": False})


def set_runner_state(runner_path: Path, state: str) -> RunnerSettings:
    return update_runner_settings(runner_path, **{"session.state": state})


def set_runner_property(runner_path: Path, key: str, value: str) -> RunnerSettings:
    settings = load_runner_settings(runner_path)
    settings.properties[key] = value
    save_runner_settings(runner_path, settings)
    return settings


def load_runner_metadata(runner_path: Path) -> RunnerMetadata:
    return RunnerMetadata.load(runner_path / "metadata.toml")


def load_task_settings(task_path: Path) -> TaskSettings:
    return TaskSettings.load(task_path / "settings.toml")


def save_task_settings(task_path: Path, settings: TaskSettings) -> None:
    settings.save(task_path / "settings.toml")


def update_task_settings(task_path: Path, **kwargs: object) -> TaskSettings:
    settings = load_task_settings(task_path)
    for key, value in kwargs.items():
        parts = key.split(".")
        obj = settings
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)
    save_task_settings(task_path, settings)
    return settings


def enable_task(task_path: Path) -> TaskSettings:
    return update_task_settings(task_path, **{"general.enabled": True})


def disable_task(task_path: Path) -> TaskSettings:
    return update_task_settings(task_path, **{"general.enabled": False})


def set_task_state(task_path: Path, state: str) -> TaskSettings:
    return update_task_settings(task_path, **{"session.state": state})


def toggle_task_enabled(task_path: Path) -> TaskSettings:
    settings = load_task_settings(task_path)
    settings.general.enabled = not settings.general.enabled
    save_task_settings(task_path, settings)
    return settings


def set_task_timeout(task_path: Path, timeout: str) -> TaskSettings:
    return update_task_settings(task_path, **{"general.timeout": timeout})
