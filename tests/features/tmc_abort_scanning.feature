@XTP-16348
Scenario: Abort scanning
    Given an subarray busy scanning
    When I command it to Abort
    Then the Tmc subarray should go into an aborted state
