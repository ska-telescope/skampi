    @XTP-966
    Scenario: Scheduling Block Resource allocation
        Given the subarray ska_mid/tm_subarray_node/1 and the expected states EMPTY, RESOURCING, IDLE, CONFIGURING, SCANNING, CONFIGURING, SCANNING, CONFIGURING, SCANNING, CONFIGURING, SCANNING, READY
        When the OET runs the script file://scripts/observe_sb.py passing the SB scripts/data/example_sb.json as an argument
        Then the task runs to completion
        Then and the SubArrayNode ObsState passed through the expected states
