from __future__ import annotations

from pathlib import Path
from typing import Any

from textual import on
from textual.widgets import Button

from termux_tasker.config import PropertyDef, RunnerSettings
from termux_tasker.ui.base import (
    ButtonConfig,
    InputScreen,
    InfoScreen,
    MenuScreen,
)
from termux_tasker.ui.screens._utils import (
    termux_app,
    parse_property_value,
    is_property_value_empty,
)

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

        def _show_input() -> None:
            termux_app(self).push_screen(
                InputScreen(
                    title=prop.name,
                    description=prop.description or "",
                    input_type=prop.input_type,
                    options=prop.options or [],
                    current_value=cur_val,
                ),
                _on_result,
            )

        def _warn_and_retry() -> None:
            termux_app(self).push_screen(
                InfoScreen(
                    message=f"'{prop.name}' is required and must have a value.",
                    severity="warning",
                ),
                lambda _: _show_input(),
            )

        def _on_result(result: Any) -> None:
            if result is None:
                return
            if not prop.optional and is_property_value_empty(result, prop.input_type):
                _warn_and_retry()
                return
            current_settings = self._load_settings()
            if prop.input_type == "checkbox" and isinstance(result, (list, tuple)):
                current_settings.properties[prop.name] = ",".join(str(v) for v in result)
            else:
                current_settings.properties[prop.name] = str(result)
            current_settings.save(self._settings_file())
            self._refresh_items()

        _show_input()
