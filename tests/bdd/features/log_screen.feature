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

  Scenario: Dynamic mode appends new content via Auto-scroll
    Given a LogScreen is opened in dynamic mode
    And there is existing content in the file
    When I enable Auto-scroll in Settings
    And new content is appended to the file
    Then the new content appears in the RichLog within 1 second
    And previously displayed content is not duplicated

  Scenario: Clear Screen clears the log display
    Given a LogScreen is opened in dynamic mode
    And content is displayed
    When I click "Clear Screen" in Settings
    Then the RichLog display is cleared
    And the file read position is moved to the end of the file

  Scenario: Toggle Auto-scroll on/off
    Given a LogScreen is opened in dynamic mode
    When I enable Auto-scroll in Settings
    Then the follow timer is started (1 second interval)
    When I disable Auto-scroll in Settings
    Then the follow timer is stopped

  Scenario: Toggle Word Wrap on/off
    Given a LogScreen is opened with a file path
    When I check "Word Wrap" in Settings
    Then the soft wrap is enabled
    When I uncheck "Word Wrap" in Settings
    Then the soft wrap is disabled

  Scenario: Settings open and close
    Given a LogScreen is opened with a file path
    When I press "Settings" button
    Then a LogSettingsScreen is shown
    When I press "Close" button in Settings
    Then the LogSettingsScreen is dismissed

  Scenario: Help screen shows descriptions
    Given a LogScreen is opened in dynamic mode
    When I open Help from Settings
    Then a LogHelpScreen is shown with setting descriptions

  Scenario: Static mode shows only Word Wrap in Settings
    Given a LogScreen is opened with a file path
    When I press "Settings" button
    Then only "Word Wrap" setting is visible
    And there is no Help button in Settings

  Scenario: Clear Log File shows confirmation before deleting
    Given a LogScreen is opened in dynamic mode
    And there is existing content in the file
    When I click "Clear Log File" in Settings
    Then a ConfirmClearScreen is shown
    When I cancel the clear confirmation
    Then the log file content is preserved
    And the RichLog display still shows previous content

  Scenario: Clear Log File deletes after confirmation
    Given a LogScreen is opened in dynamic mode
    And there is existing content in the file
    When I click "Clear Log File" in Settings
    Then a ConfirmClearScreen is shown
    When I confirm the clear
    Then the log file is truncated
