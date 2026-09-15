# Backlog

*Ordered by `priority desc` within each section. Bugs on the top.*

## In progress

* —

## Todo

* `high`   Bug: UI gets irresponsive while executing heavy tasks (during tt-selenium-runner initialization)
* `high`   Bug: Acquire wake-lock on the startup
* `high`   Bug: Runner doesn't change Enabled state to False after a critical error, even though State changes to Off correctly. Termination step should play "finally" block role
* `high`   Bug: Ghost processes are still hanging in the process list even though the runner is terminated (or tasker was killed)
* `high`   Bug: Task's default_timeout is not taken into account
* `high`   Doc: Establish repo/project naming for runners/tasks
* `high`   Doc: Simplify docs - separate User from Developer docs
* `high`   Implement possibility to kill the runner (1) from termination modal screen and (2) from runner menu
* `high`   Set settings_enable_monitor_phantom_procs on launching
* `medium` Bug: Local Storage should open FileBrowserScreen at /sdcard/ instead of ~/ in Termux env
* `medium` Bug: TUI hangs on picking up ~/.termux-tasker as Local Storage install
* `medium` Implement runner/task validation tools for external use
* `medium` Show the task in progress in the description section in RunnerScreen
* `low`    Bug: "Failed to check out tag" message on update if any change was made to codebase manually
* `low`    Bug: Add root element to tcss of each base screen, as it can affect parent screen style
* `low`    Create ./run shortcut in ~/.shortcuts in ./install.sh for a Termux shortcut widget
* `low`    Line length is too long and doesn't fit to the screen when LogScreen's word-wrap is on
* `low`    Add an app alias creation to install.sh
* `low`    Backspace key should behave the same way as Esc key
* `low`    ConfirmationScreen arrow keys navigation
* `low`    Move focus to radio buttons on InputScreen opening
* `low`    Implement ability to install multiple similar tasks
* `low`    Design autoupgrade mechanism, make it configurable (depends on deliverable format)

## Investigation

* `high`   Determine deliverable format and how it will be executed on device
* `low`    Explore task-to-runner data sharing (install packages, patches, set runner settings)
* `low`    Investigate replacing timeout with cron-based scheduling
* `low`    UI/UX best practices course (TUI in particular?)
* `low`    Runner tracing screen with duration spent on each step

## Done

* —

## Cancelled

* —
