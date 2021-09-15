Feature: 

	#This test case verifies that when an observation is going on and Restart command is invoked on the subarray, the ongoing activity is Restarted.
	@XTP-1106
	Scenario Outline: BDD test case for Restart functionality
		Given operator has a running telescope with a subarray in state <subarray_obsstate> and Subarray has transitioned into obsState ABORTED
		When I invoke Restart command
		Then subarray changes its obsState to EMPTY

		Examples:
		| subarray_obsstate  | 
		| IDLE               | 
		| READY              | 
		| SCANNING           | 
