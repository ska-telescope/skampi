@XTP-20968
Feature: Visibility Receive Script

	@XTP-20969
	Scenario: Execute visibility receive script for a single scan
		Given the test volumes are present and the test data are downloaded
		And an SDP subarray in READY state
		When SDP is commanded to capture data from a scan
		Then the data received matches with the data sent
		And a list of data products can be retrieved
		And an available data product can be downloaded