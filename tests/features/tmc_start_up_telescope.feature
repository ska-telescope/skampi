@XTP-6190
Feature: Start up the telescope using TMC

	
	@XTP-6187 @XTP-6186 @XTP-3324
	Scenario: Start up the telescope (SDP only)
		Given an TMC
		Given an partial Telescope consisting of SDP only
		When I start up the telescope
		Then the sdp must be on

	@XTP-6426 @XTP-6186 @XTP-3324
	Scenario: Switch of the telescope (SDP only)
		Given an TMC
		Given an partial Telescope consisting of SDP only that is ON
		When I switch off the telescope
		Then the sdp must be off