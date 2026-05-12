Feature: Runner Menu
  As a user
  I want to manage a specific runner from its menu
  So that I can toggle, configure, view logs, and uninstall it

  Scenario: Runner menu shows runner details
    Given the Runner Menu screen is shown for a runner
    Then the description shows:
      """
      - Version
      - Enabled status
      - Session state
      - All configured properties with their values
      """

  Scenario: Runner menu contains management buttons
    Given the Runner Menu screen is shown
    Then it contains "Enable"/"Disable" toggle button
    And it contains "Show Tasks" button
    And it contains "Show Runner Logs" button
    And it contains "Show metadata.toml" button
    And it contains "Show settings.toml" button
    And it contains "Update" button
    And it contains "Uninstall" button
    And it contains "Back" button
    And for each property defined in metadata it contains "Set <property>" button

  Scenario: Enable a runner
    Given the Runner Menu screen is shown
    And the runner is disabled
    When I press "Enable" button
    Then a new RunnerProcess is created
    And the runner is added to `app.state.runners`
    And `settings.general.enabled` is set to True
    And the runner's `run()` method is called
    And the menu item changes to "Disable"

  Scenario: Disable a runner
    Given the Runner Menu screen is shown
    And the runner is enabled and running
    When I press "Disable" button
    Then a loading screen "Runner shutting down" is shown
    And the runner process is shut down
    And the runner is removed from `app.state.runners`
    And `settings.general.enabled` is set to False
    Then the loading screen is dismissed
    And the menu item changes to "Enable"

  Scenario: Navigate to Tasks from Runner menu
    Given the Runner Menu screen is shown
    When I press "Show Tasks" button
    Then the Tasks screen is pushed
    And the title is "Tasks"
    And it shows all installed tasks for this runner (if any)
    And it contains "Install Task" button
    And it contains "Back" button

  Scenario: View runner logs
    Given the Runner Menu screen is shown
    When I press "Show Runner Logs" button
    Then a LogScreen is pushed with the runner's stdout file
    And follow mode is enabled

  Scenario: View runner metadata
    Given the Runner Menu screen is shown
    When I press "Show metadata.toml" button
    Then a LogScreen is pushed with the runner's metadata file
    And follow mode is disabled

  Scenario: Update a runner
    Given the Runner Menu screen is shown
    When I press "Update" button
    Then the runner directory is copied to a temporary location
    And the Install Runner Version screen is pushed

  Scenario: Set a runner property
    Given the Runner Menu screen is shown
    And the runner metadata defines a property
    When I press "Set <property>" button
    Then an InputScreen is shown for that property
    And the correct input type (text/radio/checkbox)
    And the current value is pre-populated
    And the property description is shown
    When I enter a valid value and press Ok
    Then the property value is saved in settings.toml
    And the runner description is updated

  Scenario: Set a required runner property with empty value shows warning
    Given the Runner Menu screen is shown
    And the property is non-optional
    When I press "Set <property>" button
    And I clear the value and press Ok
    Then a warning InfoScreen is shown
    And it says "'<property>' is required and must have a value."
    When I dismiss the warning
    Then the InputScreen is shown again to retry

  Scenario: Cancel setting a runner property
    Given the Runner Menu screen is shown
    When I press "Set <property>" button
    And I press "Cancel" (or Escape)
    Then the property value is unchanged

  Scenario: Uninstall a runner
    Given the Runner Menu screen is shown for a runner
    When I press "Uninstall" button
    Then a confirmation dialog is shown
    And the message says "Are you sure you want to uninstall <name> runner?"
    And it has "Yes" and "No" buttons

  Scenario: Confirm uninstall of an idle runner
    Given a runner uninstall confirmation dialog is shown
    And the runner state is "off"
    When I press "Yes" button
    Then the runner directory is deleted with `shutil.rmtree`
    And the current screen is popped (back to Runners screen)

  Scenario: Confirm uninstall of a running runner
    Given a runner uninstall confirmation dialog is shown
    And the runner state is not "off"
    When I press "Yes" button
    Then a loading screen "Runner shutting down" is shown
    And the runner process is shut down
    And the runner is removed from `app.state.runners`
    And `settings.general.enabled` is set to False
    And the settings are saved
    And the runner directory is deleted
    And the current screen is popped (back to Runners screen)

  Scenario: Cancel uninstall of a runner
    Given a runner uninstall confirmation dialog is shown
    When I press "No" button
    Then the dialog is dismissed
    And the runner remains intact
