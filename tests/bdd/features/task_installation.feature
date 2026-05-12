Feature: Task Installation
  As a user
  I want to install tasks from various sources
  So that I can add new tasks to runners

  Scenario: Install task from bundled list
    Given the Task Type screen is shown
    When I press "Bundled" button
    Then the Bundled Task screen is pushed
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
    Then the Install Task screen is pushed

  Scenario: Install task from local storage
    Given the Task Type screen is shown
    When I press "Local Storage" button
    Then a FileBrowserScreen is shown in folder selection mode
    When I select a folder and press "Select"
    Then the folder is copied to a temporary directory
    And metadata is validated
    Then the Install Task screen is pushed

  Scenario: Install task - post-install navigation
    Given a task is successfully installed
    Then the install screens are popped back to the Runner Menu screen
    And the Tasks screen is pushed
    And the newly installed task is visible in the list

  Scenario: Navigate back from Task Menu to Runner Menu
    Given the Task Menu screen is shown for an installed task
    When I press "Back" button (or Escape)
    Then the screen is popped
    And the Runner Menu screen is shown
