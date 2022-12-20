@VTS-225
Feature: Verification of OET scripts being executed successfully during an observation

    #Scenario: Observing a SBI
	@XTP-778 @XTP-776
	Scenario: Observing a Scheduling Block
		Given an OET
		And sub-array is in the ObsState IDLE
		When I tell the OET to observe using script file:///scripts/observe_mid_sb.py and SBI /tmp/oda/mid_sb_example.json
		And the OET will execute the script correctly
		then the sub-array goes to ObsState IDLE

