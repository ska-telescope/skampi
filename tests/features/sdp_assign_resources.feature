Feature: Assign resources to sdp subarray

  Scenario: Assign resources to sdp subarray in mid
    Given an SDP subarray
    When I assign resources to it
    Then the subarray must be in IDLE state

  Scenario: Assign resources to sdp subarray in low
    Given an SDP subarray
    When I assign resources to it
    Then the subarray must be in IDLE state