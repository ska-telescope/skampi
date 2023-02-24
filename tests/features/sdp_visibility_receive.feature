Feature: Visibility Receive Script

	Scenario: Execute visibility receive script
		Given an SDP subarray
		And obsState is EMPTY
		And the volumes are created and the data is copied
		And I deploy the visibility receive script
		And the SDP subarray is configured
		When SDP is commanded to capture data from a scan
#		Then the data received matches with the data sent
#		And each scan can be identified by its associated metadata