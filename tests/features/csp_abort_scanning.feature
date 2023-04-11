@XTP-20128
Scenario:Abort scanning on CSP Low
    Given an subarray busy scanning
    When I command it to Abort
    Then the subarray should go into an aborted state