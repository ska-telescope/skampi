Feature: Verification of OET scripts being executed successfully during an observation for configure command on subarray node

    Scenario: Configure scan with a SBI on OET subarray in mid
        Given an OET
        When I tell the OET to scan SBI using script file:///scripts/observe_sb.py --subarray_id=1 and SB /tmp/oda/mid_sb_example.json
        Then the sub-array goes to ObsState READY   