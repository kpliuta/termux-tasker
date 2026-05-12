Feature: Runner Installation
  As a user
  I want to install runners from various sources
  So that I can add new runners to manage tasks

  Scenario: Install runner from bundled list
    Given the Runner Type screen is shown
    When I press "Bundled" button
    Then the Bundled Runner screen is shown
    And bundled runners are fetched from `bundled_runners.toml`
    And each runner repo is cloned to a temporary directory
    And each runner shows its name with "[Installed]" suffix if already installed
    And installable runners show a clickable button

  Scenario: Install runner from GitHub URL
    Given the Runner Type screen is shown
    When I press "GitHub URL" button
    Then an InputScreen is shown for URL entry
    When I enter a valid GitHub URL and press Ok
    Then the repository is cloned to a temporary directory
    And metadata is validated (existence + essentials)
    Then the Install Runner screen is shown with the cloned folder

  Scenario: Install runner from local storage
    Given the Runner Type screen is shown
    When I press "Local Storage" button
    Then a FileBrowserScreen is shown in folder selection mode
    When I select a folder and press "Select"
    Then the folder is copied to a temporary directory
    And metadata is validated (existence + essentials)
    Then the Install Runner screen is shown

  Scenario: Install runner with version selection (git source)
    Given the Install Runner screen is shown for a git-based runner
    When I press "Install" button
    Then the Install Runner Version screen is shown
    And a loading screen "Fetching <name> versions" is shown
    Then the main branch and all tags are shown as version buttons
    And already-installed versions show "[Installed]" suffix
    When I select a version
    Then a confirmation dialog is shown asking to install/update/reinstall that version

  Scenario: Install runner with version selection (local source)
    Given the Install Runner screen is shown for a local runner
    When I press "Install" button
    Then the Install Runner Version screen is shown
    And a single version button is shown for the local version
    And "[Installed]" suffix shown if already installed

  Scenario: Install runner - validate full runner before install
    Given I selected a runner version to install
    When I confirm the installation
    Then the full RunnerValidator runs validation
    And validation passes, the install proceeds
    And validation fails, an error InfoScreen is shown

  Scenario: Install runner - set required properties during install
    Given I am installing a runner with non-optional properties without defaults
    When the install finalizes
    And properties are prompted one by one via InputScreen
    When I provide valid values for all properties
    Then the runner is installed to `runners_dir/<id>`
    And the install screens are popped
    And the Runner Menu screen is shown for the newly installed runner

  Scenario: Install runner - skip optional properties during install
    Given I am installing a runner where all properties have defaults or are optional
    When the install finalizes
    Then default properties are filled
    And the runner is installed to `runners_dir/<id>`
    And no property prompts are shown
    And the Runner Menu screen is shown for the newly installed runner

  Scenario: Git checkout failure during runner install
    Given I selected a git tag to install
    When the git checkout fails
    Then an error InfoScreen is shown with "Failed to checkout tag '<tag>'"
    And the install is aborted

  Scenario: Cancel runner version selection
    Given the Install Runner Version screen is shown
    When I press "Back" button (or Escape)
    Then I am returned to the previous screen
    And no installation occurs
