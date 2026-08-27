from __future__ import annotations

from pathlib import Path
from typing import Any

from textual import on
from textual.widgets import Button

from termux_tasker.config import PropertyDef, RunnerSettings
from termux_tasker.ui.base import (
    ButtonConfig,
    MenuScreen,
)
from termux_tasker.ui.screens._utils import (
    termux_app,
    parse_property_value,
)
from termux_tasker.ui.screens._ui_utils import ask_validated_input

_SET_PREFIX = "set_"
_NOT_SET = "(not set)"


class PropertiesScreen(MenuScreen):
    """Unified properties editor for runners and tasks.

    Shows one "Set <property>" button per property definition with the
    current value displayed above it as "[b]name[/b]: value".  Refreshing
    is event-driven: items are rebuilt right after a value is saved and
    the reactive watcher updates the button titles in place.
    """

    def __init__(
        self,
        item_path: Path,
        properties: list[PropertyDef],
        item_name: str,
    ) -> None:
        self.item_path = item_path
        self.properties = properties
        super().__init__(self._build_items(), show_back_button=True)
        self.title = "Properties"
        self.sub_title = item_name

    # ── Items ─────────────────────────────────────────────────────────

    def _settings_file(self) -> Path:
        return self.item_path / "settings.toml"

    def _load_settings(self) -> RunnerSettings:
        return RunnerSettings.load(self._settings_file())

    def _build_items(self) -> list[ButtonConfig]:
        settings = self._load_settings()
        items: list[ButtonConfig] = []
        for prop in self.properties:
            value = settings.properties.get(prop.name) or _NOT_SET
            items.append(ButtonConfig(
                f"{_SET_PREFIX}{prop.name}",
                f"Set {prop.name}",
                title=f"[b]{prop.name}[/b]: {value}",
            ))
        return items

    def _refresh_items(self) -> None:
        self.menu_items = self._build_items()

    # ── Property editing ──────────────────────────────────────────────

    @on(Button.Pressed)
    def on_set_property(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if not btn_id.startswith(_SET_PREFIX):
            return
        event.stop()
        self._set_property(btn_id[len(_SET_PREFIX):])

    def _set_property(self, prop_name: str) -> None:
        try:
            prop = next(p for p in self.properties if p.name == prop_name)
        except StopIteration:
            return

        settings = self._load_settings()
        cur_val = parse_property_value(
            settings.properties.get(prop.name, ""), prop.input_type
        )
        empty_message = None if prop.optional else (
            f"'{prop.name}' is required and must have a value."
        )

        def _on_valid(result: Any) -> None:
            current_settings = self._load_settings()
            if prop.input_type == "checkbox" and isinstance(result, (list, tuple)):
                current_settings.properties[prop.name] = ",".join(str(v) for v in result)
            else:
                current_settings.properties[prop.name] = str(result)
            current_settings.save(self._settings_file())
            self._refresh_items()

        ask_validated_input(
            termux_app(self),
            title=prop.name,
            input_type=prop.input_type,
            current_value=cur_val,
            description=prop.description or "",
            options=prop.options or [],
            is_valid=lambda _: True,
            on_valid=_on_valid,
            empty_message=empty_message,
            invalid_message=empty_message,
        )
