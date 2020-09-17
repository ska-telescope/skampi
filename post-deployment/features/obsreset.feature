Scenario: obsreset-test, Sub-array Invokes RESTART command
        Given A running telescope for executing observations on a subarray
        Given Sub-array is in READY state
        Given I call abort on subarray1
        When I call ObsReset on Subarray
        Then Sub-array changes to IDLE state
