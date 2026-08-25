from __future__ import annotations

import pytest
from textual.app import App
from textual.containers import VerticalScroll
from textual.css.query import NoMatches
from textual.dom import BadIdentifier
from textual.widgets import Button, Static

from termux_tasker.ui.base.menu_screen import (
    ButtonConfig,
    ButtonLayout,
    MenuScreen,
)


class TestButtonConfig:
    def test_defaults(self) -> None:
        cfg = ButtonConfig(id="ok", label="OK")
        assert cfg.id == "ok"
        assert cfg.label == "OK"
        assert cfg.variant == "default"
        assert cfg.disabled is False
        assert cfg.layout == ButtonLayout.TOP
        assert cfg.title == ""

    def test_custom_values(self) -> None:
        cfg = ButtonConfig(
            label="Install",
            id="install",
            variant="primary",
            disabled=True,
            layout=ButtonLayout.BOTTOM,
            title="[b]Title[/b]",
        )
        assert cfg.label == "Install"
        assert cfg.id == "install"
        assert cfg.variant == "primary"
        assert cfg.disabled is True
        assert cfg.layout == ButtonLayout.BOTTOM
        assert cfg.title == "[b]Title[/b]"

    def test_empty_id_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            ButtonConfig(id="", label="OK")

    def test_blank_id_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            ButtonConfig(id="   ", label="OK")

    def test_invalid_identifier_rejected(self) -> None:
        with pytest.raises(BadIdentifier):
            ButtonConfig(id="1abc", label="OK")

    def test_valid_identifiers_accepted(self) -> None:
        for btn_id in ("a", "_x", "set_property-1", "version_v1_0_0"):
            assert ButtonConfig(id=btn_id, label="L").id == btn_id


class TestMenuScreenInit:
    def test_stores_menu_items(self) -> None:
        items = [ButtonConfig(label="A", id="a"), ButtonConfig(label="B", id="b")]
        screen = MenuScreen(menu_items=items)
        assert len(screen.menu_items) == 2
        assert screen.menu_items[0].label == "A"
        assert screen.menu_items[1].label == "B"

    def test_description_defaults_to_none(self) -> None:
        screen = MenuScreen(menu_items=[])
        assert screen.description is None

    def test_stores_description(self) -> None:
        screen = MenuScreen(menu_items=[], description="Hello")
        assert screen.description == "Hello"

    def test_description_widget_stored(self) -> None:
        widget = Static("custom")
        screen = MenuScreen(menu_items=[], description_widget=widget)
        assert screen._description_widget is widget

    def test_description_max_height_default(self) -> None:
        screen = MenuScreen(menu_items=[])
        assert screen._description_max_height is None

    def test_description_max_height_custom(self) -> None:
        screen = MenuScreen(menu_items=[], description_max_height="50%")
        assert screen._description_max_height == "50%"

    def test_column_count_default(self) -> None:
        screen = MenuScreen(menu_items=[])
        assert screen._column_count == 1

    def test_column_count_custom(self) -> None:
        screen = MenuScreen(menu_items=[], column_count=5)
        assert screen._column_count == 5

    def test_show_back_button_default(self) -> None:
        screen = MenuScreen(menu_items=[])
        assert screen.show_back_button is False

    def test_show_exit_button_default(self) -> None:
        screen = MenuScreen(menu_items=[])
        assert screen.show_exit_button is False

    def test_duplicate_ids_rejected(self) -> None:
        items = [
            ButtonConfig(label="A", id="dup"),
            ButtonConfig(label="B", id="dup"),
        ]
        with pytest.raises(ValueError, match="Duplicate button id"):
            MenuScreen(menu_items=items)

    def test_empty_id_item_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            MenuScreen(menu_items=[ButtonConfig(id="", label="A")])


class TestMenuScreenCompose:
    @pytest.mark.asyncio
    async def test_renders_buttons(self) -> None:
        items = [ButtonConfig(label="A", id="a"), ButtonConfig(label="B", id="b")]

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(MenuScreen(menu_items=items))

        async with TestApp().run_test() as pilot:
            buttons = pilot.app.screen.query(Button)
            labels = [str(b.label).strip() for b in buttons]
            assert "A" in labels
            assert "B" in labels

    @pytest.mark.asyncio
    async def test_renders_description(self) -> None:
        screen = MenuScreen(menu_items=[], description="Test desc")

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with TestApp().run_test() as pilot:
            desc = pilot.app.screen.query_one("#description", Static)
            assert "Test desc" in str(desc.render())

    @pytest.mark.asyncio
    async def test_renders_description_widget(self) -> None:
        widget = Static("custom widget content")
        screen = MenuScreen(menu_items=[], description_widget=widget)

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with TestApp().run_test() as pilot:
            found = False
            for w in pilot.app.screen.query(Static):
                if "custom widget content" in str(w.render()):
                    found = True
                    break
            assert found

    @pytest.mark.asyncio
    async def test_back_button_shown_when_enabled(self) -> None:
        screen = MenuScreen(menu_items=[], show_back_button=True)

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with TestApp().run_test() as pilot:
            btn = pilot.app.screen.query_one("#back", Button)
            assert str(btn.label).strip() == "Back"

    @pytest.mark.asyncio
    async def test_exit_button_shown_when_enabled(self) -> None:
        screen = MenuScreen(menu_items=[], show_exit_button=True)

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with TestApp().run_test() as pilot:
            btn = pilot.app.screen.query_one("#exit", Button)
            assert str(btn.label).strip() == "Exit"

    @pytest.mark.asyncio
    async def test_disabled_button(self) -> None:
        items = [ButtonConfig(label="Disabled", id="dis", disabled=True)]

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(MenuScreen(menu_items=items))

        async with TestApp().run_test() as pilot:
            btn = pilot.app.screen.query_one("#dis", Button)
            assert btn.disabled is True

    @pytest.mark.asyncio
    async def test_button_title_rendered(self) -> None:
        items = [ButtonConfig(label="OK", id="ok", title="[b]My Title[/b]")]

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(MenuScreen(menu_items=items))

        async with TestApp().run_test() as pilot:
            titles = pilot.app.screen.query(".btn-title")
            assert len(titles) >= 1
            assert "My Title" in str(titles[0].render())

    @pytest.mark.asyncio
    async def test_column_count_1_no_rows(self) -> None:
        """column_count=1 should render buttons directly, not in Horizontal rows."""
        items = [
            ButtonConfig(label="A", id="a"),
            ButtonConfig(label="B", id="b"),
        ]

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(MenuScreen(menu_items=items, column_count=1))

        async with TestApp().run_test() as pilot:
            from textual.containers import Horizontal
            rows = pilot.app.screen.query(Horizontal)
            assert len(rows) == 0

    @pytest.mark.asyncio
    async def test_column_count_2_creates_rows(self) -> None:
        """column_count=2 should group buttons in Horizontal rows."""
        items = [
            ButtonConfig(label="A", id="a"),
            ButtonConfig(label="B", id="b"),
            ButtonConfig(label="C", id="c"),
        ]

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(MenuScreen(menu_items=items, column_count=2))

        async with TestApp().run_test() as pilot:
            rows = pilot.app.screen.query(".button-row")
            assert len(rows) == 2

    @pytest.mark.asyncio
    async def test_bottom_layout_buttons_in_bottom_bar(self) -> None:
        items = [
            ButtonConfig(label="Top", id="top"),
            ButtonConfig(label="Bottom", id="bottom", layout=ButtonLayout.BOTTOM),
        ]

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(MenuScreen(
                    menu_items=items, show_back_button=True
                ))

        async with TestApp().run_test() as pilot:
            bottom_bar = pilot.app.screen.query_one("#bottom-container")
            bottom_btns = [
                b for b in bottom_bar.query(Button)
                if b.id not in ("back", "exit")
            ]
            assert len(bottom_btns) == 1
            assert bottom_btns[0].id == "bottom"

    @pytest.mark.asyncio
    async def test_back_exit_in_bottom_bar(self) -> None:
        items = [ButtonConfig(label="Top", id="top")]

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(MenuScreen(
                    menu_items=items,
                    show_back_button=True,
                    show_exit_button=True,
                ))

        async with TestApp().run_test() as pilot:
            bottom_bar = pilot.app.screen.query_one("#bottom-container")
            back = bottom_bar.query_one("#back", Button)
            exit_ = bottom_bar.query_one("#exit", Button)
            assert str(back.label).strip() == "Back"
            assert str(exit_.label).strip() == "Exit"

    @pytest.mark.asyncio
    async def test_column_count_2_with_bottom_bar(self) -> None:
        items = [
            ButtonConfig(label="A", id="a"),
            ButtonConfig(label="B", id="b"),
            ButtonConfig(label="Bottom", id="bottom", layout=ButtonLayout.BOTTOM),
        ]

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(MenuScreen(
                    menu_items=items,
                    column_count=2,
                    show_back_button=True,
                ))

        async with TestApp().run_test() as pilot:
            scroll_rows = pilot.app.screen.query_one("#top-container").query(".button-row")
            assert len(scroll_rows) == 1
            bottom_bar = pilot.app.screen.query_one("#bottom-container")
            back = bottom_bar.query_one("#back", Button)
            assert back is not None


class TestMenuScreenWatchers:
    @pytest.mark.asyncio
    async def test_watch_menu_items_updates_buttons(self) -> None:
        screen = MenuScreen(menu_items=[ButtonConfig(label="A", id="a")])

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with TestApp().run_test() as pilot:
            screen.menu_items = [
                ButtonConfig(label="A", id="a"),
                ButtonConfig(label="B", id="b"),
            ]
            await pilot.pause()
            buttons = pilot.app.screen.query(Button)
            ids = {b.id for b in buttons if b.id}
            assert "a" in ids
            assert "b" in ids

    @pytest.mark.asyncio
    async def test_watch_menu_items_updates_title_in_place(self) -> None:
        """Same button ids with a changed title must update the caption
        without rebuilding the DOM."""
        screen = MenuScreen(
            menu_items=[ButtonConfig(label="Set p", id="set_p", title="[b]p[/b]: old")]
        )

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with TestApp().run_test() as pilot:
            btn_before = pilot.app.screen.query_one("#set_p", Button)
            screen.menu_items = [
                ButtonConfig(label="Set p", id="set_p", title="[b]p[/b]: new")
            ]
            await pilot.pause()
            btn_after = pilot.app.screen.query_one("#set_p", Button)
            assert btn_after is btn_before
            titles = pilot.app.screen.query(".btn-title")
            assert len(titles) == 1
            assert "new" in str(titles[0].render())

    @pytest.mark.asyncio
    async def test_bottom_bar_label_updates_in_place(self) -> None:
        """Bottom-bar-only changes must not force a full rebuild."""
        items = [ButtonConfig(label="Update", id="update", layout=ButtonLayout.BOTTOM)]
        screen = MenuScreen(menu_items=items, show_back_button=True)

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with TestApp().run_test() as pilot:
            btn_before = pilot.app.screen.query_one("#update", Button)
            screen.menu_items = [
                ButtonConfig(label="Update!", id="update", layout=ButtonLayout.BOTTOM)
            ]
            await pilot.pause()
            btn_after = pilot.app.screen.query_one("#update", Button)
            assert btn_after is btn_before
            assert str(btn_after.label).strip() == "Update!"

    @pytest.mark.asyncio
    async def test_watch_menu_items_rejects_duplicate_ids(self) -> None:
        screen = MenuScreen(menu_items=[ButtonConfig(label="A", id="a")])

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with TestApp().run_test() as pilot:
            with pytest.raises(ValueError, match="Duplicate button id"):
                screen.menu_items = [
                    ButtonConfig(label="B", id="b"),
                    ButtonConfig(label="C", id="b"),
                ]
            await pilot.pause()

    @pytest.mark.asyncio
    async def test_watch_description_updates_text(self) -> None:
        screen = MenuScreen(menu_items=[], description="old")

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with TestApp().run_test() as pilot:
            screen.description = "new"
            await pilot.pause()
            desc = pilot.app.screen.query_one("#description", Static)
            assert "new" in str(desc.render())

    @pytest.mark.asyncio
    async def test_no_description_no_scroll(self) -> None:
        """When no description or description_widget is provided, description-scroll shouldn't appear."""
        screen = MenuScreen(menu_items=[])

        class TestApp(App):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with TestApp().run_test() as pilot:
            with pytest.raises(NoMatches):
                pilot.app.screen.query_one("#description-scroll", VerticalScroll)
