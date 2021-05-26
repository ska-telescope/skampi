Feature: 

	#This test case verifies the behaviour of a subarray low when ObsReset command is invoked.
	@XTP-1567
	Scenario Outline: BDD test case for ObsReset command in MVP Low
		Given operator has a running telescope with a subarray in state <subarray_obsstate> and Subarray has transitioned into obsState ABORTED
		When the operator invokes ObsReset command
		Then the subarray should transition to obsState IDLE

		Examples:
		| subarray_obsstate  | 
		| IDLE               |
		| READY              |
		| SCANNING           |
		 