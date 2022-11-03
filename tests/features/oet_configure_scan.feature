Feature: Verification of configure a scan using a predefined config on subarray node
 
  Scenario: Configure a scan using a predefined config
    Given A running telescope for executing observations on a subarray
    When I tell the OET to config SBI using script file:///scripts/observe_sb.py --subarray_id=1 and SB /tmp/oda/mid_sb_example.json
    Then the sub-array goes to ObsState READY
|