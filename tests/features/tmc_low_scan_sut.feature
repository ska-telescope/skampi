@XTP-17103
Scenario: execute a scan for the elapsed scan duration
    Given the subarray <subarray_id> obsState is READY
    When the user issues the scan command with a <scan_id> to the subarray <subarray_id>
    Then the subarray <subarray_id> obsState transitions to SCANNING
    And the subarray <subarray_id> obsState transitions to READY after the scan duration elapsed
    Examples: 
        | subarray_id   |  scan_id |
        |        1      |    123   |