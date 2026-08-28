Feature: Properties Screen
  As a user
  I want to edit runner and task properties in one dedicated screen
  So that values are easy to see and change

  Scenario: Open properties screen from runner menu
    Given the Runner Menu screen is shown for a runner
    When I press "Properties" button
    Then the Properties screen is shown
    And the title is "Properties"
    And the subtitle is the runner's name
    And for each property defined in metadata it contains "Set <property>" button
    And each property button shows "<property>: <value>" as its title
    And it contains "Back" button

  Scenario: Runner menu has no inline property controls
    Given the Runner Menu screen is shown for a runner
    Then it contains no "Set <property>" buttons
    And the description shows no properties

  Scenario: Back returns to the runner menu
    Given the Properties screen is shown from the runner menu
    When I press "Back" button (or Escape)
    Then the Runner Menu screen is shown again

  Scenario: Set a runner property
    Given the Properties screen is shown from the runner menu
    And the runner metadata defines a property
    When I press "Set <property>" button
    Then an InputScreen is shown for that property
    And the correct input type (text/radio/checkbox)
    And the current value is pre-populated
    And the property description is shown
    When I enter a valid value and press Ok
    Then the property value is saved in settings.toml
    And the property button title shows the saved value

  Scenario: Required runner property with empty value shows warning
    Given the Properties screen is shown from the runner menu
    And the property is non-optional
    When I press "Set <property>" button
    And I clear the value and press Ok
    Then a warning InfoScreen is shown
    And it says "'<property>' is required and must have a value."
    When I dismiss the warning
    Then the InputScreen is shown again to retry

  Scenario: Cancel setting a runner property
    Given the Properties screen is shown from the runner menu
    When I press "Set <property>" button
    And I press "Cancel" (or Escape)
    Then the property value is unchanged

  Scenario: Open properties screen from task menu
    Given the Task Menu screen is shown for a task
    When I press "Properties" button
    Then the Properties screen is shown
    And the title is "Properties"
    And the subtitle is the task's name
    And for each property defined in metadata it contains "Set <property>" button
    And it contains "Back" button

  Scenario: Task menu has no inline property controls
    Given the Task Menu screen is shown for a task
    Then it contains no "Set <property>" buttons
    And the description shows no properties

  Scenario: Back returns to the task menu
    Given the Properties screen is shown from the task menu
    When I press "Back" button (or Escape)
    Then the Task Menu screen is shown again

  Scenario: Set a task property
    Given the Properties screen is shown from the task menu
    When I press "Set <property>" button
    Then an InputScreen is shown for that property
    When I enter a valid value and press Ok
    Then the task property value is saved in settings.toml
    And the property button title shows the saved value
