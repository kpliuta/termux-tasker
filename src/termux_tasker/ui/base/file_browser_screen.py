from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Union

from textual import on
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Static

_HERE = Path(__file__).parent


class FileBrowserScreen(ModalScreen[Union[Path, None]]):
    """A modal screen for browsing and selecting files or folders.

    When *select_folder* is True, directory selection enables the "Select"
    button; file selection does not.  When False, file selection enables it.

    When *read_only* is True, the screen shows only a Close button.

    When *expand* is True, all directories are expanded on mount.
    """

    CSS_PATH = _HERE / "tcss" / "file_browser_screen.tcss"
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
