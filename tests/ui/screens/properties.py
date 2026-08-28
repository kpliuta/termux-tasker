from __future__ import annotations

import tempfile
from pathlib import Path

from textual.app import App
from textual import on
from textual.widgets import Button

from termux_tasker.config import PropertyDef, RunnerSettings
from termux_tasker.ui.screens.properties import PropertiesScreen


def _make_fake_item() -> Path:
    """Create a throwaway runner-like directory with sample settings."""
    item = Path(tempfile.mkdtemp(prefix="properties_preview_"))
    settings = RunnerSettings()
    settings.properties.update({"api-key": "secret-123", "region": "eu"})
    settings.save(item / "settings.toml")
    return item


class PropertiesScreenPreviewApp(App):
    """Standalone preview for the unified Properties screen.

    Shows a properties screen backed by a fake runner directory.
    Back returns to a bare exit screen.
    """

    PROPERTIES = [
        PropertyDef(
            name="api-key",
            description="Secret API key",
            input_type="text",
            optional=False,
        ),
        PropertyDef(
            name="region",
            description="Server region",
            input_type="radio",
            options=["eu", "us", "asia"],
            default="eu",
        ),
        PropertyDef(
            name="flags",
            description="Extra feature flags",
            input_type="checkbox",
            options=["verbose", "dry-run"],
        ),
        PropertyDef(
            name="note",
            description="Free-form note (optional)",
            input_type="text",
        ),
    ]

    def compose(self):
        yield Button("Exit preview", id="exit")

    def on_mount(self) -> None:
        self.push_screen(
            PropertiesScreen(
                _make_fake_item(), self.PROPERTIES, "Sample Runner"
            )
        )

    @on(Button.Pressed, "#exit")
    def on_exit(self) -> None:
        self.exit()


if __name__ == "__main__":
    app = PropertiesScreenPreviewApp()
    app.run()
