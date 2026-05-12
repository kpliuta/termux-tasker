Feature: Task Validation
  As a user
  I want tasks to be validated before installation
  So that only compatible and correctly structured tasks are installed

  Scenario: Validate task - runner version compatibility
    Given a task specifies `runner_min_version = ">=10.1.0"`
    And the installed runner has version "1.1.0"
    When the task validator runs
    Then validation fails because the runner version is incompatible

  Scenario: Validate task - runner version compatible
    Given a task specifies `runner_min_version = ">=1.1.0,<2.0.0"`
    And the installed runner has version "1.1.0"
    When the task validator runs
    Then validation passes
