from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from termux_tasker.config import RunnerMetadata, BundledTasks, PropertyDef


GITHUB_URL_RE = re.compile(r"^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(\.git)?$")
TOML_KEY_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_-]*$")
RUNNER_ID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
VALID_INPUT_TYPES = {"text", "radio", "checkbox"}


class RunnerValidatorException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class RunnerValidator:
    def __init__(self, runner_dir: Path, app_version: str = "0.1.0") -> None:
        self.runner_dir = runner_dir
        self.app_version = app_version
        self._metadata: Optional[RunnerMetadata] = None

    def _is_git_repo(self) -> bool:
        return (self.runner_dir / ".git").exists()

    def _get_git_tag(self) -> Optional[str]:
        import subprocess
        try:
            result = subprocess.run(
                ["git", "tag", "--points-at", "HEAD"],
                capture_output=True, text=True, cwd=self.runner_dir, timeout=10,
            )
            tag = result.stdout.strip()
            return tag if tag else None
        except (subprocess.SubprocessError, FileNotFoundError):
            return None

    def validate_metadata_existed(self) -> None:
        if not (self.runner_dir / "metadata.toml").exists():
            raise RunnerValidatorException(
                f"metadata.toml not found in {self.runner_dir}"
            )

    def validate_metadata_essentials(self) -> None:
        meta = RunnerMetadata.load(self.runner_dir / "metadata.toml")
        if not meta.general.name:
            raise RunnerValidatorException(
                f"metadata.toml: [general].name is required and must be a non-empty string"
            )
        self._metadata = meta

    def validate_metadata_structure(self) -> None:
        path = self.runner_dir / "metadata.toml"
        meta = RunnerMetadata.load(path)
        self._metadata = meta

        general = meta.general

        # [general] id: required, valid pattern
        if not general.id:
            raise RunnerValidatorException(
                "metadata.toml: [general].id is required and must be a non-empty string"
            )
        if not RUNNER_ID_RE.match(general.id):
            raise RunnerValidatorException(
                f"metadata.toml: [general].id '{general.id}' must consist of a-z, A-Z, 0-9, _, -"
            )

        # [general] name: required
        if not general.name:
            raise RunnerValidatorException(
                "metadata.toml: [general].name is required and must be a non-empty string"
            )

        # [general] version: required
        if not general.version:
            raise RunnerValidatorException(
                "metadata.toml: [general].version is required"
            )

        is_git = self._is_git_repo()
        if is_git:
            try:
                Version(general.version)
            except Exception:
                raise RunnerValidatorException(
                    f"metadata.toml: [general].version '{general.version}' is not a valid semantic version"
                )
            tag = self._get_git_tag()
            if tag and general.version != tag:
                raise RunnerValidatorException(
                    f"metadata.toml: [general].version '{general.version}' does not match git tag '{tag}'"
                )

        # [general] url: required if git repo
        if is_git and not general.url:
            raise RunnerValidatorException(
                "metadata.toml: [general].url is required for git repositories"
            )
        if general.url and not GITHUB_URL_RE.match(general.url):
            raise RunnerValidatorException(
                f"metadata.toml: [general].url '{general.url}' is not a valid GitHub URL"
            )

        # [general] app_min_version: required
        if not general.app_min_version:
            raise RunnerValidatorException(
                "metadata.toml: [general].app_min_version is required"
            )

        # Validate properties
        self._validate_properties(meta.properties)

        # Validate task-validators
        for i, tv in enumerate(meta.task_validators):
            if not tv.command:
                raise RunnerValidatorException(
                    f"metadata.toml: [[task-validator]].{i}.command is required"
                )
            if "{task_dir}" not in tv.command:
                raise RunnerValidatorException(
                    f"metadata.toml: [[task-validator]].{i}.command '{tv.command}' "
                    f"must contain {{task_dir}} placeholder"
                )

        # [exec] validation
        if not meta.exec.task_exec:
            raise RunnerValidatorException(
                "metadata.toml: [exec].task-exec is required"
            )
        if "{task_dir}" not in meta.exec.task_exec:
            raise RunnerValidatorException(
                "metadata.toml: [exec].task-exec must contain {task_dir} placeholder"
            )

    def _validate_properties(self, properties: list[PropertyDef]) -> None:
        for i, p in enumerate(properties):
            if not p.name:
                raise RunnerValidatorException(
                    f"metadata.toml: [[property]].{i}.name is required"
                )
            if not TOML_KEY_RE.match(p.name):
                raise RunnerValidatorException(
                    f"metadata.toml: [[property]].{i}.name '{p.name}' is not a valid TOML key"
                )
            if p.input_type not in VALID_INPUT_TYPES:
                raise RunnerValidatorException(
                    f"metadata.toml: [[property]].{i}.input-type '{p.input_type}' "
                    f"must be one of {VALID_INPUT_TYPES}"
                )
            if p.input_type in ("radio", "checkbox") and (not p.options or len(p.options) == 0):
                raise RunnerValidatorException(
                    f"metadata.toml: [[property]].{i}.options is required when "
                    f"input-type is '{p.input_type}'"
                )
            if p.default and p.input_type in ("radio", "checkbox") and p.options:
                if p.default not in p.options:
                    raise RunnerValidatorException(
                        f"metadata.toml: [[property]].{i}.default '{p.default}' "
                        f"must be one of options {p.options}"
                    )

    def validate_bundled_structure(self) -> None:
        bundled_path = self.runner_dir / "bundled.toml"
        if not bundled_path.exists():
            return

        bundled = BundledTasks.load(bundled_path)
        for i, task in enumerate(bundled.tasks):
            if not task.url:
                raise RunnerValidatorException(
                    f"bundled.toml: [[tasks]].{i}.url is required"
                )
            if not GITHUB_URL_RE.match(task.url):
                raise RunnerValidatorException(
                    f"bundled.toml: [[tasks]].{i}.url '{task.url}' is not a valid GitHub URL"
                )

    def check_app_compatibility(self) -> None:
        if self._metadata is None:
            self.validate_metadata_existed()
            self.validate_metadata_structure()

        meta = self._metadata
        if meta is None:
            raise RunnerValidatorException("Metadata not loaded")
        try:
            spec = SpecifierSet(meta.general.app_min_version)
            if not spec.contains(Version(self.app_version)):
                raise RunnerValidatorException(
                    f"Application version {self.app_version} does not satisfy "
                    f"requirement {meta.general.app_min_version} from "
                    f"runner '{meta.general.id}'"
                )
        except RunnerValidatorException:
            raise
        except Exception as e:
            raise RunnerValidatorException(
                f"Invalid version specifier '{meta.general.app_min_version}': {e}"
            )

    def validate(self) -> None:
        self.validate_metadata_existed()
        self.validate_metadata_structure()
        self.validate_bundled_structure()
        self.check_app_compatibility()
