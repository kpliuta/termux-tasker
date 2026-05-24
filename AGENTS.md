[//]: # (identity)

- You are an experienced Python engineer.
- MEMORY.md is your cross-session memory for this project. Read it at session start to get up to speed fast. If it doesn't exist, analyze the project file by file and create it.
- If something is unclear, analyze the codebase deeper and update MEMORY.md.
- When introducing new conventions, libraries, patterns, or project structure changes, update MEMORY.md immediately.
- Keep AGENTS.md and MEMORY.md up to date — update after any codebase change.
- Stay consistent with existing patterns and code style.

[//]: # (workflow)

- Ask before starting if anything is unclear.
- Cover new/modified logic with both BDD and unit tests; run after each change — must be green. Tests always run in parallel (`-n auto` default in pyproject.toml).
- Delete all unused code (methods, classes, files, imports).
- Run `poetry run mypy src/` and `poetry run autoflake --remove-all-unused-imports --ignore-init-module-imports --in-place --recursive src/` after every change — both must pass/be clean.
- Update README.md for user-visible changes.

[//]: # (python)

- `from __future__ import annotations` at the top of every file.
- Type hints on all function signatures and dataclass fields.
- Early returns / guard clauses for error handling; happy path last.
- Descriptive variable names with auxiliary verbs: `is_active`, `has_permission`.
- `@dataclass` for data models; `tomlkit` for TOML I/O via `_write_toml` helper.
- `Path` for all filesystem paths — never raw strings.
- Prefer modules+functions over classes; use classes primarily for UI screens.

[//]: # (textual)

- Subclass `MenuScreen` for feature screens; pass `menu_items: dict[str, str]` (label→button_id).
- Handle button events with `@on(Button.Pressed, "#button_id")` — always `event.stop()`.
- Use `termux_app(self)` from `_utils.py` for typed app access — prefer over `self.app` everywhere in feature screens (but `self.app` is fine in base screens in `ui/base/`).
- `BINDINGS` list for keyboard shortcuts: `[("escape", "press_back", "Back")]`.
- `push_screen(screen, callback)` for modals; callback receives dismissed screen's result.
- `self.run_worker(self._async_method())` for async work from sync contexts.
- CSS files named `{screen_name}.tcss` alongside the Python file:
  ```python
  _HERE = Path(__file__).parent
  CSS_PATH = _HERE / "menu_screen.tcss"
  ```
- Import all base screen types from `termux_tasker.ui.base.screen` (never re-import from individual files).

[//]: # (testing — BDD)

- BDD tests: `tests/bdd/features/*.feature` + step definitions in `tests/bdd/{given,thens,when}_steps.py`.
- Step definitions import: `from tests.bdd.steps_common import *  # noqa`.
- `pilot` fixture → `PilotDriver`; use `ui(pilot)` helper for all interactions.
- Put pure-logic tests (no UI) as unit tests, not BDD. BDD is for UI flows only.
- External operations (git, network) mocked in `conftest.py` via `mock_external_ops` auto use fixture.
- Merging multiple Given-When-Then blocks in a single scenario doesn't work (state leaks). Instead, merge more `And` assertions into a single flow or keep scenarios separate.

[//]: # (testing — pilot interactions)

- `ui(pilot).click_id("#button_id")` for known IDs, `ui(pilot).click_label("Button Text")` for label lookup.
- `ui(pilot).assert_screen(ScreenType)` and `ui(pilot).pause()` for navigation/assertions.
- `ui(pilot).press("escape")` sends key event; use `pause()` between actions to drain event loop.
- `ui(pilot).set_value("#input_field", value)` for text inputs.
- `pilot.pause(0.02)` yields to event loop for UI updates. Avoid long fixed pauses — use short pause + assertion loops.

[//]: # (testing — unit)

- Unit tests in `tests/unit/` — plain pytest, no BDD.
- Mock external dependencies; avoid `torch`.
- All tests run in parallel by default (`-n auto`). For serial debugging: `pytest -n 0`.
- Fixtures for runner/task directories defined in `tests/bdd/conftest.py`.
