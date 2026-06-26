from __future__ import annotations

from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.css.query import NoMatches
from textual.events import Key, ScreenResume
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Static

_HERE = Path(__file__).parent


class MenuScreen(Screen[None]):
    """A screen with a menu of buttons.

    Uses Textual reactive attributes (menu_items, description) so that
    subclasses can mutate them and the UI auto-updates via watchers.

    ``init=False`` prevents watchers from firing during ``__init__``
    (before the widget tree exists).  Watchers fire on subsequent
    mutations only.
    """

    CSS_PATH = _HERE / "tcss" / "menu_screen.tcss"
    BINDINGS = [("escape", "press_back", "Back")]

    menu_items: reactive[dict[str, str]] = reactive({}, init=False)
    description: reactive[str | None] = reactive(None, init=False)

    def __init__(
            self,
            menu_items: dict[str, str],
            description: str | None = None,
            show_back_button: bool = False,
            show_exit_button: bool = False,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.menu_items = menu_items
        self.description = description
        self.show_back_button = show_back_button
        self.show_exit_button = show_exit_button

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            if self.description:
                yield Static(self.description, id="description")

            for label, btn_id in self.menu_items.items():
                if btn_id:
                    yield Button(label, id=btn_id, variant="default")
                else:
                    yield Button(label, variant="default", disabled=True)

            yield Static(classes="spacer")

            if self.show_back_button:
                yield Button("Back", id="back", variant="error")

            if self.show_exit_button:
                yield Button("Exit", id="exit", variant="error")

        yield Footer()

    def watch_menu_items(self) -> None:
        """Reactive watcher — called automatically when self.menu_items changes.

        Optimization: if the set of button IDs is unchanged (same keys),
        mutate labels in-place to preserve focus and avoid flicker.
        Otherwise, tear down and rebuild the entire DOM.
        """
        try:
            scroll = self.query_one(VerticalScroll)
        except NoMatches:
            return  # widget tree may not exist yet (triggered via init=False)
        existing_ids = {btn.id for btn in scroll.query(Button) if btn.id}
        needed_ids = {v for v in self.menu_items.values() if v}
        action_buttons = [b for b in scroll.query(Button) if b.id not in ("back", "exit")]
        if needed_ids == existing_ids - {"back", "exit"} and len(self.menu_items) == len(action_buttons):
            id_to_label = {v: k for k, v in self.menu_items.items()}
            for btn in action_buttons:
                if btn.id in id_to_label:
                    btn.label = id_to_label[btn.id]
        else:
            self.run_worker(self._rebuild_menu(scroll))

    async def _rebuild_menu(self, scroll: VerticalScroll) -> None:
        """Full DOM teardown and rebuild of the button menu.

        Used when the button structure has changed (different IDs),
        since in-place label mutation is insufficient.
        """
        await scroll.remove_children()

        desc = Static(self.description or "", id="description")
        desc.display = bool(self.description)
        await scroll.mount(desc)

        for label, btn_id in self.menu_items.items():
            if btn_id:
                btn = Button(label, id=btn_id, variant="default")
            else:
                btn = Button(label, variant="default", disabled=True)
            await scroll.mount(btn)

        await scroll.mount(Static(classes="spacer"))
        if self.show_back_button:
            await scroll.mount(Button("Back", id="back", variant="error"))
        if self.show_exit_button:
            await scroll.mount(Button("Exit", id="exit", variant="error"))

    def watch_description(self, description: str | None) -> None:
        try:
            desc = self.query_one("#description", Static)
            desc.update(description or "")
            desc.display = bool(description)
        except NoMatches:
            pass

    @on(Button.Pressed, "#back")
    def on_back_button_pressed(self, event: Button.Pressed) -> None:
        """Handle back button presses."""
        event.stop()
        self.app.pop_screen()

    def action_press_back(self) -> None:
        """Handle Esc key — pop screen if back button is shown."""
        if self.show_back_button:
            self.app.pop_screen()

    def on_key(self, event: Key) -> None:
        """Handle key presses for navigation."""
        if event.key == "up":
            event.stop()
            self.focus_previous(Button)
        elif event.key == "down":
            event.stop()
            self.focus_next(Button)

    def on_mount(self) -> None:
        pass

    def on_screen_resume(self, _event: ScreenResume) -> None:
        self._refresh()

    def _refresh(self) -> None:
        pass
