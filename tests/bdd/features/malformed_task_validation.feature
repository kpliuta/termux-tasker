Feature: Malformed Task Validation

  Scenario: Invalid GitHub URL
    Given the Runner Type / Task Type screen is shown
    When I press "GitHub URL" button
    And I enter an invalid URL (doesn't match GitHub URL regex)
    Then an error is shown
    And the install flow is aborted
