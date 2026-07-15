# Backlog

*Ordered by `priority desc` within each section. Bugs on the top.*

## In progress

* —

## Todo

* `high`   Bug: Runner doesn't change Enabled state to False after a critical error, even though State changes to Off correctly. Termination step should play "finally" block role
* `high`   Bug: Ghost processes are still hanging in the process list even though the runner is terminated (or tasker was killed)
* `high`   Implement possibility to kill the runner (1) from termination modal screen and (2) from runner menu
* `high`   Set settings_enable_monitor_phantom_procs on launching
* `medium` Bug: Close button on LogScreen is loosing its dimensions in some screen resolutions
* `medium` Bug: Local Storage should open FileBrowserScreen at /sdcard/ instead of ~/ in Termux env
* `medium` Bug: TUI hangs on picking up ~/.termux-tasker as Local Storage install
* `medium` Implement runner/task validation tools for external use
* `low`    Add an indicator to LogScreen showing watcher instance type when Auto-scroll is on
* `low`    Backspace key should behave the same way as Esc key
* `low`    ConfirmationScreen arrow keys navigation
* `low`    Move focus to radio buttons on InputScreen opening
* `low`    Implement Beginning/End navigation buttons on the LogScreen.
* `low`    Implement ability to install multiple similar tasks
* `low`    Implement manual update (minor version update should check installed runners for compatibility, major update - complete reinstalling of the app)
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

* —

## Cancelled

* —
