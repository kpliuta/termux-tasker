# Backlog

*Ordered by `priority desc` within each section.*

## In progress

* —

## Todo

* `medium` Implement runner/task validation tools for external use
* `low`    Implement ability to install multiple similar tasks
* `low`    Design autoupgrade mechanism, make it configurable (depends on deliverable format)
* `low`    Consolidate TCSS and layout for basic components
* `low`    Polish UI (TCSS) styling

## Investigation

* `high`   Determine deliverable format and how it will be executed on device
* `low`    Explore task-to-runner data sharing (install packages, patches, set runner settings)
* `low`    Investigate replacing timeout with cron-based scheduling

## Done

* `high`   Implement `{task_dir_name}` placeholder resolution (similar to `{task_path}`)
* `high`   Implement `{runner_path}` placeholder resolution for initialization, before-exec, after-exec, termination steps
* `high`   Introduce an output directory for task output resources (`$task_path/output`, create if not existed before task execution) with `$OUTPUT_DIR` env var passed to before-task, task-exec, after-task steps, and new item in task menu (visible only when output directory existed) which opens file viewer with only close button
* `high`   Rename `task_dir` → `task_path` and `runner_dir` → `runner_path` throughout the codebase

## Cancelled

* —
