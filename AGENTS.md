[//]: # (identity)

- You are an experienced Python engineer.
- MEMORY.md is your cross-session memory for this project. Read it at session start to get up to speed fast. If it doesn't exist, analyze the project file by file and create it.
- If something is unclear, analyze the codebase deeper and update MEMORY.md.
- When introducing new conventions, libraries, patterns, or project structure changes, update MEMORY.md immediately.
- Keep AGENTS.md and MEMORY.md up to date — update after any codebase change.
- Stay consistent with existing patterns and code style.

[//]: # (workflow)

- Ask before starting if anything is unclear.
- FOLLOW TDD — strict red-green-refactor order, see the dedicated section below. Tests always run in parallel (`-n auto` default in pyproject.toml).
- Delete all unused code (methods, classes, files, imports).
- Run `poetry run mypy src/` and `poetry run autoflake --remove-all-unused-imports --ignore-init-module-imports --in-place --recursive src/` after every change — both must pass/be clean.
- Update README.md for user-visible changes.
- Update CHANGELOG.md (add entries under `## [Unreleased]`) and BACKLOG.md (move completed items, update status) for every commit.
- Use all the skills under .agent/skills/* where applicable.

[//]: # (tdd)

- Strict red-green-refactor order for every behavior change — no `src/` edits before step 1 is done:
  1. RED — write the failing BDD scenario + unit tests first, run them, confirm they fail for the expected reason.
  2. GREEN — implement the minimal `src/` change that makes them pass.
  3. REFACTOR — clean up while keeping tests green; re-run.
- The only exceptions are pure refactors already covered by green tests, test-only changes, and docs.
- New/modified logic needs both BDD (UI flows) and unit (pure logic) coverage; run the affected tests after each change and the full suite before finishing — must be green.
- Plan test steps before implementation steps in TodoWrite.

[//]: # (python)

- `from __future__ import annotations` at the top of every file.
- Type hints on all function signatures and dataclass fields.
- Early returns / guard clauses for error handling; happy path last.
- Descriptive variable names with auxiliary verbs: `is_active`, `has_permission`.
- `@dataclass` for data models; `tomlkit` for TOML I/O via `_write_toml` helper.
- `Path` for all filesystem paths — never raw strings.
- Prefer modules+functions over classes; use classes primarily for UI screens.
- Never use broad exception clauses (`except Exception:` / bare `except:`). Catch only the specific exception(s) you expect (e.g. `NoMatches` from `textual.widget`). A broad clause is acceptable only when immediately re-raising a wrapped, domain-specific exception.

[//]: # (textual)

- Subclass `MenuScreen` for feature screens; pass `menu_items: list[ButtonConfig]` (import `ButtonConfig` from `termux_tasker.ui.base`).
- One-way UI layering: `ui/base/` must never reference `ui/screens/` — not even via lazy/local imports inside handlers.
- Use `ButtonConfig(id, label, variant, disabled, layout, title)` for button configuration.
- `ButtonLayout.TOP` (default) places buttons in the scroll area; `ButtonLayout.BOTTOM` places them in the bottom bar.
- `column_count` (default 1) controls how many buttons appear per row — applies uniformly to all buttons including Back/Exit.
- Set `title="[b]Header[/b]"` on a `ButtonConfig` to show formatted text above the button (Rich markup supported).
- `ButtonConfig.id` is **required**: non-empty and a valid Textual identifier (validated in `__post_init__`). Ids must be unique per screen — `MenuScreen` raises `ValueError` on duplicates at construction and on every runtime `menu_items` reassignment.
- Never name helpers `_validate_<reactive>` / `validate_<reactive>` inside `MenuScreen` subclasses — Textual treats them as reactive value validators and their return value replaces the attribute.
- Handle button events with `@on(Button.Pressed, "#button_id")` — always `event.stop()`.
- Use `termux_app(self)` from `_utils.py` for typed app access — prefer over `self.app` everywhere in feature screens (but `self.app` is fine in base screens in `ui/base/`).
- `BINDINGS` list for keyboard shortcuts: `[("escape", "press_back", "Back")]`.
- `push_screen(screen, callback)` for modals; callback receives dismissed screen's result.
- `self.run_worker(self._async_method())` for async work from sync contexts.
- CSS files in `./tcss/` subdirectory:
  ```python
  _HERE = Path(__file__).parent
  CSS_PATH = _HERE / "tcss" / "menu_screen.tcss"
  ```
- Import all base screen types from `termux_tasker.ui.base` (never re-import from individual files).
- Description can be `str` (with Rich markup) or a `Widget` instance — use `description` and `description_widget` params.
- `description_max_height` controls the description area height (default "100%").
- Reassigning `self.menu_items` updates labels/disabled/titles **in place** when button ids are unchanged (no rebuild, focus preserved); changing the id set triggers a full DOM rebuild.
- Runner/task property editing lives in the unified `PropertiesScreen` (`ui/screens/properties.py`); menus only push it via a "Properties" button. Button ids prefixed `set_` are reserved for property buttons.
- Status/description text uses `Content` with theme-variable span styles (e.g. `Content.assemble(("[01:33]", "$foreground-disabled"))`) — never Rich `Text` spans. `Content` spans resolve `$vars` via the widget theme at render. Hex is only for computed colors (dashboard gradient bars) and the `KeyValueWidget` key column (resolved via `get_css_variables()`, rebuilt on mount).

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

[//]: # (entry point)

- `run.sh` is the Termux entry point; installs Python + Poetry, then runs the app.
- Pass `--skip-android-init` to bypass Termux checks (local dev on PC).
- `main()` in `app.py` parses `sys.argv` for `--skip-android-init`.
- BDD tests always create the app with `skip_android_init=True`.
- `android_init.py` contains async checks (Termux env, storage, packages, upgrade) called from `on_mount()`.
