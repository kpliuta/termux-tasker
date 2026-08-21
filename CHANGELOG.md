# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Changed

- Refactored `MenuScreen` to use `list[ButtonConfig]` instead of `dict[str, str]` for menu items. New `ButtonConfig` dataclass supports `label`, `id`, `variant`, `disabled`, `layout` (TOP/BOTTOM), and `title` (Rich markup above button).
- Description area now supports Rich markup formatting, arbitrary `Widget` content via `description_widget` param, and configurable max height via `description_max_height`.
- Button disabled state is now explicit via `ButtonConfig(disabled=True)` instead of implicit empty ID.
- Added `ButtonLayout` (TOP/BOTTOM) enum for flexible button placement.
- Replaced per-button style (`ButtonStyle`) with `column_count` on `MenuScreen` — all buttons (including Back/Exit) are arranged in uniform rows of `column_count` columns.

## [0.2.2] - 2026-07-31

### Fixed

- Runner, task, and app version lists now fetch remote git tags before showing available versions, so newly released versions appear on the Update screens.

## [0.2.1] - 2026-07-29

### Added

- tt-selenium-runner runner to bundled_runners.toml.

### Changed

- Remove main branch option from `install.sh`.

## [0.2.0] - 2026-07-15

### Added

- Manual app update from Settings screen with runner compatibility check.

### Changed

- Simplified `get_installed_runner_versions`/`get_installed_task_versions` to singular `get_installed_runner_version`/`get_installed_task_version` returning `Optional[str]` — only one installation per runner/task id is supported.

### Fixed

- Removed `main`/`master` from the version selection list in runner and task install/update flows. Only tagged versions (bare semver) are now selectable, fixing incorrect version display when installed from the main branch.

## [0.1.1] - 2026-07-13

### Changed

- Update AGENTS.md and README.md.

### Fixed

- BDD tests.