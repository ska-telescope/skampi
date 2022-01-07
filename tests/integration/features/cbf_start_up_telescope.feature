Feature: Start up the cbf

  Scenario: Start up the cbf in low
    Given an CBF
    When I start up the telescope
    Then the cbf must be on

  Scenario: Start up the cbf in mid
    Given an CBF
    When I start up the telescope
    Then the cbf must be on