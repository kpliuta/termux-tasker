# Termux Tasker

A TUI tool for managing shell-based automation tasks on Termux (Android). Built with [Textual](https://textual.textualize.io/).

## Overview

Termux Tasker provides a terminal UI to run and monitor shell-based automation on Termux (Android).

- **Runner** — defines **how** to execute tasks. A runner is a shell script runner that follows a defined lifecycle (init → before-exec → task loop → after-exec → termination).
- **Task** — defines **what** to execute. A task is a unit of work assigned to a runner.

## Architecture

```
src/termux_tasker/
├── app.py                # App entry point & lifecycle
├── app_state.py          # Global state (directories, runners, sessions)
├── config.py             # TOML-based config models (dataclasses + caching)
├── runner_process.py     # Runner execution loop (asyncio-based)
├── runner_validator.py   # Runner metadata & structure validation
├── task_validator.py     # Task metadata & runner-compatibility validation
├── resources/
│   ├── default.app.toml        # Default app config
│   └── bundled_runners.toml    # Built-in runner URLs
└── ui/
    ├── base/
    │   └── screen.py     # Shared screens (MenuScreen, InputScreen,
    │                     #   InfoScreen, ConfirmationScreen, LoadingScreen,
    │                     #   LogScreen, FileBrowserScreen)
    └── screens/
        ├── _utils.py                   # Git operations, property helpers
        ├── main_menu.py                # Entry screen
        ├── settings.py                 # App settings screen
        ├── runners.py                  # Installed runners list screen
        ├── runner_menu.py              # Runner management screen
        ├── runner_type.py              # Install source selection screen
        ├── bundled_runner.py           # Browse bundled runners screen
        ├── install_runner.py           # Confirm runner install screen
        ├── install_runner_version.py   # Version selection & install screen
        ├── tasks.py                    # Installed tasks list screen
        ├── task_menu.py                # Task management screen
        ├── task_type.py                # Install source selection screen
        ├── bundled_task.py             # Browse bundled tasks screen
        ├── install_task.py             # Confirm task install screen
        └── install_task_version.py     # Version selection & install screen
```

### Data flow

1. App starts → creates work directories (`~/.termux-tasker/`) → shows **Main Menu**.
2. User navigates to **Runners** → sees installed runners (polled every 1s from disk).
3. User presses **Install Runner** → selects source (Bundled / GitHub URL / Local) → repository is cloned/copied → metadata validated → version selected → runner installed under `runners/<id>/`.
4. From **Runner Menu**, user can enable/disable, view logs, set properties, or open **Tasks**.
5. User presses **Install Task** from **Tasks Screen** → selects source (Bundled / GitHub URL / Local) → repository cloned/copied → metadata validated (runner compatibility + custom validators) → version selected → task installed under `runners/<runner_id>/tasks/<task_id>/`.
6. When a runner is **enabled**, it starts an asyncio loop executing shell commands through its defined lifecycle phases.
7. The runner iterates over all enabled tasks, skipping those whose timeout hasn't elapsed since last run.

### Configuration model (TOML)

All configuration is TOML-based, stored under `~/.termux-tasker/`:

| File                                    | Purpose                                                           |
|-----------------------------------------|-------------------------------------------------------------------|
| `app.toml`                              | Global app settings                                               |
| `runners/<id>/metadata.toml`            | Runner definition (id, name, version, properties, exec commands)  |
| `runners/<id>/settings.toml`            | Runner runtime state (enabled, timeout, property values, session) |
| `runners/<id>/tasks/<id>/metadata.toml` | Task definition (id, name, version, runner_id, default_timeout)   |
| `runners/<id>/tasks/<id>/settings.toml` | Task runtime state (enabled, timeout, property values, session)   |

Configuration use class-level instance caching (`_instances` dict) for performance. Call `clear_cache(path)` to invalidate when files change on disk.

### Runner lifecycle

```
initialization
     ↓
 before-exec  ──→ for each enabled task ──→ after-exec  ──→ idle (sleep timeout)
                      ├─ before-task                         ↓
                      ├─ task-exec (run command)          shutdown → termination → off
                      └─ after-task
```

Runner processes are managed via `RunnerProcess` (asyncio). Each runs shell commands with environment variables `VAR_<PROPERTY_NAME>` for configured properties.

## Installation

```bash
# Production
poetry install

# Development
poetry install --with dev
```

Requires **Python ≥3.13** and dependencies: `textual`, `tomlkit`, `packaging`.

## Usage

```bash
# Launch the TUI
poetry run termux-tasker
```

### Key bindings

| Key       | Action                |
|-----------|-----------------------|
| `Escape`  | Back / Cancel / Close |
| `Ctrl+Q`  | Exit app              |
| `↑` / `↓` | Navigation            |

### Screen flow

```
Main Menu
├── Show Runners → Runners Screen 
│   ├── [Runner] → Runner Menu
│   │   ├── Enable/Disable (starts/stops the runner loop)
│   │   ├── Show Tasks → Tasks Screen
│   │   │   ├── [Task] → Task Menu
│   │   │   │   ├── Enable/Disable
│   │   │   │   ├── Show metadata/settings (view files)
│   │   │   │   ├── Set Timeout
│   │   │   │   ├── Set Properties
│   │   │   │   ├── Update (version selection)
│   │   │   │   └── Uninstall
│   │   │   └── Install Task (source selection → install flow)
│   │   ├── Show Runner Logs (follow mode)
│   │   ├── Show metadata/settings (view files)
│   │   ├── Set Properties
│   │   ├── Update (version selection)
│   │   └── Uninstall
│   └── Install Runner (source selection → install flow)
└── Settings
```

## Development

### Test structure

```
tests/
├── bdd/                    # Behavior-Driven Development tests (pytest-bdd)
│   ├── features/           # Gherkin feature files
│   ├── helpers/            # Test helpers (UI, settings, file system, validation)
│   ├── conftest.py         # pytest fixtures (pilot, app state, runner dirs)
│   ├── given_steps.py      # Given step implementations
│   ├── when_steps.py       # When step implementations
│   ├── then_steps.py       # Then step implementations
│   └── steps_common.py     # Shared imports and utilities
├── unit/                   # Unit tests
└── ui/                     # Manual UI component previews (textual-dev)
```

### Running tests

```bash
# Unit tests
poetry run python -m pytest tests/unit/ -v

# BDD tests
poetry run python -m pytest tests/bdd/ -v

# Run a specific BDD scenario by name
poetry run python -m pytest tests/bdd/ -v -k "navigate_back_from_task_menu_to_tasks_menu"

# All tests
poetry run python -m pytest tests/ -v
```

### UI component previews (manual)

```bash
poetry run python -m textual_dev run --dev tests/ui/base/menu_screen.py
poetry run python -m textual_dev run --dev tests/ui/base/input_screen.py
poetry run python -m textual_dev run --dev tests/ui/base/info_screen.py
poetry run python -m textual_dev run --dev tests/ui/base/loading_screen.py
poetry run python -m textual_dev run --dev tests/ui/base/log_screen.py
poetry run python -m textual_dev run --dev tests/ui/base/file_browser_screen.py
```

### Key test fixtures (conftest.py)

- `app_state_fixture` — bootstraps `~/.termux-tasker/` with a pre-installed `sh_runner` and `sh_runner_task`
- `pilot` — Textual pilot for driving the TUI in tests
- `sh_runner_dir`, `sh_runner_task_dir` — paths to test fixture runner/task directories
- `sh_runner_malformed_no_exec_dir` — malformed runner fixture for validation tests
- `sh_runner_task_no_required_file_dir`, `sh_runner_task_wrong_version_dir` — malformed task fixtures
