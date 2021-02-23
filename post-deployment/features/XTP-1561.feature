Feature: Default

	#An mvp test in skampi pipeline that sets up at least one scan and checks for uniqueness of IDs.
	@XTP-1583 @XTP-1561 @PI9
	Scenario: TMC coordinates observational scan and SDP uses the scan ID as provided by the skuid service
		Given a running telescope
		And the SKUID_URL environment variable has been set
		And a scan ID has been retrieved prior to the scan
		And Subarray is configured successfully
		When I call the execution of the scan command for duration of 6 seconds
		Then the scanID used by SDP has a value equal to the last ID that was retrieved prior to the scan plus one