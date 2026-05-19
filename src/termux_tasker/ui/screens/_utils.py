from __future__ import annotations

import ast
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, cast

from termux_tasker.config import (
    RunnerMetadata,
    RunnerSettings,
    TaskMetadata,
    PropertyDef,
)
from termux_tasker.runner_process import RunnerProcess
from termux_tasker.ui.base.screen import LoadingScreen, InfoScreen

if TYPE_CHECKING:
    from textual.screen import Screen
    from termux_tasker.app import TermuxTaskerApp


GITHUB_URL_RE = re.compile(
    r"^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(\.git)?$"
)

VALID_ID_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_-]*$")


def sanitize_id(name: str) -> str:
    """Sanitize an arbitrary string for use as a Textual widget ID.

    Textual IDs must start with a letter or underscore and contain only
    alphanumerics, underscores, or hyphens.  Invalid characters are
    replaced with underscores.
    """
    result = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    if result and not result[0].isalpha() and result[0] != '_':
        result = '_' + result
    return result if result else "_"


def termux_app(screen: Screen) -> TermuxTaskerApp:
    return cast("TermuxTaskerApp", screen.app)


def clone_repo(
    url: str, tmp_dir: Path, prefix: str
) -> Optional[Path]:
    if not GITHUB_URL_RE.match(url):
        return None
    tmp_folder = tmp_dir / f"{prefix}_{uuid.uuid4().hex}"
    try:
        result = subprocess.run(
            ["git", "clone", url, str(tmp_folder)],
            capture_output=True, text=True, timeout=120,
        )
        return tmp_folder if result.returncode == 0 else None
    except subprocess.SubprocessError:
        return None


def copy_to_tmp(src: Path, tmp_dir: Path, prefix: str) -> Path:
    tmp_folder = tmp_dir / f"{prefix}_{uuid.uuid4().hex}"
    shutil.copytree(src, tmp_folder)
    return tmp_folder


def fetch_git_tags(
    repo_path: Path,
) -> tuple[list[str], str]:
    tags: list[str] = []
    main_branch = "main"

    try:
        result = subprocess.run(
            ["git", "tag", "--list"],
            capture_output=True, text=True, cwd=repo_path, timeout=30,
        )
        if result.stdout.strip():
            tags = result.stdout.strip().splitlines()

        branch_result = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            capture_output=True, text=True, cwd=repo_path, timeout=10,
        )
        if branch_result.returncode == 0:
            ref = branch_result.stdout.strip()
            main_branch = ref.split("/")[-1] if "/" in ref else "main"
    except subprocess.SubprocessError:
        pass

    return tags, main_branch


def git_checkout(repo_path: Path, tag: str) -> bool:
    try:
        subprocess.run(
            ["git", "checkout", tag],
            capture_output=True, text=True,
            cwd=repo_path, timeout=30, check=True,
        )
        return True
    except subprocess.SubprocessError:
        return False


def get_installed_runner_versions(
    runners_dir: Path, runner_id: str
) -> set[str]:
    versions: set[str] = set()
    if not runners_dir.exists():
        return versions
    for runner_dir in runners_dir.iterdir():
        if not runner_dir.is_dir():
            continue
        meta_path = runner_dir / "metadata.toml"
        if meta_path.exists():
            meta = RunnerMetadata.load(meta_path)
            if meta.general.id == runner_id:
                versions.add(meta.general.version)
    return versions


def get_installed_task_versions(
    tasks_dir: Path, task_id: str
) -> set[str]:
    versions: set[str] = set()
    if not tasks_dir.exists():
        return versions
    for task_dir in tasks_dir.iterdir():
        if not task_dir.is_dir():
            continue
        meta_path = task_dir / "metadata.toml"
        if meta_path.exists():
            meta = TaskMetadata.load(meta_path)
            if meta.general.id == task_id:
                versions.add(meta.general.version)
    return versions


def merge_runner_properties(
    old_settings: RunnerSettings,
    old_properties: list[PropertyDef],
    new_properties: list[PropertyDef],
) -> RunnerSettings:
    """Merge old property values into a new settings instance during version update.

    A value is preserved only when the **full signature** of the property
    (name + input_type + optional + options tuple) matches between the old
    and new definitions.  This prevents carrying over stale values for
    properties that changed type or options between versions.

    The ``general`` and ``session`` fields are carried over wholesale.
    """
    old_sigs = {
        (p.name, p.input_type, p.optional, tuple(p.options or []))
        for p in old_properties
    }
    new_settings = RunnerSettings()
    new_settings.general = old_settings.general
    new_settings.session = old_settings.session

    for p in new_properties:
        sig = (p.name, p.input_type, p.optional, tuple(p.options or []))
        if sig in old_sigs and p.name in old_settings.properties:
            new_settings.properties[p.name] = old_settings.properties[p.name]

    return new_settings


def fill_default_properties(
    settings_path: Path,
    properties: list[PropertyDef],
) -> None:
    """Fill in default values for properties that are missing from the settings.

    Only writes to disk if at least one property was actually filled
    (avoids unnecessary I/O on every install/update).
    """
    settings = RunnerSettings.load(settings_path)
    changed = False
    for prop in properties:
        if prop.name not in settings.properties and prop.default is not None:
            settings.properties[prop.name] = prop.default
            changed = True
    if changed:
        settings.save(settings_path)


def parse_property_value(raw: str, input_type: str) -> Any:
    """Deserialize a stored property value for the InputScreen.

    For checkboxes, tries ast.literal_eval first (supports Python list
    repr from ``str(result)``), then falls back to comma-splitting.
    Returns the raw string for text/radio inputs.
    """
    if input_type == "checkbox" and raw:
        try:
            parsed = ast.literal_eval(raw)
            if isinstance(parsed, list):
                return parsed
            return [parsed]
        except (ValueError, SyntaxError):
            return [v.strip() for v in raw.split(",")]
    return raw


def is_property_value_empty(result: Any, input_type: str) -> bool:
    """Check whether a property value is considered "empty".

    For checkboxes: an empty list/tuple.
    For text/radio: a blank string.
    """
    if input_type == "checkbox":
        return isinstance(result, (list, tuple)) and not result
    return isinstance(result, str) and not result.strip()
