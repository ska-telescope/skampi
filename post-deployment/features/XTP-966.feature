    @XTP-966
    Scenario: Scheduling Block Resource Allocation and Observation
        Given the subarray ska_mid/tm_subarray_node/1 and the SB scripts/data/example_sb.json
        When the OET allocates resources for the SB with the script file://scripts/allocate_from_file_sb.py 
        Then the OET observes the SB with the script file://scripts/observe_sb.py
        Then the SubArrayNode obsState passes in order through the following states EMPTY, RESOURCING, IDLE, CONFIGURING, SCANNING, CONFIGURING, SCANNING, CONFIGURING, SCANNING, CONFIGURING, SCANNING, IDLE
