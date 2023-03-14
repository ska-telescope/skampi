Feature: Visibility Receive Script

	Scenario: Execute visibility receive script for a single scan (full)
		Given an SDP subarray
		And the test volumes are present and the test data are downloaded
		And I deploy the visibility receive script
		And the SDP subarray is configured
		When SDP is commanded to capture data from a scan
		Then the data received matches with the data sent

	Scenario: Execute visibility receive script for a single scan
		Given the test volumes are present and the test data are downloaded
		And an SDP subarray in READY state
		When SDP is commanded to capture data from a scan
		Then the data received matches with the data sent