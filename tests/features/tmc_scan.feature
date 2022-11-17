@XTP-13150
Scenario: Run a scan from TMC
    Given an TMC
    Given a subarray in READY state
    When I command it to scan for a given period
    Then the subarray must be in the SCANNING state until finished


    