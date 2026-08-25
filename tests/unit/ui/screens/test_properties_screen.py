from __future__ import annotations

from pathlib import Path

import pytest
from textual.app import App
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from termux_tasker.config import PropertyDef, RunnerSettings
from termux_tasker.ui.base import InfoScreen, InputScreen
from termux_tasker.ui.screens.properties import PropertiesScreen

_PROPS = [
    PropertyDef(name="p-1", description="First property", input_type="text", optional=False),
    PropertyDef(name="p-2", input_type="radio", options=["a", "b"]),
]


def _make_item(tmp_path: Path, values: dict[str, str] | None = None) -> Path:
    item = tmp_path / "items" / "item_1"
    item.mkdir(parents=True)
    settings = RunnerSettings()
    settings.properties.update(values or {})
    settings.save(item / "settings.toml")
    return item


def _make_app(screen: Screen) -> App[None]:
    class HostApp(App[None]):
        def on_mount(self) -> None:
            self.push_screen(screen)

    return HostApp()


def _title_text(screen: Screen, btn_id: str) -> str:
    btn = screen.query_one(f"#{btn_id}", Button)
    siblings = list(btn.parent.children)  # type: ignore[union-attr]
    prev = siblings[siblings.index(btn) - 1]
    assert isinstance(prev, Static)
    return str(prev.render())


class TestPropertiesScreenInit:
    @pytest.mark.asyncio
    async def test_title_and_subtitle(self, tmp_path: Path) -> None:
        screen = PropertiesScreen(_make_item(tmp_path), _PROPS, "My Runner")

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with TestApp().run_test():
            assert screen.title == "Properties"
            assert screen.sub_title == "My Runner"

    @pytest.mark.asyncio
    async def test_button_per_property_with_value_in_title(self, tmp_path: Path) -> None:
        item = _make_item(tmp_path, {"p-1": "v1"})
        screen = PropertiesScreen(item, _PROPS, "My Runner")

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with TestApp().run_test() as pilot:
            labels = [
                str(b.label).strip()
                for b in pilot.app.screen.query(Button)
                if b.id and b.id.startswith("set_")
            ]
            assert labels == ["Set p-1", "Set p-2"]
            assert _title_text(pilot.app.screen, "set_p-1") == "p-1: v1"
            # Unset properties show the "(not set)" placeholder
            assert _title_text(pilot.app.screen, "set_p-2") == "p-2: (not set)"

    @pytest.mark.asyncio
    async def test_back_button_shown(self, tmp_path: Path) -> None:
        screen = PropertiesScreen(_make_item(tmp_path), _PROPS, "My Runner")

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with TestApp().run_test() as pilot:
            back = pilot.app.screen.query_one("#back", Button)
            assert str(back.label).strip() == "Back"


class TestPropertiesScreenEditing:
    @pytest.mark.asyncio
    async def test_set_property_saves_and_updates_title_in_place(
        self, tmp_path: Path
    ) -> None:
        item = _make_item(tmp_path)
        screen = PropertiesScreen(item, _PROPS, "My Runner")

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with TestApp().run_test() as pilot:
            btn_before = pilot.app.screen.query_one("#set_p-1", Button)
            await pilot.click("#set_p-1")
            await pilot.pause()
            assert isinstance(pilot.app.screen, InputScreen)

            input_field = pilot.app.screen.query_one("#input_field", Input)
            assert input_field.value == ""
            input_field.value = "new_value"
            await pilot.click("#ok")
            await pilot.pause()

            saved = RunnerSettings.load(item / "settings.toml")
            assert saved.properties["p-1"] == "new_value"
            assert isinstance(pilot.app.screen, PropertiesScreen)
            btn_after = pilot.app.screen.query_one("#set_p-1", Button)
            assert btn_after is btn_before  # in-place update, no rebuild
            assert _title_text(pilot.app.screen, "set_p-1") == "p-1: new_value"

    @pytest.mark.asyncio
    async def test_set_property_prefills_current_value(self, tmp_path: Path) -> None:
        item = _make_item(tmp_path, {"p-2": "a"})
        screen = PropertiesScreen(item, _PROPS, "My Runner")

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with TestApp().run_test() as pilot:
            await pilot.click("#set_p-2")
            await pilot.pause()
            dialog = pilot.app.screen
            assert isinstance(dialog, InputScreen)
            assert dialog.input_type == "radio"
            assert dialog.options == ["a", "b"]
            assert dialog.current_value == "a"

    @pytest.mark.asyncio
    async def test_cancel_keeps_value_unchanged(self, tmp_path: Path) -> None:
        item = _make_item(tmp_path)
        screen = PropertiesScreen(item, _PROPS, "My Runner")

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with TestApp().run_test() as pilot:
            await pilot.click("#set_p-1")
            await pilot.pause()
            await pilot.click("#cancel")
            await pilot.pause()

            assert isinstance(pilot.app.screen, PropertiesScreen)
            saved = RunnerSettings.load(item / "settings.toml")
            assert "p-1" not in saved.properties

    @pytest.mark.asyncio
    async def test_required_empty_warns_and_retries(self, tmp_path: Path) -> None:
        item = _make_item(tmp_path)
        screen = PropertiesScreen(item, _PROPS, "My Runner")

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with TestApp().run_test() as pilot:
            await pilot.click("#set_p-1")
            await pilot.pause()
            pilot.app.screen.query_one("#input_field", Input).value = ""
            await pilot.click("#ok")
            await pilot.pause()

            warning = pilot.app.screen
            assert isinstance(warning, InfoScreen)
            msg = warning.query_one("#info_message")
            assert "required and must have a value" in str(msg.render())

            await pilot.click("#info_button")
            for _ in range(50):
                if isinstance(pilot.app.screen, InputScreen):
                    break
                await pilot.pause(0.02)
            assert isinstance(pilot.app.screen, InputScreen)

            # Providing a value after the retry saves it
            pilot.app.screen.query_one("#input_field", Input).value = "retry_val"
            await pilot.click("#ok")
            await pilot.pause()
            saved = RunnerSettings.load(item / "settings.toml")
            assert saved.properties["p-1"] == "retry_val"

    @pytest.mark.asyncio
    async def test_optional_empty_value_is_saved(self, tmp_path: Path) -> None:
        """p-2 is optional — clearing it must save an empty string."""
        props = [PropertyDef(name="p-2", input_type="text")]
        item = _make_item(tmp_path, {"p-2": "old"})
        screen = PropertiesScreen(item, props, "My Runner")

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with TestApp().run_test() as pilot:
            await pilot.click("#set_p-2")
            await pilot.pause()
            pilot.app.screen.query_one("#input_field", Input).value = ""
            await pilot.click("#ok")
            await pilot.pause()

            saved = RunnerSettings.load(item / "settings.toml")
            assert saved.properties["p-2"] == ""


class TestPropertiesScreenBack:
    @pytest.mark.asyncio
    async def test_back_pops_to_caller(self, tmp_path: Path) -> None:
        screen = PropertiesScreen(_make_item(tmp_path), _PROPS, "My Runner")
        app = _make_app(screen)

        async with app.run_test() as pilot:
            await pilot.pause()
            assert pilot.app.screen is screen
            await pilot.click("#back")
            await pilot.pause()
            assert not isinstance(pilot.app.screen, PropertiesScreen)
