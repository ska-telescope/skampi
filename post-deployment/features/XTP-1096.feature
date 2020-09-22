Feature: 

	#This test case verifies the behaviour of a subarray when ObsReset command is invoked.
	@XTP-1096
	Scenario Outline: BDD test case for ObsReset command
		Given Subarray has transitioned into obsState ABORTED during an observation
		When the operator invokes ObsReset command
		Then the subarray should transition to obsState IDLE