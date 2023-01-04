
Feature: Configure a scan using sdp leaf node

	@XTP-13147
	Scenario: Configure scan on sdp subarray in mid using the leaf node
		Given an SDP subarray in the IDLE state
		And a TMC SDP subarray Leaf Node
		When I configure it for a scan
		Then the subarray must be in the READY state
