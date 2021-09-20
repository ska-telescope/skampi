Feature: 

	#This test case verifies that when an observation is going on and Abort command is invoked on the subarray low, the ongoing activity is aborted.
	@XTP-1566
	Scenario Outline: when the telescope subarrays can be aborted then Abort brings them in ABORTED observation state in MVP Low
		Given operator has a running low telescope with a subarray in obsState <subarray_obsstate>
		When operator issues the ABORT command
		Then the subarray eventually transitions into obsState ABORTED
		
		Examples:
		| subarray_obsstate  |
		| IDLE               |
		| READY              |
		| SCANNING           |
		