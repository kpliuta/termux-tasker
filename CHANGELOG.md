# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Added

- Unified **Properties** screen for runners and tasks: "Set <property>" buttons with live values shown as "**property**: value"; opened via a new "Properties" button on both menus.

### Changed

- Property editing moved off Runner/Task menus into the Properties screen; property values no longer shown in menu descriptions.
- `MenuScreen` updates button labels/disabled/titles in place instead of rebuilding the menu.
- Task Menu button id `set_timeout` → `timeout` (`set_` prefix now reserved for properties).
- Refactored `MenuScreen` to use `list[ButtonConfig]`; added `column_count`, `title`, Rich-markup descriptions, explicit disabled state, and TOP/BOTTOM layout.
- Renamed Main Menu → Dashboard (`DashboardScreen`).

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