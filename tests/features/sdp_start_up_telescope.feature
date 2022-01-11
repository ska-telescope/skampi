@XTP-3961
Feature: Start up the sdp

	
	@XTP-3959 @XTP-3960 @XTP-3325
	Scenario: Start up the sdp in low
		Given an SDP
		When I start up the telescope
		Then the sdp must be on	

	
	@XTP-3958 @XTP-3960 @XTP-3324
	Scenario: Start up the sdp in mid
		Given an SDP
		When I start up the telescope
		Then the sdp must be on