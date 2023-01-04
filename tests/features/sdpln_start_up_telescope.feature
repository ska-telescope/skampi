
Feature: Start up the sdp using sdp leaf node

	@XTP-16744
	Scenario: Start up the sdp in low using the leaf node
		Given an SDP
		And an SDP leaf node
		When I start up the telescope
		Then the sdp must be on

	@XTP-14547
	Scenario: Start up the sdp in mid using the leaf node
		Given an SDP
		And an SDP leaf node
		When I start up the telescope
		Then the sdp must be on
