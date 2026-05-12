Feature: Main Menu Navigation
  As a user
  I want to navigate the main menu
  So that I can access runners, settings, and exit

  Scenario: Navigate to Runners screen from main menu
    Given the main menu screen is shown
    When I press "Show Runners" button
    Then the Runners screen is shown
    And the title is "Runners"
    And it contains "Install Runner" button
    And it contains "Back" button

  Scenario: Navigate to Settings screen from main menu
    Given the main menu screen is shown
    When I press "Settings" button
    Then the Settings screen is shown
    And the title is "Settings"
    And it shows "Termux upgrade on startup" option
    And it contains "Back" button

  Scenario: Exit app from main menu (no runners)
    Given the main menu screen is shown
    And no runners are running
    When I press "Exit" button
    Then the app exits immediately

  Scenario: Exit app with running runners shows confirmation
    Given the main menu screen is shown
    And at least one runner is running
    When I press "Exit" button
    Then a confirmation dialog is shown with message "Are you sure you want terminate runners in progress and exit?"
    And it contains "Yes" button
    And it contains "No" button

  Scenario: Confirm exit with running runners
    Given a confirmation dialog is shown for exiting with running runners
    When I press "Yes" button
    Then a loading screen "Runners shutting down" is shown
    And all runners are shut down
    And each runner's settings have `enabled = False`
    Then the loading screen is dismissed
    And the app exits

  Scenario: Cancel exit with running runners
    Given a confirmation dialog is shown for exiting with running runners
    When I press "No" button
    Then the confirmation dialog is dismissed
    And the main menu screen is shown again
    And runners continue running

  Scenario: Exit via Ctrl+Q from any screen
    Given any screen is shown
    When I press Ctrl+Q
    Then the same exit flow is triggered as pressing "Exit" on the main menu
