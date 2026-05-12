Feature: Runners Screen
  As a user
  I want to manage runners from the runners screen
  So that I can view, install, and open runners

  Scenario: Runners screen polls and updates runner list
    Given the Runners screen is shown
    When a runner is installed or removed on disk
    Then the runner list is updated within 1 second
    And each runner shows its name with status in brackets: `<name> [<state>]`

  Scenario: Open runner menu from Runners screen
    Given the Runners screen is shown
    And there is at least one installed runner
    When I press a runner button
    Then the Runner Menu screen is pushed
    And the title is "Runner"
    And the subtitle is the runner's name

  Scenario: Navigate to install runner flow
    Given the Runners screen is shown
    When I press "Install Runner" button
    Then the Runner Type screen is pushed
    And it contains "Bundled" button
    And it contains "GitHub URL" button
    And it contains "Local Storage" button
    And it contains "Back" button
