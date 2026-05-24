Feature: Log Screen
  As a user
  I want to view and follow log files
  So that I can monitor runner output

  Scenario: View a log file
    Given a LogScreen is opened with a file path
    Then the file content is displayed in the RichLog widget

  Scenario: Close the LogScreen
    Given a LogScreen is opened with a file path
    When I press "Close" button (or Escape)
    Then the LogScreen is dismissed

  Scenario: Display raw file content (no markup parsing)
    Given a LogScreen is opened with a TOML file containing `[section]` headers
    Then the square brackets are displayed literally
    And not interpreted as Textual markup

  Scenario: Follow mode appends new content
    Given a LogScreen is opened with follow mode enabled
    And there is existing content in the file
    When new content is appended to the file
    Then the new content appears in the RichLog within 1 second
    And previously displayed content is not duplicated

  Scenario: Reset clears the log display
    Given a LogScreen is opened with follow mode enabled
    And content is displayed
    When I press "Reset" button
    Then the RichLog display is cleared
    And the file read position is moved to the end of the file
    When new content is written to the file
    Then only the new content appears (old content is not re-displayed)

  Scenario: Toggle follow on/off
    Given a LogScreen is opened with follow mode enabled
    When I uncheck the "Follow" checkbox
    Then the follow timer is stopped
    When I check the "Follow" checkbox again
    Then the follow timer is started (1 second interval)
