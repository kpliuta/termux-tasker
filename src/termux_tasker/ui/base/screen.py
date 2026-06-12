from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Sequence, Union

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Grid, Vertical, Horizontal
from textual.css.query import NoMatches
from textual.events import Key, ScreenResume
from textual.reactive import reactive
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Header, Footer, Button, Static, DirectoryTree, Input,
    Checkbox, RadioButton, RadioSet, LoadingIndicator, RichLog
)

_HERE = Path(__file__).parent


class MenuScreen(Screen[None]):
    """A screen with a menu of buttons.

    Uses Textual reactive attributes (menu_items, description) so that
    subclasses can mutate them and the UI auto-updates via watchers.

    ``init=False`` prevents watchers from firing during ``__init__``
    (before the widget tree exists).  Watchers fire on subsequent
    mutations only.
    """

    CSS_PATH = _HERE / "menu_screen.tcss"
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


class FileBrowserScreen(ModalScreen[Union[Path, None]]):
    """A modal screen for browsing and selecting files or folders.

    When *select_folder* is True, directory selection enables the "Select"
    button; file selection does not.  When False, file selection enables it.

    When *read_only* is True, the screen shows only a Close button.

    When *expand* is True, all directories are expanded on mount.
    """

    CSS_PATH = _HERE / "file_browser_screen.tcss"
    BINDINGS = [("escape", "close", "Close")]

    def __init__(
            self,
            select_folder: bool = False,
            path: Path = Path("."),
            read_only: bool = False,
            expand: bool = False,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.select_folder = select_folder
        self._start_path = path
        self._selected_path: Path | None = None
        self.read_only = read_only
        self.expand = expand

    def compose(self) -> ComposeResult:
        with Grid():
            yield DirectoryTree(str(self._start_path))
            if self.read_only:
                yield Static()
                yield Button("Close", id="close", variant="primary")
            else:
                yield Button("Select", id="select", variant="primary", disabled=True)
                yield Button("Close", id="close", variant="primary")

    def on_mount(self) -> None:
        if self.expand:
            self.run_worker(self._expand_all())

    async def _expand_all(self) -> None:
        tree = self.query_one(DirectoryTree)
        await self._expand_node(tree, tree.root)

    async def _expand_node(self, tree: DirectoryTree, node: Any) -> None:
        node.expand()
        await asyncio.sleep(0)
        for child in list(node.children):
            await self._expand_node(tree, child)

    @on(DirectoryTree.FileSelected)
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        if self.read_only:
            event.stop()
            return
        if not self.select_folder:
            self._selected_path = event.path
            self.query_one("#select", Button).disabled = False
        else:
            self._selected_path = None
            self.query_one("#select", Button).disabled = True

    @on(DirectoryTree.DirectorySelected)
    def on_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        if self.read_only:
            event.stop()
            return
        if self.select_folder:
            self._selected_path = event.path
            self.query_one("#select", Button).disabled = False
        else:
            self._selected_path = None
            self.query_one("#select", Button).disabled = True

    @on(Button.Pressed, "#select")
    def on_select(self, event: Button.Pressed) -> None:
        event.stop()
        if self._selected_path:
            self.dismiss(self._selected_path)

    @on(Button.Pressed, "#close")
    def on_close(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss(None)

    def action_close(self) -> None:
        self.dismiss(None)


class InputScreen(ModalScreen[Union[str, Sequence[str], None]]):
    """A modal screen for gathering user input via text, radio buttons, or checkboxes."""

    CSS_PATH = _HERE / "input_screen.tcss"
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(
            self,
            title: str,
            description: str | None = None,
            input_type: str = "text",
            options: Sequence[str] | None = None,
            current_value: Union[str, Sequence[str], None] = None,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ) -> None:
        """Initialize the input screen.

        Args:
            title: The title of the dialog.
            description: Optional description text.
            input_type: One of 'text', 'radio', or 'checkbox'.
            options: List of options for radio or checkbox types.
            current_value: Initial value(s) to pre-populate or select.
        """
        super().__init__(name=name, id=id, classes=classes)
        self.dialog_title = title
        self.description = description
        self.input_type = input_type
        self.options = options or []
        self.current_value = current_value

    def compose(self) -> ComposeResult:
        with Grid():
            with Vertical(id="input_dialog"):
                yield Static(self.dialog_title, id="input_title")
                if self.description:
                    yield Static(self.description, id="input_description")

                with VerticalScroll(id="input_content"):
                    if self.input_type == "text":
                        yield Input(
                            value=str(self.current_value) if self.current_value is not None else "",
                            id="input_field"
                        )
                    elif self.input_type == "radio":
                        with RadioSet():
                            for option in self.options:
                                is_selected = False
                                if self.current_value is not None:
                                    if isinstance(self.current_value, str):
                                        is_selected = option.lower() == self.current_value.lower()
                                yield RadioButton(option, value=is_selected)
                    elif self.input_type == "checkbox":
                        selected_values = set()
                        if self.current_value:
                            if isinstance(self.current_value, str):
                                selected_values.add(self.current_value.lower())
                            elif isinstance(self.current_value, (list, tuple, set)):
                                selected_values = {v.lower() for v in self.current_value if isinstance(v, str)}

                        for option in self.options:
                            yield Checkbox(
                                option,
                                value=option.lower() in selected_values
                            )

            yield Button("Cancel", id="cancel", variant="error")
            yield Button("Ok", id="ok", variant="primary")

    @on(Button.Pressed, "#ok")
    def handle_ok(self, event: Button.Pressed) -> None:
        """Collect and return the selected value(s)."""
        event.stop()
        if self.input_type == "text":
            self.dismiss(self.query_one(Input).value)
        elif self.input_type == "radio":
            radio_set = self.query_one(RadioSet)
            pressed = radio_set.pressed_button
            if pressed is not None:
                self.dismiss(str(pressed.label))
            else:
                self.dismiss(None)
        elif self.input_type == "checkbox":
            selected = [
                str(cb.label) for cb in self.query(Checkbox) if cb.value
            ]
            self.dismiss(selected)

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self, event: Button.Pressed) -> None:
        """Close the dialog without returning a value."""
        event.stop()
        self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class InfoScreen(ModalScreen[None]):
    """A modal screen for displaying messages with different severity levels."""

    CSS_PATH = _HERE / "info_screen.tcss"
    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(
            self,
            message: str,
            severity: str = "info",
            button_text: str = "Ok",
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.message = message
        self.severity = severity
        self.button_text = button_text

    def compose(self) -> ComposeResult:
        with Vertical(id="info_dialog"):
            yield Static(self.message, id="info_message", classes=self.severity)
            yield Button(self.button_text, id="info_button", variant="primary")

    @on(Button.Pressed, "#info_button")
    def on_ok(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss(None)

    def action_dismiss(self, result: None = None) -> None:  # type: ignore[override]
        self.dismiss(None)


class ConfirmationScreen(ModalScreen[Union[str, None]]):
    """A modal screen for displaying a confirmation message with two action buttons.

    The return value is the *ok_button_id* string on confirm, or *None* on cancel.
    Callers can pattern-match on the button ID to distinguish multiple
    confirmation screens (e.g. "yes_exit" vs "yes_uninstall").
    """

    CSS_PATH = _HERE / "confirmation_screen.tcss"
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(
            self,
            message: str,
            ok_button_text: str = "Ok",
            cancel_button_text: str = "Cancel",
            ok_button_id: str = "ok_button",
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.message = message
        self.ok_button_text = ok_button_text
        self.cancel_button_text = cancel_button_text
        self.ok_button_id = ok_button_id

    def compose(self) -> ComposeResult:
        with Vertical(id="confirmation_dialog"):
            yield Static(self.message, id="confirmation_message")
            with Horizontal(id="confirmation_buttons"):
                yield Button(self.cancel_button_text, id="cancel_button", variant="error")
                yield Button(self.ok_button_text, id=self.ok_button_id, variant="primary")

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dismiss the screen with ok_button_id or None."""
        event.stop()
        if event.button.id == "cancel_button":
            self.dismiss(None)
        else:
            self.dismiss(self.ok_button_id)

    def action_cancel(self) -> None:
        self.dismiss(None)


class LoadingScreen(ModalScreen[None]):
    """A modal screen with a loading indicator and a message."""

    CSS_PATH = _HERE / "loading_screen.tcss"

    def __init__(
            self,
            message: str = "",
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.initial_message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="loading_dialog"):
            yield LoadingIndicator()
            yield Static(self.initial_message, id="loading_message")

    def update_message(self, message: str) -> None:
        """Update the message displayed below the loading indicator."""
        self.query_one("#loading_message", Static).update(message)


class LogScreen(ModalScreen[None]):
    """A modal screen for displaying logs with an optional 'follow' feature.

    When follow mode is enabled (via a Checkbox), a 1-second interval timer
    polls the file for new content and appends it to the RichLog widget.
    Tracks ``_file_pos`` to read incrementally.
    """

    CSS_PATH = _HERE / "log_screen.tcss"
    BINDINGS = [("escape", "close", "Close")]

    def __init__(
            self,
            content: str | Path = "",
            show_follow: bool = False,
            soft_wrap: bool = False,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.content = content
        self.show_follow = show_follow and isinstance(content, Path)
        self.soft_wrap = soft_wrap
        self._timer: Any = None
        self._file_pos = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="log_dialog"):
            yield RichLog(highlight=True, markup=False, wrap=self.soft_wrap)
            with Horizontal(id="log_controls"):
                yield Checkbox("Wrap", id="wrap_checkbox", value=self.soft_wrap)
                if self.show_follow:
                    yield Checkbox("Follow", id="follow_checkbox")
                    yield Button("Reset", id="reset_button", variant="default")
                yield Button("Close", id="close_button", variant="primary")

    def on_mount(self) -> None:
        self._load_content()

    def _load_content(self) -> None:
        log = self.query_one(RichLog)
        if isinstance(self.content, Path):
            if self.content.exists():
                with open(self.content, "rb") as f:
                    data = f.read()
                    log.write(data.decode(errors="replace").rstrip("\n"))
                    self._file_pos = f.tell()
            else:
                log.write(f"File not found: {self.content}")
        else:
            log.write(self.content)

    @on(Checkbox.Changed, "#follow_checkbox")
    def on_follow_changed(self, event: Checkbox.Changed) -> None:
        if event.value:
            self._timer = self.set_interval(1.0, self._update_log_from_file)
        else:
            if self._timer:
                self._timer.stop()
                self._timer = None

    @on(Checkbox.Changed, "#wrap_checkbox")
    def on_wrap_changed(self, event: Checkbox.Changed) -> None:
        event.stop()
        self.soft_wrap = event.value
        log = self.query_one(RichLog)
        log.wrap = event.value
        log.clear()
        self._load_content()

    def _update_log_from_file(self) -> None:
        if isinstance(self.content, Path) and self.content.exists():
            log = self.query_one(RichLog)
            with open(self.content, "rb") as f:
                f.seek(self._file_pos)
                data = f.read()
                self._file_pos = f.tell()
            if data:
                log.write(data.decode(errors="replace").rstrip("\n"))

    @on(Button.Pressed, "#reset_button")
    def on_reset(self, event: Button.Pressed) -> None:
        event.stop()
        if isinstance(self.content, Path) and self.content.exists():
            self._file_pos = self.content.stat().st_size
            self.query_one(RichLog).clear()

    @on(Button.Pressed, "#close_button")
    def on_close(self, event: Button.Pressed) -> None:
        event.stop()
        if self._timer:
            self._timer.stop()
        self.dismiss(None)

    def action_close(self) -> None:
        if self._timer:
            self._timer.stop()
        self.dismiss(None)
