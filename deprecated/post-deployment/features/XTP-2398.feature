Feature: Default

	#This test case verifies that when an observation is going on and the Restart command is invoked on the subarray, the subarray is Restarted.
	@XTP-2398
	Scenario Outline: BDD Test case for subarray Restart functionality
		Given operator has a running telescope with a subarray in state <subarray_obsstate> and Subarray has transitioned into obsState ABORTED
		When the operator invokes Restart command
		Then the subarray changes its obsState to EMPTY
		
		Examples:
		| subarray_obsstate  | 
		| IDLE               | 
		| READY              | 
		| SCANNING           |