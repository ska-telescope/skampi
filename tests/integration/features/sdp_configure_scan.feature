Feature: Configure scan on sdp subarray

  Scenario: Configure scan on sdp subarray in mid
    Given an SDP subarray in IDLE state
    When I configure it for a scan
    Then the subarray must be in the READY state

  Scenario: Configure scan on sdp subarray in low
    Given an SDP subarray in IDLE state
    When I configure it for a scan
    Then the subarray must be in the READY state