@XTP-4782
Feature: Run a scan on sdp subarray

	
	@XTP-4774 @XTP-4773 @XTP-4679 @XTP-4676 @XTP-3324
	Scenario: Run a scan on sdp subarray in mid
		Given an SDP subarray in READY state
		When I command it to scan for a given period
		Then the SDP subarray must be in the SCANNING state until finished	

	
	@XTP-4775 @XTP-4773 @XTP-4680 @XTP-4676 @XTP-3325
	Scenario: Run a scan on sdp subarray in low
		Given an SDP subarray in READY state
		When I command it to scan for a given period
		Then the SDP subarray must be in the SCANNING state until finished

	@XTP-16344
    Scenario: Abort scanning
        Given an subarray busy scanning
        When I command it to Abort
        Then the subarray should go into an aborted state