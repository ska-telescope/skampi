    @XTP-966
    Scenario: Scheduling Block Resource allocation
        Given the subarray ska_mid/tm_subarray_node/1 and the expected states EMPTY, RESOURCING, IDLE, CONFIGURING, SCANNING, CONFIGURING, SCANNING, CONFIGURING, SCANNING, CONFIGURING, SCANNING, IDLE
        When the OET allocates resources with the script file://scripts/allocate_from_file_sb.py for the SB scripts/data/example_sb.json
        Then the OET observes the SB scripts/data/example_sb.json with the script file://scripts/observe_sb.py
        Then the task runs to completion
        Then the SubArrayNode ObsState passed through the expected states
