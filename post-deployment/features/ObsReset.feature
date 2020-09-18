Scenario: obsreset-test, Sub-array Invokes RESTART command
        Given A running telescope for executing observations on a subarray
        When I call ObsReset on Subarray
        Then Sub-array changes to IDLE state
