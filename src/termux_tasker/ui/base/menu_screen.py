from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Sequence, Literal, cast

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.css.query import NoMatches
from textual.dom import check_identifiers
from textual.events import Key, ScreenResume
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Static
from textual.widget import Widget

ButtonVariant = Literal["default", "primary", "success", "warning", "error"]

_HERE = Path(__file__).parent


class ButtonLayout(Enum):
    """Where buttons appear on screen."""

    TOP = "top"
    BOTTOM = "bottom"


def check_unique_button_ids(items: Sequence[ButtonConfig]) -> None:
    """Reject duplicate button ids.

    Ids are the key for event handlers and in-place updates — two
    buttons sharing one would silently break both.

    Note: must not be named ``_validate_*`` — Textual treats methods
    with that prefix as reactive value validators.
    """
    seen: set[str] = set()
    for item in items:
        if item.id in seen:
            raise ValueError(f"Duplicate button id: {item.id!r}")
        seen.add(item.id)


@dataclass
class ButtonConfig:
    """Configuration for a single button in MenuScreen.

    ``id`` is required: it must be non-empty and a valid Textual
    identifier (letters, digits, underscores, hyphens; must not start
    with a digit).  It is used for event handlers and in-place menu
    updates.
    """

    id: str
    label: str
    variant: ButtonVariant = "default"
    disabled: bool = False
    layout: ButtonLayout = ButtonLayout.TOP
    title: str = ""

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError(
                "ButtonConfig.id is required and must be a non-empty string"
            )
        check_identifiers("button id", self.id)


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

    menu_items: reactive[list[ButtonConfig]] = reactive([], init=False)
    description: reactive[str | None] = reactive(None, init=False)

    def __init__(
            self,
            menu_items: list[ButtonConfig] | Sequence[ButtonConfig],
            description: str | None = None,
            description_widget: Widget | None = None,
            description_max_height: str | None = None,
            column_count: int = 1,
            show_back_button: bool = False,
            show_exit_button: bool = False,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        check_unique_button_ids(menu_items)
        self.menu_items = list(menu_items)
        self.description = description
        self._description_widget = description_widget
        self._description_max_height = description_max_height
        self._column_count = column_count
        self.show_back_button = show_back_button
        self.show_exit_button = show_exit_button
        # Last title rendered per button id — used to skip redundant
        # in-place title updates in watch_menu_items.
        self._active_titles: dict[str, str] = {}

    # ── Compose ───────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="top-container"):
            yield from self._compose_description()
            yield from self._compose_top_buttons()
        with Container(id="bottom-container"):
            yield from self._compose_bottom_buttons()
        yield Footer()

    def _compose_description(self) -> ComposeResult:
        if self._description_widget is not None or self.description:
            with VerticalScroll(id="description-scroll") as ds:
                if self._description_max_height is not None:
                    ds.styles.max_height = self._description_max_height
                if self._description_widget is not None:
                    yield self._description_widget
                elif self.description:
                    yield Static(self.description, id="description")

    def _make_title_static(self, btn: ButtonConfig) -> Static | None:
        """Build the caption rendered above a button, if it has a title.

        Records the rendered title so watch_menu_items can skip
        redundant updates later.
        """
        if not btn.title:
            return None
        self._active_titles[btn.id] = btn.title
        return Static(btn.title, classes="btn-title")

    def _compose_top_buttons(self) -> ComposeResult:
        top = [b for b in self.menu_items if b.layout == ButtonLayout.TOP]
        yield from self._compose_button_group(top)

    def _compose_bottom_buttons(self) -> ComposeResult:
        bottom = [b for b in self.menu_items if b.layout == ButtonLayout.BOTTOM]
        yield from self._compose_button_group(bottom)

        if self.show_back_button:
            yield Button("Back", id="back", variant="error")
        if self.show_exit_button:
            yield Button("Exit", id="exit", variant="error")

    def _compose_button_group(self, buttons: list[ButtonConfig]) -> ComposeResult:
        per_row = self._column_count
        if per_row <= 1:
            for btn in buttons:
                yield from self._compose_single_button(btn)
        else:
            for row_idx in range(0, len(buttons), per_row):
                row_buttons = buttons[row_idx: row_idx + per_row]
                with Horizontal(
                    id=f"button-row-{row_idx}", classes="button-row"
                ):
                    for btn in row_buttons:
                        title_static = self._make_title_static(btn)
                        if title_static is not None:
                            yield title_static
                        yield Button(
                            btn.label,
                            id=btn.id,
                            variant=btn.variant,
                            disabled=btn.disabled,
                        )

    def _compose_single_button(self, btn: ButtonConfig) -> ComposeResult:
        title_static = self._make_title_static(btn)
        if title_static is not None:
            yield title_static
        yield Button(
            btn.label,
            id=btn.id,
            variant=btn.variant,
            disabled=btn.disabled,
        )

    # ── Watchers ──────────────────────────────────────────────────────

    def watch_menu_items(self) -> None:
        """Reactive watcher — called automatically when self.menu_items changes.

        Optimization: if the set of button IDs is unchanged,
        mutate labels/titles/disabled in-place to preserve focus and avoid
        flicker.  Otherwise, tear down and rebuild the entire DOM.
        """
        try:
            self.query_one(VerticalScroll)
        except NoMatches:
            return  # widget tree may not exist yet (triggered via init=False)

        # Runtime reassignments are validated too; __init__ validated
        # its list explicitly before assigning.
        check_unique_button_ids(self.menu_items)

        action_buttons = [
            btn for btn in self.query(Button)
            if btn.id not in ("back", "exit")
        ]
        existing_ids = {btn.id for btn in action_buttons}
        needed_ids = {btn.id for btn in self.menu_items}

        if (
            needed_ids == existing_ids
            and len(self.menu_items) == len(action_buttons)
        ):
            id_to_config = {btn.id: btn for btn in self.menu_items}
            for btn in action_buttons:
                # Back/Exit are excluded above; every mounted action
                # button comes from a validated config, so id is set.
                btn_id = cast(str, btn.id)
                cfg = id_to_config[btn_id]
                btn.label = cfg.label
                btn.disabled = cfg.disabled
                self._update_button_title(btn, cfg)
        else:
            self.run_worker(self._rebuild_menu())

    def _update_button_title(self, btn: Button, cfg: ButtonConfig) -> None:
        """Sync the caption above *btn* with ``cfg.title`` (in-place)."""
        btn_id = btn.id
        if not btn_id or self._active_titles.get(btn_id) == cfg.title:
            return
        parent = btn.parent
        siblings = list(parent.children) if parent else []
        idx = siblings.index(btn)
        prev = siblings[idx - 1] if idx > 0 else None
        if isinstance(prev, Static) and "btn-title" in prev.classes:
            if cfg.title:
                prev.update(cfg.title)
            else:
                prev.display = False
        self._active_titles[btn_id] = cfg.title

    async def _rebuild_menu(self) -> None:
        """Full DOM teardown and rebuild of the button menu."""
        try:
            scroll = self.query_one(VerticalScroll)
        except NoMatches:
            return
        await scroll.remove_children()

        desc_scroll = VerticalScroll(id="description-scroll")
        if self._description_max_height is not None:
            desc_scroll.styles.max_height = self._description_max_height
        if self._description_widget is not None:
            await scroll.mount(desc_scroll)
            await desc_scroll.mount(self._description_widget)
        elif self.description:
            await scroll.mount(desc_scroll)
            await desc_scroll.mount(Static(self.description, id="description"))

        top_buttons = [b for b in self.menu_items if b.layout == ButtonLayout.TOP]
        await self._mount_button_group(scroll, top_buttons)

        bottom_bar = self.query_one("#bottom-container", Container)
        await bottom_bar.remove_children()

        bottom_cfgs = [b for b in self.menu_items if b.layout == ButtonLayout.BOTTOM]
        await self._mount_button_group(bottom_bar, bottom_cfgs)

        if self.show_back_button:
            await bottom_bar.mount(Button("Back", id="back", variant="error"))
        if self.show_exit_button:
            await bottom_bar.mount(Button("Exit", id="exit", variant="error"))

    async def _mount_button_group(
        self, parent: Widget, buttons: list[ButtonConfig]
    ) -> None:
        per_row = self._column_count
        if per_row <= 1:
            for btn in buttons:
                title_static = self._make_title_static(btn)
                if title_static is not None:
                    await parent.mount(title_static)
                await parent.mount(
                    Button(
                        btn.label,
                        id=btn.id,
                        variant=btn.variant,
                        disabled=btn.disabled,
                    )
                )
        else:
            for i in range(0, len(buttons), per_row):
                row_buttons = buttons[i: i + per_row]
                row = Horizontal(id=f"button-row-{i}", classes="button-row")
                await parent.mount(row)
                for btn in row_buttons:
                    title_static = self._make_title_static(btn)
                    if title_static is not None:
                        await row.mount(title_static)
                    await row.mount(
                        Button(
                            btn.label,
                            id=btn.id,
                            variant=btn.variant,
                            disabled=btn.disabled,
                        )
                    )

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
