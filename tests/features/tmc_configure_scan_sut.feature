@XTP-17877
Scenario: Configure for a scan on a subarray - happy flow
    Given the Telescope is in ON state
    And the subarray <subarray_id> obsState is IDLE
    When I issue the configure command with <scan_type> and <scan_configuration> to the subarray <subarray_id>
    Then the subarray <subarray_id> obsState is READY
    Examples: 
        | subarray_id   |  scan_configuration   |    scan_type      |
        | 1             |         tba           |       "science_A" |
