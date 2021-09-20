Feature:

	#This test case verifies that when an observation is going on and Abort command is invoked on the subarray, the ongoing activity is aborted.
	@XTP-1104
	Scenario Outline: when the telescope subarrays can be aborted then abort brings them in ABORTED
		Given operator has a running telescope with a subarray in state <subarray_obsstate>
		When operator issues the ABORT command
		Then the subarray eventually goes into ABORTED

		Examples:
			| subarray_obsstate |
			| IDLE        |
			| CONFIGURING |
			| READY       |
			| SCANNING    |
			| RESETTING   |


