Feature: Idempotency and Edge Cases

  Scenario: Reinstall a runner (update)
    Given a runner is already installed
    When I install the same runner again with a different version
    Then old settings are merged with new property definitions
    And properties that no longer exist in the new version are preserved
    And properties that still exist retain their values

  Scenario: Reinstall a runner (same version)
    Given a runner is already installed
    When I install the same runner with the same version
    Then it's treated as a "reinstall"
    And old settings are merged with new property definitions

  Scenario: Runner state persistence across app restarts
    Given a runner was disabled before the app exited
    When the app is restarted
    Then the runner's `settings.general.enabled` is still False
    And it is not started automatically
