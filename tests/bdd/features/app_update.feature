Feature: App Update
  As a user
  I want to manually update the app from Settings
  So that I can stay on the latest version with compatible runners

  Scenario: Settings screen shows Update App button
    Given the Settings screen is shown
    Then it has an Update App button

  Scenario: Clicking Update App opens version selection screen
    Given the Settings screen is shown
    When I press "Update App" button
    Then the App Version screen is shown

  Scenario: App version screen loads and displays versions
    Given the App Version screen is shown
    Then all tags are shown as version buttons

  Scenario: Selecting a compatible version shows confirmation
    Given the App Version screen is shown
    And all installed runners are compatible with the selected version
    When I select a version
    Then a loading screen "Checking runner compatibility" is shown
    And a confirmation dialog is shown with "Are you sure you want to update"

  Scenario: Confirming update triggers app update
    Given the App Version screen is shown
    And all installed runners are compatible with the selected version
    When I select a version
    And I press "Yes" button
    Then a loading screen "Updating app" is shown
    And an info screen showing app update success is shown

  Scenario: Incompatible runner blocks update with warning
    Given the App Version screen is shown
    And an installed runner is incompatible with the selected version
    When I select a version
    Then a loading screen "Checking runner compatibility" is shown
    And a warning InfoScreen is shown
    And it mentions the incompatible runner

  Scenario: Dismissing incompatible runner warning returns to version selection
    Given the App Version screen is shown
    And an installed runner is incompatible with the selected version
    When I select a version
    And I dismiss the warning
    Then the App Version screen is shown

  Scenario: Cancel update goes back to version selection
    Given the App Version screen is shown
    And all installed runners are compatible with the selected version
    When I select a version
    And I press "No" button
    Then the App Version screen is shown
