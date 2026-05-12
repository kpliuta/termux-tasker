Feature: Malformed Runner Validation
  Scenario: Malformed runner - no exec section
    Given the runner `sh_runner_malformed_no_exec` which has no `[exec]` section
    When the runner is validated
    Then validation fails with an appropriate error
