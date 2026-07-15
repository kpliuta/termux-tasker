from __future__ import annotations

from pathlib import Path

from packaging.specifiers import SpecifierSet
from packaging.version import Version
from textual import on
from textual.widgets import Button

from termux_tasker.config import RunnerMetadata
from termux_tasker.ui.base import (
    MenuScreen,
    LoadingScreen,
    InfoScreen,
    ConfirmationScreen,
)
from termux_tasker.ui.screens._utils import (
    termux_app,
    fetch_git_tags,
    git_checkout,
    poetry_install,
    sanitize_id,
)


def _check_runners_app_compatibility(
    runners_path: Path, app_version: str
) -> list[tuple[str, str, str]]:
    """Check all installed runners against a candidate app version.

    Returns list of (runner_id, runner_name, app_min_version) for each
    incompatible runner.
    """
    incompatible: list[tuple[str, str, str]] = []
    if not runners_path.exists():
        return incompatible
    for runner_path in runners_path.iterdir():
        if not runner_path.is_dir():
            continue
        meta_path = runner_path / "metadata.toml"
        if not meta_path.exists():
            continue
        meta = RunnerMetadata.load(meta_path)
        try:
            spec = SpecifierSet(meta.general.app_min_version)
            if not spec.contains(Version(app_version)):
                incompatible.append((
                    meta.general.id,
                    meta.general.name,
                    meta.general.app_min_version,
                ))
        except Exception:
            pass
    return incompatible


class UpdateAppVersionScreen(MenuScreen):
    def __init__(self) -> None:
        self._id_to_tag: dict[str, str] = {}

        super().__init__({}, show_back_button=True)
        self.title = "App Version"
        self.sub_title = termux_app(self).state.app_version
        self._loaded = False

    def on_mount(self) -> None:
        if not self._loaded:
            self._loaded = True
            self.run_worker(self._load_versions())

    async def _load_versions(self) -> None:
        app = termux_app(self)
        app_root = app.state.app_root_path
        current_version = app.state.app_version

        loading = LoadingScreen("Fetching app versions")
        await termux_app(self).push_screen(loading)

        tags = fetch_git_tags(app_root)

        items: dict[str, str] = {}
        for tag in tags:
            label = tag
            if tag == current_version:
                label += " \\[Installed]"
            safe = sanitize_id(tag)
            self._id_to_tag[safe] = tag
            items[label] = f"version_{safe}"

        await loading.dismiss(None)
        self.menu_items = items

    @on(Button.Pressed)
    def on_version(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if not btn_id.startswith("version_"):
            return
        event.stop()
        safe = btn_id[8:]
        tag = self._id_to_tag.get(safe, safe)
        self.run_worker(self._do_update(tag))

    async def _do_update(self, tag: str) -> None:
        app = termux_app(self)
        loading = LoadingScreen(
            f"Checking runner compatibility with version {tag}"
        )
        await termux_app(self).push_screen(loading)

        incompatible = _check_runners_app_compatibility(
            app.state.runners_path, tag
        )

        await loading.dismiss(None)

        if incompatible:
            lines = [
                f"The following runners are not compatible with version {tag}:",
                "",
            ]
            for runner_id, runner_name, min_ver in incompatible:
                lines.append(f"- {runner_id} ({runner_name}) requires {min_ver}")
            lines.append("")
            lines.append("Please update these runners first.")

            await termux_app(self).push_screen(
                InfoScreen(
                    message="\n".join(lines),
                    severity="warning",
                )
            )
            return

        def on_confirm(result: str | None) -> None:
            if result is not None:
                self.run_worker(self._finalize_update(tag))

        await termux_app(self).push_screen(
            ConfirmationScreen(
                message=f"Are you sure you want to update app to version {tag}?",
                ok_button_text="Yes",
                cancel_button_text="No",
                ok_button_id="yes_update",
            ),
            on_confirm,
        )

    async def _finalize_update(self, tag: str) -> None:
        app = termux_app(self)
        app_root = app.state.app_root_path

        loading = LoadingScreen(f"Updating app to version {tag}")
        await termux_app(self).push_screen(loading)

        git_checkout(app_root, tag)

        poetry_install(app_root)

        await loading.dismiss(None)

        await termux_app(self).push_screen(
            InfoScreen(
                message=f"App updated to version {tag}. Please restart the app.",
                severity="info",
            )
        )
