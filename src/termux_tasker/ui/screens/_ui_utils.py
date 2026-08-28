"""UI / Textual-screen helpers for feature screens.

This module holds utilities that drive Textual screens (push screens, prompt
for input, show warnings). It is the UI counterpart to
``termux_tasker.ui.screens._utils``, which keeps non-UI, general-purpose
helpers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Sequence

from termux_tasker.ui.base import InfoScreen, InputScreen
from termux_tasker.ui.screens._utils import is_property_value_empty

if TYPE_CHECKING:
    from termux_tasker.app import TermuxTaskerApp


def ask_validated_input(
    app: TermuxTaskerApp,
    *,
    title: str,
    input_type: str = "text",
    current_value: Any = "",
    description: str = "",
    options: Sequence[Any] = (),
    is_valid: Callable[[Any], bool] = lambda _: True,
    on_valid: Callable[[Any], None],
    empty_message: str | None = None,
    invalid_message: str | None = None,
) -> None:
    """Prompt for input with interactive validation and re-prompting.

    Flow:
      - Show an ``InputScreen`` prefilled with ``current_value``.
      - ``None`` result cancels (nothing happens).
      - Empty value (only when ``empty_message`` is set) -> warning
        ``InfoScreen`` -> re-prompt.
      - Value failing ``is_valid`` (only when ``invalid_message`` is set)
        -> warning ``InfoScreen`` -> re-prompt.
      - Valid value -> ``on_valid(result)``.

    The same pattern is shared by ``PropertiesScreen`` (property editing)
    and ``TaskMenuScreen`` (timeout editing).
    """

    def _show_input() -> None:
        app.push_screen(
            InputScreen(
                title=title,
                input_type=input_type,
                current_value=current_value,
                description=description,
                options=list(options),
            ),
            _on_result,
        )

    def _warn(message: str) -> None:
        app.push_screen(
            InfoScreen(message=message, severity="warning"),
            lambda _: _show_input(),
        )

    def _on_result(result: Any) -> None:
        if result is None:
            return
        if empty_message is not None and is_property_value_empty(result, input_type):
            _warn(empty_message)
            return
        if invalid_message is not None and not is_valid(result):
            _warn(invalid_message)
            return
        on_valid(result)

    _show_input()
