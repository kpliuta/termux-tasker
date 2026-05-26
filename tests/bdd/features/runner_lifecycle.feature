Feature: Runner Execution Lifecycle
  As a user
  I want the runner to execute tasks through a defined lifecycle
  So that initialization, execution, and cleanup happen properly

  Scenario: Runner starts and goes through lifecycle states
    Given a runner is enabled
    When the runner's `run()` method is called
    Then the state transitions to "initialization"
    And the initialization command is executed
    Then the runner enters a loop:
      """
      - "before-exec" state: before-exec command is executed
      - "before-task" state: for each enabled task, before-task command is executed (with `{task_path}`)
      - "task-exec" state: for each enabled task, task command is executed
      - "after-task" state: after-task command is executed
      - "after-exec" state: after-exec command is executed
      - "idle" state: sleeps for the configured timeout duration
      """
    When the runner is shut down
    Then the state transitions to "termination"
    And the termination command is executed
    Then the state transitions to "off"

  Scenario: Runner environment variables
    Given a runner is executing a command
    Then the environment contains:
      """
      - All OS environment variables
      - `VAR_<property_name>` for each runner property
      - `VAR_<property_name>` for each task property (when executing task commands)
      """
    And property names are converted to uppercase with non-alphanumeric chars replaced by underscores

  Scenario: Runner skips disabled tasks
    Given a runner has both enabled and disabled tasks
    When the runner's execution loop reaches task iteration
    Then disabled tasks are skipped
    And the runner proceeds to the next task

  Scenario: Runner respects task timeout
    Given a task is configured with `settings.general.timeout = "30s"`
    When the runner's execution loop enters "idle" state
    Then it sleeps for 30 seconds before the next iteration
