Feature: Task Installation
  As a user
  I want to install tasks from various sources
  So that I can add new tasks to runners

  Scenario: Install task from bundled list
    Given the Task Type screen is shown
    When I press "Bundled" button
    Then the Bundled Task screen is shown
    And bundled tasks are fetched from the runner's `bundled.toml`
    And each task repository is cloned
    And the runner's task validator is run to check metadata

  Scenario: Install task from GitHub URL
    Given the Task Type screen is shown
    When I press "GitHub URL" button
    Then an InputScreen is shown for URL entry
    When I enter a valid GitHub URL and press Ok
    Then the repository is cloned
    And metadata is validated
    Then the Install Task screen is shown

  Scenario: Install task from local storage
    Given the Task Type screen is shown
    When I press "Local Storage" button
    Then a FileBrowserScreen is shown in folder selection mode
    When I select a folder and press "Select"
    Then the folder is copied to a temporary directory
    And metadata is validated
    Then the Install Task screen is shown

  Scenario: Install task - post-install navigation
    Given a task is successfully installed
    Then the install screens are popped back to the Runner Menu screen
    And the Task Menu screen is shown
    And the newly installed task is visible in the list

  Scenario: Navigate back from Task Menu to Tasks Menu
    Given the Task Menu screen is shown for an installed task
    When I press "Back" button (or Escape)
    Then the screen is popped
    And the Tasks screen is shown

  Scenario: Cancel required property during task install re-prompts
    Given I am installing a task with non-optional properties without defaults
    When I cancel the property prompt
    Then a warning InfoScreen is shown that the property is required
    When I dismiss the warning
    Then the same property InputScreen is shown again
    When I provide a valid value and press Ok
    Then the next property is prompted
