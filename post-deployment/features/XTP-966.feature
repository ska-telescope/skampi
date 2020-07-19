
    @XTP-966
    Scenario: Scheduling Block Resource allocation
        Given the subarray ska_mid/tm_subarray_node/1 and the expected states READY, CONFIGURING, SCANNING
        When the OET runs the script file://scripts/observe.py passing the SB scripts/data/example_configure.json as an argument
        Then the task runs to completion
        Then and the SubArrayNode ObsState passed through the expected states