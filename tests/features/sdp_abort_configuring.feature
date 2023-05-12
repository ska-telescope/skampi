@XTP-20122
Scenario: Abort configuring SDP Low
    Given an subarray busy configuring
    When I command it to Abort
    Then the subarray should go into an aborted state