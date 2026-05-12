Feature: Keyboard Shortcuts
  As a user
  I want keyboard shortcuts to work consistently
  So that I can navigate the app efficiently

  Scenario: Escape returns to previous screen
    Given any screen with a "Back" button (or similar close action)
    When I press Escape
    Then the same action is triggered as pressing the "Back"/"Close"/"Cancel" button
    # Exception: the "Exit" button on Main Menu is NOT triggered by Escape

  Scenario: Arrow keys navigate between buttons
    Given a MenuScreen with multiple buttons
    When I press "up" arrow key
    Then focus moves to the previous Button widget
    When I press "down" arrow key
    Then focus moves to the next Button widget
