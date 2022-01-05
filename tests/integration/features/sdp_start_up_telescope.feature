Feature: Start up the sdp

  Scenario: Start up the sdp in mid
    Given an SDP
    When I start up the telescope
    Then the sdp must be on

  Scenario: Start up the sdp in low
    Given an SDP
    When I start up the telescope
    Then the sdp must be on