# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Added

- Screens with a Back button now also show a `🏠` Home button, that pops the screen stack back to the Dashboard (except Runners and Settings).
- Dashboard now has a `❓` Help button in the bottom bar. Settings (`🔧`) and Runners buttons moved to the bottom bar as well in a 3-column row.
- Dashboard now shows live system resource monitoring: CPU/MEM gradient bars, plus a `PID <root>+<children> RSS <bytes>` line under each runner with live processes, hidden when the runner is stopped.
- Runner Menu now shows live `PID`, `RSS`, and `Last Run` rows (`n/a` when idle/never run).
- Runner Menu lifecycle states now carry timer suffixes: previous-run duration on every timed state, a live elapsed timer on the active state, `exec [i/n]` task progress while tasks run, and an `idle` countdown to the next iteration.
- Dashboard runner headers now show the same `idle` countdown (`[idle][MM:SS]`) while a runner is idle.
- Task Menu now shows `Last Run` and `Last Status` rows (`n/a` when never run).
- Task Menu lifecycle states now carry timer suffixes: `running` shows summed task-phase durations plus live elapsed time, `stopped` shows the parent runner's idle countdown while the runner is idle and the task is enabled.

### Changed

- Disabled tasks on dashboard are now grayed out using `$foreground-disabled`.
- Split the shared `RunnerSettings`/`TaskSettings` alias into independent `RunnerSettings`/`TaskSettings` classes.
- Runner `settings.toml [session]` now records `last_run` (`"YYYY-MM-DD HH:MM:SS"`, UTC) at the start of each execution cycle.
- Task `last_run` is stamped at task-block entry for the same reason.
- Task `settings.toml [session]` now records `last_run_before_duration`, `last_run_exec_duration`, `last_run_after_duration` (int seconds, per-phase wall time, omitted until the first run, written on both success and failure).
- Runner `settings.toml [session]` now records `last_run_init_duration`, `last_run_before_duration`, `last_run_exec_duration` (whole task-loop wall time), `last_run_after_duration`, `last_run_termination_duration` (int seconds, omitted until run, written even when a step fails).
- Status/description text now uses Textual `Content` with `$var` span styles instead of Rich `Text` with pre-resolved hexes: theme colors resolve at render (theme switching works live), and the hex-translation layer is deleted.

### Fixed

- Task Menu no longer resets a genuinely `running` task to `stopped` when opened mid-run: the runner now adopts `session_id` and stamps `last_run` (UTC start time) at task-block entry, so mid-run polling never sees a stale session.
- Task `success`/`fail` status now covers the whole task block (`before-task`/`after-task` failures also record `fail` instead of leaving a stale status).
- Rate-limit comparison is timezone-aware (UTC on both sides). Runner/task log timestamps are UTC like the files. Previously the naive-local comparison was off by the UTC offset.

## [0.3.0] - 2026-08-28

### Added

- Unified **Properties** screen for runners and tasks (new "Properties" button on both menus; "Set <property>" buttons show live `property: value`).
- `DashboardScreen` now displays a live overview of all runners and tasks.

### Changed

- Main Menu renamed → Dashboard (`DashboardScreen`).
- Property values removed from menu descriptions.
- Reworked menu descriptions into reusable `MenuScreen` description widgets: `KeyValueWidget` and `StateWidget` (key/value rows + lifecycle state list).
- `MenuScreen`: `list[ButtonConfig]`, in-place updates, `column_count`, `title`, Rich-markup descriptions, disabled state, TOP/BOTTOM layout.
- Extracted shared `ask_validated_input` helper (validated input with re-prompt) for `PropertiesScreen` and `TaskMenuScreen`.
- `SettingsScreen` shows App Version / Session ID via `KeyValueWidget` instead of a plain description string.
- Runner menu buttons renamed: "Show Tasks" → "Tasks", "Show Runner Logs" → "Logs".
- Bracketed status captions colored: `[enabled]`/`[Installed]`/`[true]` → `$text-success`, `[disabled]`/`[false]` → `$text-error`.
- Migrated state colors from `$success`/`$warning`/`$error` to `$text-success`/`$text-warning`/`$text-error`.

## [0.2.2] - 2026-07-31

### Fixed

- Runner, task, and app version lists now fetch remote git tags before showing available versions, so newly released versions appear on the Update screens.

## [0.2.1] - 2026-07-29

### Added

- tt-selenium-runner runner to bundled_runners.toml.

### Changed

- Removed main branch option from `install.sh`.

## [0.2.0] - 2026-07-15

### Added

- Manual app update from Settings screen with runner compatibility check.

### Changed

- Simplified `get_installed_runner_versions`/`get_installed_task_versions` to singular `get_installed_runner_version`/`get_installed_task_version` returning `Optional[str]` — only one installation per runner/task id is supported.

### Fixed

- Removed `main`/`master` from the version selection list in runner and task install/update flows. Only tagged versions (bare semver) are now selectable, fixing incorrect version display when installed from the main branch.

## [0.1.1] - 2026-07-13

### Changed

- Updated AGENTS.md and README.md.

### Fixed

- BDD tests.