from __future__ import annotations

from pathlib import Path

from termux_tasker.config import RunnerMetadata, RunnerSettings, TaskSettings


class SettingsHelper:
    """Encapsulates loading, saving and mutating settings for runners and tasks."""

    # ── Runner settings ─────────────────────────────────────────────────

    @staticmethod
    def load_runner_settings(runner_dir: Path) -> RunnerSettings:
        return RunnerSettings.load(runner_dir / "settings.toml")

    @staticmethod
    def save_runner_settings(runner_dir: Path, settings: RunnerSettings) -> None:
        settings.save(runner_dir / "settings.toml")

    @staticmethod
    def update_runner_settings(runner_dir: Path, **kwargs) -> RunnerSettings:
        settings = SettingsHelper.load_runner_settings(runner_dir)
        for key, value in kwargs.items():
            parts = key.split(".")
            obj = settings
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], value)
        SettingsHelper.save_runner_settings(runner_dir, settings)
        return settings

    @staticmethod
    def enable_runner(runner_dir: Path) -> RunnerSettings:
        return SettingsHelper.update_runner_settings(
            runner_dir, **{"general.enabled": True}
        )

    @staticmethod
    def disable_runner(runner_dir: Path) -> RunnerSettings:
        return SettingsHelper.update_runner_settings(
            runner_dir, **{"general.enabled": False}
        )

    @staticmethod
    def set_runner_state(runner_dir: Path, state: str) -> RunnerSettings:
        return SettingsHelper.update_runner_settings(
            runner_dir, **{"session.state": state}
        )

    @staticmethod
    def set_runner_property(runner_dir: Path, key: str, value: str) -> RunnerSettings:
        settings = SettingsHelper.load_runner_settings(runner_dir)
        settings.properties[key] = value
        SettingsHelper.save_runner_settings(runner_dir, settings)
        return settings

    @staticmethod
    def load_runner_metadata(runner_dir: Path) -> RunnerMetadata:
        return RunnerMetadata.load(runner_dir / "metadata.toml")

    # ── Task settings ───────────────────────────────────────────────────

    @staticmethod
    def load_task_settings(task_dir: Path) -> TaskSettings:
        return TaskSettings.load(task_dir / "settings.toml")

    @staticmethod
    def save_task_settings(task_dir: Path, settings: TaskSettings) -> None:
        settings.save(task_dir / "settings.toml")

    @staticmethod
    def update_task_settings(task_dir: Path, **kwargs) -> TaskSettings:
        settings = SettingsHelper.load_task_settings(task_dir)
        for key, value in kwargs.items():
            parts = key.split(".")
            obj = settings
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], value)
        SettingsHelper.save_task_settings(task_dir, settings)
        return settings

    @staticmethod
    def enable_task(task_dir: Path) -> TaskSettings:
        return SettingsHelper.update_task_settings(
            task_dir, **{"general.enabled": True}
        )

    @staticmethod
    def disable_task(task_dir: Path) -> TaskSettings:
        return SettingsHelper.update_task_settings(
            task_dir, **{"general.enabled": False}
        )

    @staticmethod
    def set_task_state(task_dir: Path, state: str) -> TaskSettings:
        return SettingsHelper.update_task_settings(
            task_dir, **{"session.state": state}
        )

    @staticmethod
    def toggle_task_enabled(task_dir: Path) -> TaskSettings:
        settings = SettingsHelper.load_task_settings(task_dir)
        settings.general.enabled = not settings.general.enabled
        SettingsHelper.save_task_settings(task_dir, settings)
        return settings

    @staticmethod
    def set_task_timeout(task_dir: Path, timeout: str) -> TaskSettings:
        return SettingsHelper.update_task_settings(
            task_dir, **{"general.timeout": timeout}
        )
