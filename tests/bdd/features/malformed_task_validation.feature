Feature: Malformed Task Validation
  Scenario: Malformed task - missing required file
    Given the task `sh_runner_task_malformed_no_required_file` which has no `required_file`
    When the task is validated by the sh_runner's task validator
    Then validation fails because `test -f {task_dir}/required_file` returns non-zero

  Scenario: Malformed task - wrong runner version
    Given the task `sh_runner_task_malformed_wrong_runner_version` with `runner_min_version = ">=10.1.0"`
    And the installed runner has version "1.1.0"
    When the task is validated
    Then validation fails with a version compatibility error

  Scenario: Invalid GitHub URL
    Given the Runner Type / Task Type screen is shown
    When I press "GitHub URL" button
    And I enter an invalid URL (doesn't match GitHub URL regex)
    Then an error is shown
    And the install flow is aborted
