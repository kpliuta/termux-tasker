Feature: Task Menu
  As a user
  I want to manage a specific task from its menu
  So that I can toggle, configure, and uninstall it

  Scenario: Task menu displays correctly
    Given the Task Menu screen is shown for a task
    Then the description shows:
      """
      - Version
      - Enabled status
      - Session state
      - Timeout value
      - All configured properties with their values
      """
    And it contains "Enable"/"Disable" toggle button
    And it contains "Show metadata.toml" button
    And it contains "Show settings.toml" button
    And it contains "Set Timeout" button
    And it contains "Update" button
    And it contains "Uninstall" button
    And it contains "Back" button
    And for each property defined in metadata it contains "Set <property>" button

  Scenario: Toggle a task on/off
    Given the Task Menu screen is shown for a task
    When I press "Enable" / "Disable" button
    Then `settings.general.enabled` is toggled
    And the setting is saved
    And the menu item label updates accordingly

  Scenario: Set task timeout
    Given the Task Menu screen is shown
    When I press "Set Timeout" button
    Then an InputScreen is shown with the current timeout value
    When I enter a new timeout (e.g. "30s", "5m", "1h") and press Ok
    Then the timeout value is saved in settings.toml
    And the description is updated

  Scenario: Set task timeout with invalid format
    Given the Task Menu screen is shown
    When I press "Set Timeout" button
    Then an InputScreen is shown with the current timeout value
    When I enter an invalid timeout and press Ok
    Then a warning InfoScreen is shown
    And it shows "Invalid timeout format. Use e.g. 30s, 5m, 1h."
    When I dismiss the warning
    Then the InputScreen is shown again to retry

  Scenario: Set task timeout with empty value
    Given the Task Menu screen is shown
    When I press "Set Timeout" button
    Then an InputScreen is shown with the current timeout value
    When I clear the value and press Ok
    Then a warning InfoScreen is shown
    And it shows "Timeout is required and must have a value."
    When I dismiss the warning
    Then the InputScreen is shown again to retry

  Scenario: Update a task
    Given the Task Menu screen is shown
    When I press "Update" button
    Then the task directory is copied to a temporary location
    And the Install Task Version screen is shown

  Scenario: Uninstall a task
    Given the Task Menu screen is shown for a task
    When I press "Uninstall" button
    Then a confirmation dialog is shown
    And the message says "Are you sure you want to uninstall <name> task?"
    And it has "Yes" and "No" buttons

  Scenario: Confirm uninstall of a stopped task
    Given a task uninstall confirmation dialog is shown
    And the task state is "stopped"
    When I press "Yes" button
    Then a loading screen "Awaiting task termination" is shown
    And since it's already stopped, it proceeds immediately
    Then the task directory is deleted with `shutil.rmtree`
    And the screen is popped (back to Tasks screen)

  Scenario: Confirm uninstall of a running task
    Given a task uninstall confirmation dialog is shown
    And the task state is not "stopped"
    When I press "Yes" button
    Then a loading screen "Awaiting task termination" is shown
    And it waits (polling every 0.5s) until the task state becomes "stopped"
    Then the task directory is deleted
    And the screen is popped
