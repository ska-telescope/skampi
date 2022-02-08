Feature: Configure scan on CBF subarray

  Scenario: Configure scan on CBF mid subarray
    Given an CBF subarray in IDLE state
    When I configure it for a scan
    Then the CBF subarray must be in the READY state

  Scenario: Configure scan on CBF low subarray
    Given an CBF subarray in IDLE state
    When I configure it for a scan
    Then the CBF subarray must be in the READY state