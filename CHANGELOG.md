# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

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