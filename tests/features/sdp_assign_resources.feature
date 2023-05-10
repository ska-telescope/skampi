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