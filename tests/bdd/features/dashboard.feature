Feature: Dashboard Navigation
  As a user
  I want to navigate the dashboard
  So that I can access runners, settings, and exit

  Scenario: Navigate to Runners screen
    Given the dashboard screen is shown
    When I press "Runners" button
    Then the Runners screen is shown
    And the title is "Runners"
    And it contains "Install Runner" button
    And it contains "Back" button

  Scenario: Navigate to Settings screen
    Given the dashboard screen is shown
    When I press "Settings" button
    Then the Settings screen is shown
    And the title is "Settings"
    And it shows "Termux upgrade on startup" option
    And it contains "Back" button

  Scenario: Exit app from dashboard (no runners)
    Given the dashboard screen is shown
    And no runners are running
    When I press "Exit" button
    Then the app exits immediately

  Scenario: Exit app with running runners shows confirmation
    Given the dashboard screen is shown
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
    And the dashboard screen is shown again
    And runners continue running

  Scenario: Exit via Ctrl+Q from any screen
    Given any screen is shown
    When I press Ctrl+Q
    Then the same exit flow is triggered as pressing "Exit" on the dashboard

  Scenario: Dashboard shows overview heading
    Given the dashboard screen is shown
    Then the dashboard description contains "Overview"

  Scenario: Dashboard shows no runners message when empty
    Given all runners are removed
    And the dashboard screen is shown
    Then the dashboard description contains "No runners installed"

  Scenario: Dashboard shows runner in overview
    Given the dashboard screen is shown
    And a runner "sh_runner" is installed with state "off"
    Then the dashboard description contains "Simple sh runner"
    And the dashboard description contains "[off]"

  Scenario: Dashboard shows task under runner in overview
    Given the dashboard screen is shown
    And a runner "sh_runner" is installed with state "idle"
    And the runner "sh_runner" has a task "sh_runner_task" with state "running"
    Then the dashboard description contains "Simple sh runner"
    And the dashboard description contains "Simple sh runner task"
    And the dashboard description contains "[running]"

  Scenario: Dashboard buttons are in 2 columns
    Given the dashboard screen is shown
    Then the dashboard has buttons arranged in 2 columns

  Scenario: Dashboard exit button is in bottom bar
    Given the dashboard screen is shown
    Then the "Exit" button is in the bottom bar
