
Feature: Configure a scan using sdp leaf node

	@XTP-14547
	Scenario: Configure scan on sdp subarray in mid using the leaf node
		Given an SDP
		Given an SDP subarray leaf node
		When I configure it for a scan
		Then the subarray must be in the READY state