from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Optional

import tomlkit
from tomlkit.items import Table


def _write_toml(path: Path, doc: tomlkit.TOMLDocument) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tomlkit.dumps(doc))


def _properties_to_table(props: dict[str, str]) -> Table:
    t = tomlkit.table()
    for k, v in props.items():
        t[k] = v
    return t


# --- App Config ---

@dataclass
class AppSettingsTermux:
    upgrade_on_startup: bool = False


@dataclass
class AppConfig:
    settings: AppSettingsTermux = field(default_factory=AppSettingsTermux)

    @classmethod
    def load(cls, path: Path) -> AppConfig:
        if not path.exists():
            return cls()
        doc = tomlkit.parse(path.read_text())
        cfg = cls()
        settings_table = doc.get("settings", {})
        termux_table = settings_table.get("termux", {}) if isinstance(settings_table, dict) else {}
        if isinstance(termux_table, dict):
            cfg.settings.upgrade_on_startup = termux_table.get("upgrade-on-startup", False)
        return cfg

    def save(self, path: Path) -> None:
        doc = tomlkit.document()
        settings = tomlkit.table()
        termux = tomlkit.table()
        termux["upgrade-on-startup"] = self.settings.upgrade_on_startup
        settings["termux"] = termux
        doc["settings"] = settings
        _write_toml(path, doc)


# --- Property Definition ---

@dataclass
class PropertyDef:
    name: str
    description: Optional[str] = None
    input_type: str = "text"
    optional: bool = True
    options: Optional[list[str]] = None
    default: Optional[str] = None


def _parse_properties(items) -> list[PropertyDef]:
    """Convert TOML [[property]] array items to PropertyDef dataclasses."""
    result = []
    for item in items:
        result.append(PropertyDef(
            name=str(item.get("name", "")),
            description=str(item["description"]) if item.get("description") else None,
            input_type=str(item.get("input-type", "text")),
            optional=bool(item.get("optional", True)),
            options=[str(o) for o in item.get("options", [])] if item.get("options") else None,
            default=str(item["default"]) if item.get("default") else None,
        ))
    return result


# --- Runner Metadata ---

@dataclass
class TaskValidatorDef:
    command: str
    description: Optional[str] = None


@dataclass
class ExecDef:
    initialization: Optional[str] = None
    before_exec: Optional[str] = None
    before_task: Optional[str] = None
    task_exec: Optional[str] = None
    after_task: Optional[str] = None
    after_exec: Optional[str] = None
    termination: Optional[str] = None


@dataclass
class RunnerGeneral:
    id: str = ""
    name: str = ""
    description: Optional[str] = None
    version: str = "0.1.0"
    url: Optional[str] = None
    app_min_version: str = "0.1.0"


@dataclass
class RunnerMetadata:
    """Runner definition loaded from metadata.toml.

    Uses class-level instance caching (_instances) keyed by file path.
    Loading the same .toml multiple times returns the cached object,
    avoiding repeated disk I/O. Explicitly call clear_cache(path) after
    replacing the file on disk (e.g. after install/update).
    """
    _instances: ClassVar[dict[Path, RunnerMetadata]] = {}

    general: RunnerGeneral = field(default_factory=RunnerGeneral)
    properties: list[PropertyDef] = field(default_factory=list)
    task_validators: list[TaskValidatorDef] = field(default_factory=list)
    exec: ExecDef = field(default_factory=ExecDef)

    @classmethod
    def load(cls, path: Path) -> RunnerMetadata:
        if path in cls._instances:
            return cls._instances[path]
        doc = tomlkit.parse(path.read_text())
        result = cls()

        general_table = doc.get("general", {})
        if isinstance(general_table, dict):
            id_val = general_table.get("id", "")
            name_val = general_table.get("name", "")
            description_val = str(general_table["description"]) if general_table.get("description") else None
            version_val = general_table.get("version", None)
            url_val = str(general_table["url"]) if general_table.get("url") else None
            app_min_version_val = general_table.get("app_min_version", None)
            result.general = RunnerGeneral(
                id=str(id_val) if id_val is not None else "",
                name=str(name_val) if name_val is not None else "",
                description=description_val,
                version=str(version_val) if version_val is not None else "",
                url=url_val,
                app_min_version=str(app_min_version_val) if app_min_version_val is not None else "",
            )

        if "property" in doc:
            result.properties = _parse_properties(doc["property"])

        if "task-validator" in doc:
            for item in doc["task-validator"]:
                result.task_validators.append(TaskValidatorDef(
                    command=str(item.get("command", "")),
                    description=str(item["description"]) if item.get("description") else None,
                ))

        exec_table = doc.get("exec", {})
        if isinstance(exec_table, dict):
            result.exec = ExecDef(
                initialization=str(exec_table["initialization"]) if exec_table.get("initialization") else None,
                before_exec=str(exec_table["before-exec"]) if exec_table.get("before-exec") else None,
                before_task=str(exec_table["before-task"]) if exec_table.get("before-task") else None,
                task_exec=str(exec_table["task-exec"]) if exec_table.get("task-exec") else None,
                after_task=str(exec_table["after-task"]) if exec_table.get("after-task") else None,
                after_exec=str(exec_table["after-exec"]) if exec_table.get("after-exec") else None,
                termination=str(exec_table["termination"]) if exec_table.get("termination") else None,
            )

        cls._instances[path] = result
        return result

    def save(self, path: Path) -> None:
        doc = tomlkit.document()

        general = tomlkit.table()
        general["id"] = self.general.id
        general["name"] = self.general.name
        if self.general.description:
            general["description"] = self.general.description
        general["version"] = self.general.version
        if self.general.url:
            general["url"] = self.general.url
        general["app_min_version"] = self.general.app_min_version
        doc["general"] = general

        if self.properties:
            arr = tomlkit.array()
            for p in self.properties:
                t = tomlkit.table()
                t["name"] = p.name
                if p.description:
                    t["description"] = p.description
                t["input-type"] = p.input_type
                t["optional"] = p.optional
                if p.options:
                    t["options"] = p.options
                if p.default:
                    t["default"] = p.default
                arr.append(t)
            doc["property"] = arr

        if self.task_validators:
            arr = tomlkit.array()
            for tv in self.task_validators:
                t = tomlkit.table()
                t["command"] = tv.command
                if tv.description:
                    t["description"] = tv.description
                arr.append(t)
            doc["task-validator"] = arr

        # Map Python snake_case attr names to TOML kebab-case keys
        exec_table = tomlkit.table()
        for attr, key in [
            ("initialization", "initialization"),
            ("before_exec", "before-exec"),
            ("before_task", "before-task"),
            ("task_exec", "task-exec"),
            ("after_task", "after-task"),
            ("after_exec", "after-exec"),
            ("termination", "termination"),
        ]:
            val = getattr(self.exec, attr, None)
            if val:
                exec_table[key] = val
        doc["exec"] = exec_table

        _write_toml(path, doc)
        # Use type(self) instead of cls so that TaskSettings = RunnerSettings
        # alias updates the correct shared _instances dict
        type(self)._instances[path] = self

    @classmethod
    def clear_cache(cls, path: Path) -> None:
        """Explicitly evict a cached entry.

        Must be called after replacing the file on disk
        (e.g. after shutil.copytree in install flows), otherwise
        load() will return the stale cached object.
        """
        cls._instances.pop(path, None)


@dataclass
class TaskGeneral:
    id: str = ""
    name: str = ""
    description: Optional[str] = None
    version: str = "0.1.0"
    url: Optional[str] = None
    runner_id: str = ""
    runner_min_version: str = "0.1.0"
    default_timeout: str = "1h"


@dataclass
class TaskMetadata:
    """Task definition loaded from metadata.toml.

    Same class-level caching mechanism as RunnerMetadata.
    """

    _instances: ClassVar[dict[Path, TaskMetadata]] = {}

    general: TaskGeneral = field(default_factory=TaskGeneral)
    properties: list[PropertyDef] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> TaskMetadata:
        if path in cls._instances:
            return cls._instances[path]
        doc = tomlkit.parse(path.read_text())
        result = cls()

        general_table = doc.get("general", {})
        if isinstance(general_table, dict):
            id_val = general_table.get("id", "")
            name_val = general_table.get("name", "")
            description_val = str(general_table["description"]) if general_table.get("description") else None
            version_val = general_table.get("version", None)
            url_val = str(general_table["url"]) if general_table.get("url") else None
            runner_id_val = general_table.get("runner_id", "")
            runner_min_version_val = general_table.get("runner_min_version", None)
            default_timeout_val = general_table.get("default_timeout", None)
            result.general = TaskGeneral(
                id=str(id_val) if id_val is not None else "",
                name=str(name_val) if name_val is not None else "",
                description=description_val,
                version=str(version_val) if version_val is not None else "",
                url=url_val,
                runner_id=str(runner_id_val) if runner_id_val is not None else "",
                runner_min_version=str(runner_min_version_val) if runner_min_version_val is not None else "",
                default_timeout=str(default_timeout_val) if default_timeout_val is not None else "",
            )

        if "property" in doc:
            result.properties = _parse_properties(doc["property"])

        cls._instances[path] = result
        return result

    def save(self, path: Path) -> None:
        doc = tomlkit.document()

        general = tomlkit.table()
        general["id"] = self.general.id
        general["name"] = self.general.name
        if self.general.description:
            general["description"] = self.general.description
        general["version"] = self.general.version
        if self.general.url:
            general["url"] = self.general.url
        general["runner_id"] = self.general.runner_id
        general["runner_min_version"] = self.general.runner_min_version
        general["default_timeout"] = self.general.default_timeout
        doc["general"] = general

        if self.properties:
            arr = tomlkit.array()
            for p in self.properties:
                t = tomlkit.table()
                t["name"] = p.name
                if p.description:
                    t["description"] = p.description
                t["input-type"] = p.input_type
                t["optional"] = p.optional
                if p.options:
                    t["options"] = p.options
                if p.default:
                    t["default"] = p.default
                arr.append(t)
            doc["property"] = arr

        _write_toml(path, doc)
        type(self)._instances[path] = self

    @classmethod
    def clear_cache(cls, path: Path) -> None:
        """Evict cached entry for *path* (same pattern as RunnerMetadata)."""
        cls._instances.pop(path, None)


# --- Settings ---

@dataclass
class RunnerSettingsGeneral:
    enabled: bool = False
    timeout: str = "1m"


@dataclass
class SessionInfo:
    session_id: str = "none"
    state: str = "off"
    last_run: str = "none"
    last_run_status: str = "none"


@dataclass
class RunnerSettings:
    """Runner (or task) runtime settings loaded from settings.toml.

    Same class-level caching as the metadata classes.  Unlike metadata,
    load() returns a default instance when the file does not exist
    (fresh install / first launch).
    """

    _instances: ClassVar[dict[Path, RunnerSettings]] = {}

    general: RunnerSettingsGeneral = field(default_factory=RunnerSettingsGeneral)
    properties: dict[str, str] = field(default_factory=dict)
    session: SessionInfo = field(default_factory=SessionInfo)

    @classmethod
    def load(cls, path: Path) -> RunnerSettings:
        if path in cls._instances:
            return cls._instances[path]
        if not path.exists():
            result = cls()
            cls._instances[path] = result
            return result
        doc = tomlkit.parse(path.read_text())
        result = cls()

        general_table = doc.get("general", {})
        if isinstance(general_table, dict):
            result.general.enabled = bool(general_table.get("enabled", False))
            result.general.timeout = str(general_table.get("timeout", "1m"))

        properties_table = doc.get("properties", {})
        if isinstance(properties_table, dict):
            for k, v in properties_table.items():
                result.properties[str(k)] = str(v)

        session_table = doc.get("session", {})
        if isinstance(session_table, dict):
            result.session.session_id = str(session_table.get("session_id", "none"))
            result.session.state = str(session_table.get("state", "off"))
            result.session.last_run = str(session_table.get("last_run", "none"))
            result.session.last_run_status = str(session_table.get("last_run_status", "none"))

        cls._instances[path] = result
        return result

    def save(self, path: Path) -> None:
        doc = tomlkit.document()

        general = tomlkit.table()
        general["enabled"] = self.general.enabled
        general["timeout"] = self.general.timeout
        doc["general"] = general

        doc["properties"] = _properties_to_table(self.properties)

        session = tomlkit.table()
        session["session_id"] = self.session.session_id
        session["state"] = self.session.state
        # Only write non-default values to keep the file clean
        if self.session.last_run != "none":
            session["last_run"] = self.session.last_run
        if self.session.last_run_status != "none":
            session["last_run_status"] = self.session.last_run_status
        doc["session"] = session

        _write_toml(path, doc)
        type(self)._instances[path] = self

    @classmethod
    def clear_cache(cls, path: Path) -> None:
        """Evict cached entry for *path*."""
        cls._instances.pop(path, None)


# TaskSettings is an alias for RunnerSettings — same shape, different semantics.
# Because it is a Python alias, the shared ClassVar _instances dict is also shared,
# so RunnerSettings.clear_cache and TaskSettings.clear_cache operate on the same cache.
TaskSettings = RunnerSettings
TaskSettingsGeneral = RunnerSettingsGeneral


# --- Bundled ---

@dataclass
class BundledItem:
    url: str


@dataclass
class BundledRunners:
    runners: list[BundledItem] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> BundledRunners:
        if not path.exists():
            return cls()
        doc = tomlkit.parse(path.read_text())
        result = cls()
        for item in doc.get("runners", []):
            result.runners.append(BundledItem(url=str(item.get("url", ""))))
        return result


@dataclass
class BundledTasks:
    tasks: list[BundledItem] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> BundledTasks:
        if not path.exists():
            return cls()
        doc = tomlkit.parse(path.read_text())
        result = cls()
        for item in doc.get("tasks", []):
            result.tasks.append(BundledItem(url=str(item.get("url", ""))))
        return result
