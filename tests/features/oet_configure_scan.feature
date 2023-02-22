@VTS-225
Feature: Verification of OET scripts being executed successfully during an observation

    #Scenario: Observing a SBI
	@XTP-778 @XTP-776
	Scenario: Observing a Scheduling Block
		Given an OET
		And sub-array is in the ObsState IDLE
		When I tell the OET to observe using script file:///scripts/observe_mid_sb.py and SBI /tmp/oda/mid_sb_example.json
		Then the OET will execute the script correctly
		And the sub-array goes to ObsState IDLE


	#Scenario: Configure the low telescope subarray using OET
	@XTP-19864 @XTP-18866
	Scenario: Configure the low telescope subarray using OET
			Given an OET
			Given a valid scan configuration
			When I configure it for a scan
			Then the subarray must be in the READY state

