# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Added

- Dashboard now shows a live **System** block under the runners/tasks overview (refreshed every 1s): total CPU %, load averages, memory usage, live-runner count with aggregated RSS, and per-runner pid/RSS/CPU%/threads plus task running/total counts (plain text, stdlib `/proc`-based, no new dependencies).

### Fixed

- Dashboard total CPU % no longer sticks at `n/a` on kernels where the aggregate `cpu` line in `/proc/stat` is missing or not first: the parser scans all lines, falls back to summed per-core `cpuN` lines, and finally to summed per-PID counters (estimate) when `/proc/stat` itself is unreadable.

### Changed

- Disabled tasks on dashboard are now grayed out using `$foreground-disabled`.

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