Feature: Tasks Screen
  As a user
  I want to manage tasks from the tasks screen
  So that I can view, install, and open tasks

  Scenario: Tasks screen shows installed tasks
    Given the Tasks screen is shown
    Then it shows all installed tasks under the runner
    And each task showing "<name> [enabled/disabled]" status
    And it contains "Install Task" button
    And it contains "Back" button

  Scenario: Open task menu from Tasks screen
    Given the Tasks screen is shown
    And there is at least one installed task
    When I press a task button
    Then the Task Menu screen is pushed
    And the title is "Task"
    And the subtitle is the task's name

  Scenario: Navigating back from Tasks screen returns to Runner menu
    Given the Tasks screen is shown
    When I press "Back" button (or Escape)
    Then the Runner Menu screen is shown again

  Scenario: Navigate to install task flow
    Given the Tasks screen is shown
    When I press "Install Task" button
    Then the Task Type screen is pushed
    And it contains "Bundled" button
    And it contains "GitHub URL" button
    And it contains "Local Storage" button
    And it contains "Back" button

  Scenario: Task list is refreshed after task uninstall
    Given the Tasks screen is shown
    And there is at least one task installed
    When I uninstall a task from its Task Menu screen
    And return to the Tasks screen
    Then the uninstalled task no longer appears in the list
