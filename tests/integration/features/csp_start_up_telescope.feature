Feature: Start up the csp

  Scenario: Start up the csp in low
    Given an CSP
    When I start up the telescope
    Then the csp must be on

  Scenario: Start up the csp in mid
    Given an CSP
    When I start up the telescope
    Then the csp must be on