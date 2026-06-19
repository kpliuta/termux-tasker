# Backlog

*Ordered by `priority desc` within each section. Bugs on the top.*

## In progress

* —

## Todo

* `high`   Bug: Runner doesn't change Enabled state to False after a critical error, even though State changes to Off correctly. Termination step should play "finally" block role
* `high`   Bug: Ghost processes are still hanging in the process list even though the runner is terminated (or tasker was killed)
* `high`   Implement possibility to kill the runner (1) from termination modal screen and (2) from runner menu
* `medium` Bug: If runner/installer is installed from main, the version is displayed incorrectly. As a solution the installed version could be kept in the metadata
* `medium` Bug: Close button on LogScreen is loosing its dimensions in some screen resolutions
* `medium` Bug: Local Storage should open FileBrowserScreen at /sdcard/ instead of ~/ in Termux env
* `medium` Bug: TUI hangs on picking up ~/.termux-tasker as Local Storage install
* `medium` Implement runner/task validation tools for external use
* `low`    Backspace key should behave the same way as Esc key
* `low`    ConfirmationScreen arrow keys navigation
* `low`    Move focus to radio buttons on InputScreen opening
* `low`    Implement LogScreen params (offset, follow state, soft-wrap) persistence in runner settings.
* `low`    Implement Clean button to set the LogScreen offset and Reset button that will reset the offset.
* `low`    Implement Beginning/End navigation buttons on the LogScreen.
* `low`    Implement ability to install multiple similar tasks
* `low`    Design autoupgrade mechanism, make it configurable (depends on deliverable format)
* `low`    Consolidate TCSS and layout for basic components
* `low`    Polish UI (TCSS) styling
* `low`    Move screen classes from base/screen to separate files and inline tcss for each one

## Investigation

* `high`   Determine deliverable format and how it will be executed on device
* `medium` How to sync git version and poetry version?
* `low`    Explore task-to-runner data sharing (install packages, patches, set runner settings)
* `low`    Investigate replacing timeout with cron-based scheduling

## Done

* `high`   Implement `{task_dir_name}` placeholder resolution (similar to `{task_path}`)
* `high`   Implement `{runner_path}` placeholder resolution for initialization, before-exec, after-exec, termination steps
* `high`   Introduce an output directory for task output resources (`$task_path/output`, create if not existed before task execution) with `$OUTPUT_DIR` env var passed to before-task, task-exec, after-task steps, and new item in task menu (visible only when output directory existed) which opens file viewer with only close button
* `high`   Rename `task_dir` → `task_path` and `runner_dir` → `runner_path` throughout the codebase
* `medium` Implement soft-wrap for LogScreen
* `low`    Implement true Follow for LogScreen instead of re-reading a file each time

## Cancelled

* —
