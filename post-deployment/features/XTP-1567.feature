Feature: 

	#This test case verifies the behaviour of a subarray low when ObsReset command is invoked.
	@XTP-1567
	Scenario Outline: BDD test case for ObsReset command in MVP Low
		Given Subarray has transitioned into obsState ABORTED during an observation
		When the operator invokes ObsReset command
		Then the subarray should transition to obsState IDLE