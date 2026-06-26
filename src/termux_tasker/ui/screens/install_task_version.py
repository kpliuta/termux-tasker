from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import Any

from textual import on
from textual.widgets import Button

from termux_tasker.config import (
    TaskMetadata,
    TaskSettings,
    PropertyDef,
)
from termux_tasker.task_validator import TaskValidator, TaskValidatorException
from termux_tasker.ui.base import (
    MenuScreen,
    LoadingScreen,
    InfoScreen,
    ConfirmationScreen,
    InputScreen,
)
from termux_tasker.ui.screens._utils import (
    termux_app,
    fetch_git_tags,
    git_checkout,
    get_installed_task_versions,
    merge_runner_properties,
    fill_default_properties,
    sanitize_id,
    is_property_value_empty,
)


class InstallTaskVersionScreen(MenuScreen):
    def __init__(self, runner_path: Path, tmp_task_folder: Path) -> None:
        self.runner_path = runner_path
        self.tmp_task_folder = tmp_task_folder
        meta = TaskMetadata.load(tmp_task_folder / "metadata.toml")
        self._task_meta = meta
        self._id_to_tag: dict[str, str] = {}

        super().__init__({}, show_back_button=True)
        self.title = "Task Version"
        self.sub_title = meta.general.name
        self._loaded = False

    def on_mount(self) -> None:
        if not self._loaded:
            self._loaded = True
            self.run_worker(self._load_versions())

    async def _load_versions(self) -> None:
        meta = self._task_meta
        tmp_folder = self.tmp_task_folder
        is_git = (tmp_folder / ".git").exists()

        installed_versions = get_installed_task_versions(
            self.runner_path / "tasks", meta.general.id
        )

        items: dict[str, str] = {}

        if is_git:
            loading = LoadingScreen(f"Fetching {meta.general.name} versions")
            await termux_app(self).push_screen(loading)

            tags, main_branch = fetch_git_tags(tmp_folder)

            main_label = main_branch
            if main_branch in installed_versions:
                main_label += " \\[Installed]"
            safe = sanitize_id(main_branch)
            self._id_to_tag[safe] = main_branch
            items[main_label] = f"version_{safe}"

            for tag in tags:
                label = tag
                if tag in installed_versions:
                    label += " \\[Installed]"
                safe = sanitize_id(tag)
                self._id_to_tag[safe] = tag
                items[label] = f"version_{safe}"

            await loading.dismiss(None)
        else:
            tag = meta.general.version
            label = tag
            if "local" in installed_versions:
                label += " \\[Installed]"
            safe = sanitize_id(tag)
            self._id_to_tag[safe] = tag
            items[label] = f"version_{safe}"

        self.menu_items = items

    @on(Button.Pressed)
    def on_version(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if not btn_id.startswith("version_"):
            return
        event.stop()
        safe = btn_id[8:]
        tag = self._id_to_tag.get(safe, safe)
        self.run_worker(self._do_install(tag))

    async def _do_install(self, tag: str) -> None:
        meta = self._task_meta
        tmp_folder = self.tmp_task_folder
        is_git = (tmp_folder / ".git").exists()

        loading = LoadingScreen(
            f"Validating {tag} version of {meta.general.name} task"
        )
        await termux_app(self).push_screen(loading)

        if is_git and tag not in ("main", "master"):
            if not git_checkout(tmp_folder, tag):
                await loading.dismiss(None)
                await termux_app(self).push_screen(
                    InfoScreen(
                        message=f"Failed to checkout tag '{tag}'",
                        severity="error",
                    )
                )
                return
            TaskMetadata.clear_cache(tmp_folder / "metadata.toml")

        app = termux_app(self)
        try:
            validator = TaskValidator(
                self.runner_path, tmp_folder, app.state.tmp_dir
            )
            validator.validate()
        except TaskValidatorException as e:
            await loading.dismiss(None)
            await termux_app(self).push_screen(InfoScreen(message=e.message, severity="error"))
            return

        await loading.dismiss(None)

        install_state = self._check_install_state(meta.general.id, tag)

        def on_confirm(result: str | None) -> None:
            if result is not None:
                self.run_worker(
                    self._finalize_install(meta.general.id, tag, install_state)
                )

        await termux_app(self).push_screen(
            ConfirmationScreen(
                message=(
                    f"Are you sure you want to {install_state} "
                    f"task version {tag}?"
                ),
                ok_button_text="Yes",
                cancel_button_text="No",
                ok_button_id="yes_install",
            ),
            on_confirm,
        )

    def _check_install_state(self, task_id: str, tag: str) -> str:
        tasks_path = self.runner_path / "tasks"
        if not tasks_path.exists():
            return "install"
        for task_path in tasks_path.iterdir():
            if not task_path.is_dir():
                continue
            meta_path = task_path / "metadata.toml"
            if meta_path.exists():
                meta = TaskMetadata.load(meta_path)
                if meta.general.id == task_id:
                    if meta.general.version == tag:
                        return "reinstall"
                    return "update"
        return "install"

    async def _finalize_install(
        self, task_id: str, _tag: str, install_state: str
    ) -> None:
        target_dir = self.runner_path / "tasks" / task_id
        meta = self._task_meta

        if install_state == "install":
            settings = TaskSettings()
            settings.general.timeout = meta.general.default_timeout
            settings.save(self.tmp_task_folder / "settings.toml")
        else:
            old_settings = TaskSettings.load(target_dir / "settings.toml")
            old_meta = TaskMetadata.load(target_dir / "metadata.toml")
            new_settings = merge_runner_properties(
                old_settings, old_meta.properties, meta.properties
            )
            new_settings.save(self.tmp_task_folder / "settings.toml")

        properties_to_ask = self._get_properties_to_prompt()
        if properties_to_ask:
            self._prompt_properties(properties_to_ask, 0, meta, target_dir)
        else:
            self._finish_install(meta, target_dir)

    def _get_properties_to_prompt(self) -> list[PropertyDef]:
        meta = self._task_meta
        to_ask: list[PropertyDef] = []
        for prop in meta.properties:
            if not prop.optional and prop.default is None:
                settings = TaskSettings.load(
                    self.tmp_task_folder / "settings.toml"
                )
                if prop.name not in settings.properties:
                    to_ask.append(prop)
        return to_ask

    def _prompt_properties(
        self,
        props: list[PropertyDef],
        index: int,
        meta: TaskMetadata,
        target_dir: Path,
    ) -> None:
        """Sequentially prompt the user for required / non-default properties.

        Recursively prompts each property; cancellation (Esc) skips to the
        next.  Required properties with empty values show a warning and
        re-prompt.  When all properties are done, calls _finish_install.
        """
        if index >= len(props):
            self._finish_install(meta, target_dir)
            return

        prop = props[index]

        def _next(idx: int = index) -> None:
            self._prompt_properties(props, idx, meta, target_dir)

        def _schedule_retry(_: object = None) -> None:
            asyncio.get_event_loop().call_soon(_next, index)

        def _skip_or_next(result: Any) -> None:
            if result is None:
                if prop.optional:
                    asyncio.get_event_loop().call_soon(_next, index + 1)
                    return
                termux_app(self).push_screen(
                    InfoScreen(
                        message=f"'{prop.name}' is required and must have a value.",
                        severity="warning",
                    ),
                    _schedule_retry,
                )
                return
            if not prop.optional and is_property_value_empty(result, prop.input_type):
                termux_app(self).push_screen(
                    InfoScreen(
                        message=f"'{prop.name}' is required and must have a value.",
                        severity="warning",
                    ),
                    _schedule_retry,
                )
                return
            settings = TaskSettings.load(self.tmp_task_folder / "settings.toml")
            if prop.input_type == "checkbox" and isinstance(result, (list, tuple)):
                settings.properties[prop.name] = ",".join(str(v) for v in result)
            else:
                settings.properties[prop.name] = str(result)
            settings.save(self.tmp_task_folder / "settings.toml")
            asyncio.get_event_loop().call_soon(_next, index + 1)

        termux_app(self).push_screen(
            InputScreen(
                title=prop.name,
                description=prop.description or "",
                input_type=prop.input_type,
                options=prop.options or [],
            ),
            _skip_or_next,
        )

    def _finish_install(
            self, meta: TaskMetadata, target_dir: Path
    ) -> None:
        """Finalize the task installation: persist, clear caches, navigate.

        1. Fill default property values.
        2. Replace the target directory with the temp copy.
        3. Clear config caches so fresh files are loaded on next access.
        4. Pop the screen stack back to the RunnerMenuScreen.
        5. Push the TaskMenuScreen for the newly installed task.
        """
        from termux_tasker.ui.screens.runner_menu import RunnerMenuScreen
        from termux_tasker.ui.screens.task_menu import TaskMenuScreen

        fill_default_properties(
            self.tmp_task_folder / "settings.toml", meta.properties
        )

        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(self.tmp_task_folder, target_dir)

        TaskSettings.clear_cache(target_dir / "settings.toml")
        TaskMetadata.clear_cache(target_dir / "metadata.toml")

        while not isinstance(termux_app(self).screen, RunnerMenuScreen):
            termux_app(self).pop_screen()

        termux_app(self).push_screen(TaskMenuScreen(target_dir))
