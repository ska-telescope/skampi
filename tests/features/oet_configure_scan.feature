Feature: Verification of configure a scan using a predefined config on subarray node
 
  Scenario: Configure a scan using a predefined config
    Given an TMC
		Given a subarray in the IDLE state
    When I tell the OET to config SBI using script file:///scripts/observe_sb.py and SB /tmp/oda/mid_sb_example.json
    Then the sub-array goes to ObsState CONFIGURING,READY