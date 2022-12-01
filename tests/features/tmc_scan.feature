@XTP-13150
Scenario: Run a scan from TMC
    Given an TMC
    Given a subarray in READY state
    When I command it to scan for a given period
    Then the subarray must be in the SCANNING state until finished

@XTP-16348
Scenario: Abort scanning
    Given an subarray busy scanning
    When I command it to Abort
    Then the subarray should go into an aborted state