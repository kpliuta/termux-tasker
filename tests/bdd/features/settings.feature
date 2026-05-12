Feature: Settings Screen
  Scenario: View and toggle upgrade on startup
    Given the Settings screen is shown
    Then it shows "Termux upgrade on startup" with current value (true/false)
    When I press the setting button
    Then an InputScreen with radio options (Yes/No) is shown
    When I select a value and press Ok
    Then the setting is saved to `app.toml`
    And the Settings screen description is updated
