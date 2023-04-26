@XTP-4511
Feature: Assign resources to sdp subarray


	@XTP-4506 @XTP-4503 @XTP-3324
	Scenario: Assign resources to sdp subarray in mid
		Given an SDP subarray
		When I assign resources to it
		Then the subarray must be in IDLE state


	@XTP-4508 @XTP-4503 @XTP-3325
	Scenario: Assign resources to sdp subarray in low
		Given an SDP subarray
		When I assign resources to it
		Then the subarray must be in IDLE state

	@XTP-14873 @XTP-4503 @XTP-3324
	Scenario: Releasing all resources from sdp sub-array in mid
		Given an SDP subarray in IDLE state
		When I release all resources assigned to it
		Then the subarray must be in EMPTY state

	@XTP-16111
	Scenario: Assign resources with duplicate id to SDP
		Given an SDP subarray
		When I assign resources with a duplicate sb id
		Then the subarray should throw an exception and remain in the previous state

	@XTP-16235
	Scenario: Command assign resources twice in order
		Given an SDP subarray
		When I command the assign resources twice in consecutive fashion
		Then the subarray should throw an exception and continue with first command
		Then the subarray must be in IDLE state

	@XTP-20494
	Scenario: Assign resources with invalid processing block script name to SDP
		Given an SDP subarray
		When I assign resources with an invalid processing block script name
		Then the subarray should throw an exception and remain in the previous state

	@XTP-20083
	Scenario: Abort assigning SDP
		Given an subarray busy assigning
		When I command it to Abort
		Then the subarray should go into an aborted state

	@XTP-20123
	Scenario: Abort assigning SDP Low
		Given an subarray busy assigning
		When I command it to Abort
		Then the subarray should go into an aborted state
