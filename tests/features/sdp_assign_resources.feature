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