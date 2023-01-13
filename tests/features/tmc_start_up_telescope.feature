@XTP-6190
Feature: Start up the telescope using TMC

	
	@XTP-6187 @XTP-6186 @XTP-3324
	Scenario: Start up the telescope
		Given an TMC
		Given a Telescope consisting of SDP, CSP and a Dish
		When I start up the telescope
		Then the sdp, csp and dish must be on

	@XTP-6426 @XTP-6186 @XTP-3324
	Scenario: Switch of the telescope
		Given an TMC
		Given a Telescope consisting of SDP, CSP and a Dish that is ON
		When I switch off the telescope
		Then the sdp, csp and dish must be off


	Scenario: Start up the telescope in low 
		Given an TMCLow
		Given a Telescope consisting of SDP and CSP
		When I start up the telescope
		Then the sdp and csp must be on
