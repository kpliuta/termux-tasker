Feature: Home button
  As a user
  I want a home button on every screen
  So that I can jump back to the dashboard from anywhere

  Scenario: Home button returns to dashboard from Runner Menu
    Given the Runner Menu screen is shown
    When I press the "🏠" home button
    Then the dashboard screen is shown again

  Scenario: Home button returns to dashboard from deep in the stack
    Given the Task Menu screen is shown
    When I press the "🏠" home button
    Then the dashboard screen is shown again

  Scenario: Home button is shown on the Properties screen
    Given the Properties screen is shown from the runner menu
    Then it contains "🏠" button
