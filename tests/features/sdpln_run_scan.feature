
Feature: Configure a scan using sdp leaf node

	@XTP-13148
	Scenario: Run scan on sdp subarray in mid using the leaf node
		Given a TMC SDP subarray Leaf Node
		Given an SDP subarray in READY state
		When I command it to scan for a given period
		Then the SDP subarray shall go from READY to SCANNING
		Then the SDP shall go back to READY when finished
