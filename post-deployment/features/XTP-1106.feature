Feature: 

	#This test case verifies that when an observation is going on and Restart command is invoked on the subarray, the ongoing activity is Restarted.
	@XTP-1106
	Scenario Outline: BDD test case for Restart functionality
		Given A running telescope for executing observations on a subarray
		And resources are successfully assigned
		And the subarray is in ABORTED obsState
		When I invoke Restart command
		Then subarray changes its obsState to EMPTY