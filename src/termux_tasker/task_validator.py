from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Optional

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from termux_tasker.config import TaskMetadata, RunnerMetadata, PropertyDef


TIMEOUT_RE = re.compile(r"^[0-9]+[hm]$")
GITHUB_URL_RE = re.compile(r"^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(\.git)?$")
TOML_KEY_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_-]*$")
TASK_ID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
VALID_INPUT_TYPES = {"text", "radio", "checkbox"}


class TaskValidatorException(Exception):
    def __init__(self, message: str, command: str = "", cause: str = "") -> None:
        self.message = message
        self.command = command
        self.cause = cause
        super().__init__(message)


class TaskValidator:
    """Validates a task's metadata and runs the runner's custom validators.

    Pipeline (called in sequence by validate()):
      1. validate_metadata_existed     — metadata.toml existence
      2. validate_metadata_structure    — field presence, format, timeout format
      3. check_runner_compatibility     — task's runner_id matches, version satisfies
      4. execute_runner_validators      — run the runner's custom shell validators
    """

    def __init__(self, runner_dir: Path, task_dir: Path, tmp_dir: Path) -> None:
        self.runner_dir = runner_dir
        self.task_dir = task_dir
        self.tmp_dir = tmp_dir
        self._metadata: Optional[TaskMetadata] = None
        self._runner_metadata: Optional[RunnerMetadata] = None

    def _is_git_repo(self, directory: Path) -> bool:
        return (directory / ".git").exists()

    def _get_git_tag(self, directory: Path) -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", "tag", "--points-at", "HEAD"],
                capture_output=True, text=True, cwd=directory, timeout=10,
            )
            tag = result.stdout.strip()
            return tag if tag else None
        except (subprocess.SubprocessError, FileNotFoundError):
            return None

    def validate_metadata_existed(self) -> None:
        task_meta_path = self.task_dir / "metadata.toml"
        if not task_meta_path.exists():
            raise TaskValidatorException(
                f"metadata.toml not found in {self.task_dir}"
            )

    def validate_metadata_essentials(self) -> None:
        meta = TaskMetadata.load(self.task_dir / "metadata.toml")
        if not meta.general.name:
            raise TaskValidatorException(
                f"task metadata.toml: [general].name is required and must be a non-empty string"
            )
        self._metadata = meta

    def validate_metadata_structure(self) -> None:
        path = self.task_dir / "metadata.toml"
        meta = TaskMetadata.load(path)
        self._metadata = meta

        general = meta.general

        if not general.id:
            raise TaskValidatorException(
                "task metadata.toml: [general].id is required and must be a non-empty string"
            )
        if not TASK_ID_RE.match(general.id):
            raise TaskValidatorException(
                f"task metadata.toml: [general].id '{general.id}' must consist of a-z, A-Z, 0-9, _, -"
            )

        if not general.name:
            raise TaskValidatorException(
                "task metadata.toml: [general].name is required and must be a non-empty string"
            )

        if not general.version:
            raise TaskValidatorException(
                "task metadata.toml: [general].version is required"
            )

        is_git = self._is_git_repo(self.task_dir)
        if is_git:
            try:
                Version(general.version)
            except Exception:
                raise TaskValidatorException(
                    f"task metadata.toml: [general].version '{general.version}' is not a valid semantic version"
                )
            tag = self._get_git_tag(self.task_dir)
            if tag and general.version != tag:
                raise TaskValidatorException(
                    f"task metadata.toml: [general].version '{general.version}' does not match git tag '{tag}'"
                )

        if is_git and not general.url:
            raise TaskValidatorException(
                "task metadata.toml: [general].url is required for git repositories"
            )
        if general.url and not GITHUB_URL_RE.match(general.url):
            raise TaskValidatorException(
                f"task metadata.toml: [general].url '{general.url}' is not a valid GitHub URL"
            )

        if not general.runner_id:
            raise TaskValidatorException(
                "task metadata.toml: [general].runner_id is required"
            )

        if not general.runner_min_version:
            raise TaskValidatorException(
                "task metadata.toml: [general].runner_min_version is required"
            )

        if not general.default_timeout:
            raise TaskValidatorException(
                "task metadata.toml: [general].default_timeout is required"
            )
        if not TIMEOUT_RE.match(general.default_timeout):
            raise TaskValidatorException(
                f"task metadata.toml: [general].default_timeout '{general.default_timeout}' "
                f"must be in format like '1h' or '30m'"
            )

        self._validate_properties(meta.properties)

    def _validate_properties(self, properties: list[PropertyDef]) -> None:
        for i, p in enumerate(properties):
            if not p.name:
                raise TaskValidatorException(
                    f"task metadata.toml: [[property]].{i}.name is required"
                )
            if not TOML_KEY_RE.match(p.name):
                raise TaskValidatorException(
                    f"task metadata.toml: [[property]].{i}.name '{p.name}' is not a valid TOML key"
                )
            if p.input_type not in VALID_INPUT_TYPES:
                raise TaskValidatorException(
                    f"task metadata.toml: [[property]].{i}.input-type '{p.input_type}' "
                    f"must be one of {VALID_INPUT_TYPES}"
                )
            if p.input_type in ("radio", "checkbox") and (not p.options or len(p.options) == 0):
                raise TaskValidatorException(
                    f"task metadata.toml: [[property]].{i}.options is required when "
                    f"input-type is '{p.input_type}'"
                )
            if p.default and p.input_type in ("radio", "checkbox") and p.options:
                if p.default not in p.options:
                    raise TaskValidatorException(
                        f"task metadata.toml: [[property]].{i}.default '{p.default}' "
                        f"must be one of options {p.options}"
                    )

    def check_runner_compatibility(self) -> None:
        if self._metadata is None:
            self.validate_metadata_existed()
            self.validate_metadata_structure()

        meta = self._metadata
        if meta is None:
            raise TaskValidatorException("Task metadata not loaded")

        runner_meta_path = self.runner_dir / "metadata.toml"
        if not runner_meta_path.exists():
            raise TaskValidatorException(
                f"Runner metadata not found at {runner_meta_path}"
            )
        runner_meta = RunnerMetadata.load(runner_meta_path)
        self._runner_metadata = runner_meta

        if meta.general.runner_id != runner_meta.general.id:
            raise TaskValidatorException(
                f"Task runner_id '{meta.general.runner_id}' does not match "
                f"runner id '{runner_meta.general.id}'"
            )

        try:
            spec = SpecifierSet(meta.general.runner_min_version)
            if not spec.contains(Version(runner_meta.general.version)):
                raise TaskValidatorException(
                    f"Runner version {runner_meta.general.version} does not satisfy "
                    f"requirement {meta.general.runner_min_version} from task "
                    f"'{meta.general.id}'"
                )
        except TaskValidatorException:
            raise
        except Exception as e:
            raise TaskValidatorException(
                f"Invalid version specifier '{meta.general.runner_min_version}': {e}"
            )

    def execute_runner_validators(self) -> None:
        """Run the runner's custom shell-based validators against the task.

        These are arbitrary shell commands defined in the runner's
        metadata.toml ([[task-validator]]).  Each command receives
        ``{task_dir}`` substituted with the task's path.  The task is
        considered invalid if any command returns a non-zero exit code.
        Stderr is captured and truncated to the last 5 lines for error
        reporting.

        Security note: the validator commands come from the runner that
        the user chose to install — they are not untrusted input.
        """
        if self._metadata is None:
            self.validate_metadata_existed()
            self.validate_metadata_structure()

        meta = self._metadata
        if meta is None:
            raise TaskValidatorException("Task metadata not loaded")

        runner_meta = self._runner_metadata
        if runner_meta is None:
            runner_meta_path = self.runner_dir / "metadata.toml"
            runner_meta = RunnerMetadata.load(runner_meta_path)
            self._runner_metadata = runner_meta

        self.tmp_dir.mkdir(parents=True, exist_ok=True)

        for i, tv in enumerate(runner_meta.task_validators):
            stdout_file = self.tmp_dir / "stdout"
            stderr_file = self.tmp_dir / "stderr"

            stdout_file.unlink(missing_ok=True)
            stderr_file.unlink(missing_ok=True)

            command = tv.command.replace("{task_dir}", str(self.task_dir))
            full_command = f"{command} > {stdout_file} 2> {stderr_file}"

            try:
                result = subprocess.run(
                    full_command, shell=True, capture_output=False,
                    cwd=self.runner_dir, timeout=60,
                )
                if result.returncode != 0:
                    cause = self._read_cause(stderr_file)
                    raise TaskValidatorException(
                        message=f"Task validator command failed with exit code {result.returncode}",
                        command=tv.command,
                        cause=cause,
                    )
            except TaskValidatorException:
                raise
            except subprocess.TimeoutExpired:
                raise TaskValidatorException(
                    message=f"Task validator command timed out",
                    command=tv.command,
                    cause="Command timed out",
                )
            except Exception as e:
                raise TaskValidatorException(
                    message=f"Task validator command failed: {e}",
                    command=tv.command,
                    cause=str(e),
                )

    def _read_cause(self, stderr_file: Path) -> str:
        if not stderr_file.exists():
            return ""
        lines = stderr_file.read_text().splitlines()
        if len(lines) <= 5:
            return "\n".join(lines)
        return "...\n" + "\n".join(lines[-5:])

    def validate(self) -> None:
        self.validate_metadata_existed()
        self.validate_metadata_structure()
        self.check_runner_compatibility()
        self.execute_runner_validators()
