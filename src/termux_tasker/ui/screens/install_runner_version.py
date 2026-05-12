from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import Any

from textual import on
from textual.widgets import Button

from termux_tasker.config import (
    RunnerMetadata,
    RunnerSettings,
    PropertyDef,
)
from termux_tasker.runner_validator import RunnerValidator, RunnerValidatorException
from termux_tasker.ui.base.screen import (
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
    get_installed_runner_versions,
    merge_runner_properties,
    fill_default_properties,
    sanitize_id,
    is_property_value_empty,
)


class InstallRunnerVersionScreen(MenuScreen):
    def __init__(self, tmp_runner_folder: Path) -> None:
        self.tmp_runner_folder = tmp_runner_folder
        meta = RunnerMetadata.load(tmp_runner_folder / "metadata.toml")
        self._runner_meta = meta
        self._id_to_tag: dict[str, str] = {}

        super().__init__({}, show_back_button=True)
        self.title = "Runner Version"
        self.sub_title = meta.general.name
        self._loaded = False

    def on_mount(self) -> None:
        if not self._loaded:
            self._loaded = True
            self.run_worker(self._load_versions())

    async def _load_versions(self) -> None:
        meta = self._runner_meta
        tmp_folder = self.tmp_runner_folder
        is_git = (tmp_folder / ".git").exists()

        app = termux_app(self)
        installed_versions = get_installed_runner_versions(
            app.state.runners_dir, meta.general.id
        )

        items: dict[str, str] = {}

        if is_git:
            loading = LoadingScreen(f"Fetching {meta.general.name} versions")
            self.app.push_screen(loading)
            await asyncio.sleep(0)

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

            loading.dismiss(None)
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
        meta = self._runner_meta
        tmp_folder = self.tmp_runner_folder
        is_git = (tmp_folder / ".git").exists()

        loading = LoadingScreen(
            f"Validating {tag} version of {meta.general.name} runner"
        )
        self.app.push_screen(loading)
        await asyncio.sleep(0)

        if is_git and tag not in ("main", "master"):
            if not git_checkout(tmp_folder, tag):
                loading.dismiss(None)
                self.app.push_screen(
                    InfoScreen(
                        message=f"Failed to checkout tag '{tag}'",
                        severity="error",
                    )
                )
                return

        app = termux_app(self)
        try:
            validator = RunnerValidator(tmp_folder, app_version=app.state.app_version)
            validator.validate()
        except RunnerValidatorException as e:
            loading.dismiss(None)
            self.app.push_screen(InfoScreen(message=e.message, severity="error"))
            return

        loading.dismiss(None)

        install_state = self._check_install_state(meta.general.id, tag)

        def on_confirm(result: str | None) -> None:
            if result is not None:
                self.run_worker(
                    self._finalize_install(meta.general.id, tag, install_state)
                )

        self.app.push_screen(
            ConfirmationScreen(
                message=(
                    f"Are you sure you want to {install_state} "
                    f"runner version {tag}?"
                ),
                ok_button_text="Yes",
                cancel_button_text="No",
                ok_button_id="yes_install",
            ),
            on_confirm,
        )

    def _check_install_state(self, runner_id: str, tag: str) -> str:
        app = termux_app(self)
        for runner_dir in app.state.runners_dir.iterdir():
            if not runner_dir.is_dir():
                continue
            meta_path = runner_dir / "metadata.toml"
            if meta_path.exists():
                meta = RunnerMetadata.load(meta_path)
                if meta.general.id == runner_id:
                    if meta.general.version == tag:
                        return "reinstall"
                    return "update"
        return "install"

    async def _finalize_install(
        self, runner_id: str, tag: str, install_state: str
    ) -> None:
        app = termux_app(self)
        target_dir = app.state.runners_dir / runner_id
        meta = self._runner_meta

        (self.tmp_runner_folder / "tasks").mkdir(exist_ok=True)

        if install_state == "install":
            settings = RunnerSettings()
            settings.save(self.tmp_runner_folder / "settings.toml")
        else:
            old_settings = RunnerSettings.load(target_dir / "settings.toml")
            old_meta = RunnerMetadata.load(target_dir / "metadata.toml")
            new_settings = merge_runner_properties(
                old_settings, old_meta.properties, meta.properties
            )
            new_settings.save(self.tmp_runner_folder / "settings.toml")

        properties_to_ask = self._get_properties_to_prompt()
        if properties_to_ask:
            self._prompt_properties(properties_to_ask, 0, meta, target_dir)
        else:
            self._finish_install(meta, target_dir)

    def _get_properties_to_prompt(self) -> list[PropertyDef]:
        meta = self._runner_meta
        to_ask: list[PropertyDef] = []
        for prop in meta.properties:
            if not prop.optional and prop.default is None:
                settings = RunnerSettings.load(
                    self.tmp_runner_folder / "settings.toml"
                )
                if prop.name not in settings.properties:
                    to_ask.append(prop)
        return to_ask

    def _prompt_properties(
        self,
        props: list[PropertyDef],
        index: int,
        meta: RunnerMetadata,
        target_dir: Path,
    ) -> None:
        if index >= len(props):
            self._finish_install(meta, target_dir)
            return

        prop = props[index]

        def on_result(result: Any) -> None:
            if result is None:
                self._prompt_properties(props, index + 1, meta, target_dir)
                return
            if is_property_value_empty(result, prop.input_type):
                self.app.push_screen(
                    InfoScreen(
                        message=f"'{prop.name}' is required and must have a value.",
                        severity="warning",
                    ),
                    lambda _: self._prompt_properties(props, index, meta, target_dir),
                )
                return
            settings = RunnerSettings.load(
                self.tmp_runner_folder / "settings.toml"
            )
            if prop.input_type == "checkbox" and isinstance(result, (list, tuple)):
                settings.properties[prop.name] = ",".join(str(v) for v in result)
            else:
                settings.properties[prop.name] = str(result)
            settings.save(self.tmp_runner_folder / "settings.toml")
            self._prompt_properties(props, index + 1, meta, target_dir)

        self.app.push_screen(
            InputScreen(
                title=prop.name,
                description=prop.description or "",
                input_type=prop.input_type,
                options=prop.options or [],
            ),
            on_result,
        )

    def _finish_install(
            self, meta: RunnerMetadata, target_dir: Path
    ) -> None:
        from termux_tasker.ui.screens.runner_menu import RunnerMenuScreen
        from termux_tasker.ui.screens.runners_screen import RunnersScreen

        fill_default_properties(
            self.tmp_runner_folder / "settings.toml", meta.properties
        )

        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(self.tmp_runner_folder, target_dir)

        RunnerSettings.clear_cache(target_dir / "settings.toml")
        RunnerMetadata.clear_cache(target_dir / "metadata.toml")

        while not isinstance(self.app.screen, RunnersScreen):
            self.app.pop_screen()

        self.app.push_screen(RunnerMenuScreen(target_dir))
