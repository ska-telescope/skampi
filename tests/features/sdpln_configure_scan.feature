Feature: Configure scan on sdp subarray


	Scenario: Configure scan on sdp subarray in mid using the leaf node
		Given an SDP subarray in IDLE state
		When I configure it for a scan
		Then the subarray must be in the READY state
