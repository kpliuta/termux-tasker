"""General-purpose helpers for runners, tasks, and the app.

This module collects low-level, non-UI utilities used across the project:
git operations (tag fetching/checkout), filesystem and temp-dir handling,
id sanitization/dedup, property-value (de)serialization, etc.

It deliberately contains **no Textual screen logic** — anything that pushes
or drives screens (e.g. interactive input prompts) lives in
``termux_tasker.ui.screens._ui_utils`` instead.
"""

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


def make_unique(safe_id: str, taken: set[str]) -> str:
    """Return *safe_id*, or a ``_2``/``_3``… suffixed variant not in *taken*.

    The returned id is registered in *taken*.  Used when generating
    widget ids from external data (e.g. git tags) where two distinct
    values can sanitize to the same identifier.
    """
    candidate = safe_id
    counter = 2
    while candidate in taken:
        candidate = f"{safe_id}_{counter}"
        counter += 1
    taken.add(candidate)
    return candidate


def termux_app(screen: Screen[Any]) -> TermuxTaskerApp:
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


def fetch_git_tags(repo_path: Path) -> list[str]:
    """List the tags of the git repo at ``repo_path``.

    First tries ``git fetch --tags`` (best-effort) so versions released
    after the local clone are picked up too.  If the fetch fails — no
    remote, offline, or not a git repo — we fall back to whatever tags
    already exist locally.
    """
    try:
        subprocess.run(
            ["git", "fetch", "--tags", "--quiet"],
            capture_output=True, text=True, cwd=repo_path, timeout=60,
        )
    except subprocess.SubprocessError:
        pass

    tags: list[str] = []
    try:
        result = subprocess.run(
            ["git", "tag", "--list"],
            capture_output=True, text=True, cwd=repo_path, timeout=30,
        )
        if result.stdout.strip():
            tags = result.stdout.strip().splitlines()
    except subprocess.SubprocessError:
        pass
    return tags


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


def poetry_install(repo_path: Path) -> bool:
    try:
        subprocess.run(
            ["poetry", "install", "--only", "main"],
            capture_output=True, text=True, cwd=repo_path, timeout=120,
        )
        return True
    except subprocess.SubprocessError:
        return False


def get_installed_runner_version(
    runners_path: Path, runner_id: str
) -> Optional[str]:
    if not runners_path.exists():
        return None
    target = runners_path / runner_id
    meta_path = target / "metadata.toml"
    if meta_path.exists():
        meta = RunnerMetadata.load(meta_path)
        if meta.general.id == runner_id:
            return meta.general.version
    return None


def get_installed_task_version(
    tasks_path: Path, task_id: str
) -> Optional[str]:
    if not tasks_path.exists():
        return None
    target = tasks_path / task_id
    meta_path = target / "metadata.toml"
    if meta_path.exists():
        meta = TaskMetadata.load(meta_path)
        if meta.general.id == task_id:
            return meta.general.version
    return None


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
    old_signatures = {
        (p.name, p.input_type, p.optional, tuple(p.options or []))
        for p in old_properties
    }
    new_settings = RunnerSettings()
    new_settings.general = old_settings.general
    new_settings.session = old_settings.session

    for p in new_properties:
        sig = (p.name, p.input_type, p.optional, tuple(p.options or []))
        if sig in old_signatures and p.name in old_settings.properties:
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
