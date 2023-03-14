Feature: Visibility Receive Script

	# TODO: Jira ticket ID? which to use?
	Scenario: Execute visibility receive script for a single scan
		Given the test volumes are present and the test data are downloaded
		And an SDP subarray in READY state
		When SDP is commanded to capture data from a scan
		Then the data received matches with the data sent