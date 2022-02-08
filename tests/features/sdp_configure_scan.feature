@XTP-4595
Feature: Configure scan on sdp subarray

	
	@XTP-4593 @XTP-4592
	Scenario: Configure scan on sdp subarray in mid
		Given an SDP subarray in IDLE state
		When I configure it for a scan
		Then the subarray must be in the READY state	

	
	@XTP-4594 @XTP-4592
	Scenario: Configure scan on sdp subarray in low
		Given an SDP subarray in IDLE state
		When I configure it for a scan
		Then the subarray must be in the READY state