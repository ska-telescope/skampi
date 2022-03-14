@XTP-3965
Feature: Start up the csp

	
	@XTP-3962 @XTP-3963 @XTP-3325
	Scenario: Start up the csp in low
		Given an CSP
		When I start up the telescope
		Then the csp must be on	

	
	@XTP-3964 @XTP-3963 @XTP-3324
	Scenario: Start up the csp in mid
		Given an CSP
		When I start up the telescope
		Then the csp must be on