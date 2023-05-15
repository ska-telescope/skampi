@XTP-16348
Scenario: Abort scanning
    Given an subarray busy scanning
    When I command it to Abort
    Then the subarray should go into an aborted state

@XTP-20112
Scenario: Abort scanning Low
    Given an subarray busy scanning
    When I command it to Abort
    Then the subarray should go into an aborted state
