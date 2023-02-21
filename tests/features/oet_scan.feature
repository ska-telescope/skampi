Scenario: Run a scan on low subarray from OET
    Given an OET
    Given a subarray in READY state
    When I command it to scan for a given period
    Then the subarray must be in the SCANNING state until finished