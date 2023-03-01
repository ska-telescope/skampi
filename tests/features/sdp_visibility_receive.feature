Feature: Visibility Receive Script

	Scenario: Execute visibility receive script for a single scan (full)
		Given an SDP subarray
		And the volumes are created and the data is copied
		And I deploy the visibility receive script
		And the SDP subarray is configured
		When SDP is commanded to capture data from a scan
		Then the data received matches with the data sent

	Scenario: Execute visibility receive script for a single scan
		# subarray already had AssignResources and Configure run on them
		Given the volumes are created and the data is copied
		And an SDP subarray in READY state
		When SDP is commanded to capture data from a scan
		Then the data received matches with the data sent