Feature: App Startup
  As a user
  I want the app to start correctly
  So that I can manage runners and tasks

  Scenario: App starts and creates directories
    Given the app is launched for the first time
    Then the main menu screen is shown
    And it contains "Show Runners" button
    And it contains "Settings" button
    And it contains "Exit" button
    And the title is "Main Menu"
    And the work directory `.termux-tasker` is created
    And the runners directory `.termux-tasker/runners` is created
    And the tmp directory `.termux-tasker/.tmp` is created
    And the default app config is created at `.termux-tasker/app.toml`
